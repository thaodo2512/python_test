import json
import yaml
from docutils import nodes
from sphinx.util import nested_parse_with_titles
from sphinx.util.docutils import SphinxDirective
from docutils.statemachine import ViewList

class PDRTableDirective(SphinxDirective):
    """
    A Sphinx directive to create a table from JSON and YAML files.
    Usage: .. pdr-table:: :json: <json_path> :yaml: <yaml_path>
    """
    option_spec = {'json': str, 'yaml': str}

    def run(self):
        # Load JSON and YAML files
        json_path = self.options.get('json')
        yaml_path = self.options.get('yaml')
        if not json_path or not yaml_path:
            return [self.error("Both 'json' and 'yaml' options are required.")]

        try:
            with open(json_path, 'r') as f:
                json_data = json.load(f)
            with open(yaml_path, 'r') as f:
                yaml_data = yaml.safe_load(f)
        except Exception as e:
            return [self.error(f"Error loading files: {e}")]

        # Extract field types from YAML (assuming YAML has field definitions)
        field_types = self.extract_field_types(yaml_data)

        # Handle multiple PDR objects
        if isinstance(json_data, list) and len(json_data) > 0:
            selected_pdr = json_data[0]  # Use first object for table structure
            sensor_ids = [int(pdr['body']['sensorID']) for pdr in json_data]
            value_formula = self.get_sensor_id_formula(sensor_ids)
        else:
            selected_pdr = json_data
            value_formula = None

        # Generate table rows
        rows = self.generate_table_rows(selected_pdr, field_types, value_formula)

        # Create and return the table
        return [self.create_table(rows)]

    def extract_field_types(self, yaml_data):
        """Extract field types from YAML data."""
        pdr_type_key = list(yaml_data.keys())[0]
        return yaml_data[pdr_type_key]

    def get_sensor_id_formula(self, sensor_ids):
        """Generate a formula for sensorID values."""
        if not sensor_ids:
            return "Varies across objects"

        # Check for pattern "k * n"
        n_values = list(range(1, len(sensor_ids) + 1))
        k_values = [sid / n for sid, n in zip(sensor_ids, n_values)]
        if all(k == k_values[0] for k in k_values):  # Consistent multiplier
            k = k_values[0]
            return f"{int(k)} * n, n from 1 to {len(sensor_ids)}"
        return "Varies across objects"

    def generate_table_rows(self, pdr_data, field_types, value_formula):
        """Generate table rows from PDR data."""
        rows = []
        for field, value in pdr_data['body'].items():
            field_type = field_types.get(field, "Unknown")
            comment = pdr_data['body'].get(f"{field}_comment", "")
            display_value = value_formula if (value_formula and field == "sensorID") else str(value)
            rows.append([field_type, field, display_value, comment])
        return rows

    def create_table(self, rows):
        """Create a Sphinx table."""
        table = nodes.table()
        tgroup = nodes.tgroup(cols=4)
        table += tgroup

        for _ in range(4):
            tgroup += nodes.colspec(colwidth=1)

        # Table header
        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        headers = ["Type", "PDR field", "PDR field value", "comment"]
        for header in headers:
            entry = nodes.entry()
            header_row += entry
            viewlist = ViewList([header], "<pdr_table>")
            paragraph = nodes.paragraph()
            nested_parse_with_titles(self.state, viewlist, paragraph)
            entry += paragraph
        thead += header_row

        # Table body
        tbody = nodes.tbody()
        tgroup += tbody
        for row_data in rows:
            row = nodes.row()
            for cell in row_data:
                entry = nodes.entry()
                row += entry
                viewlist = ViewList([str(cell)], "<pdr_table>")
                paragraph = nodes.paragraph()
                nested_parse_with_titles(self.state, viewlist, paragraph)
                entry += paragraph
            tbody += row

        return table

    def error(self, message):
        """Generate an error node."""
        return nodes.error(None, nodes.paragraph(text=message))

def setup(app):
    app.add_directive('pdr-table', PDRTableDirective)
    return {'version': '0.1', 'parallel_read_safe': True, 'parallel_write_safe': True}