from sphinx.util.docutils import SphinxDirective
from docutils import nodes
from docutils.statemachine import StringList
import json
import yaml

# Define PDR field types based on pdr_type
PDR_TYPES = {
    2: {
        "record_handle": "uint8",
        "version": "uint8",
        "pdr_type": "uint8",
        "record_change_numer": "uint8",
        "length": "strASCII",
        "terminus_locator": "uint8",
        "validity": "uint8",
        "tid": "uint8",
        "container_id": "uint8",
        "terminus_locator_type": "uint8",
        "terminus_locator_value_size": "uint8",
        "terminus_locator_value": {
            "terminus_instance": "uint8",
            "uuid": "uint8"
        }
    }
}

def flatten_dict(d, parent_key='', sep='.'):
    """Flatten a nested dictionary into (path, value) pairs."""
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            yield from flatten_dict(v, new_key, sep=sep)
        else:
            yield new_key, v

def get_type(type_map, path):
    """Retrieve the type for a field path from the type map."""
    current = type_map
    for key in path:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current if isinstance(current, str) else None

class PdrTableDirective(SphinxDirective):
    """Custom Sphinx directive to generate a PDR table."""
    required_arguments = 3  # json_path, yaml_path, pdr_handle

    def run(self):
        json_path, yaml_path, pdr_handle = self.arguments
        pdr_handle = int(pdr_handle)

        # Load JSON file
        with open(json_path, 'r') as f:
            data = json.load(f)
        records = data.get("terminus_locator", [])
        record = next((r for r in records if r.get("record_handle") == pdr_handle), None)
        if record is None:
            raise ValueError(f"No record found with record_handle {pdr_handle}")

        # Load YAML file
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        comments = config.get("pdr_display", {})

        # Get pdr_type and corresponding type map
        pdr_type = record.get("pdr_type")
        type_map = PDR_TYPES.get(pdr_type, {})

        # Flatten the record into field paths and values
        fields = list(flatten_dict(record))

        # Create table structure
        table = nodes.table()
        tgroup = nodes.tgroup(cols=4)
        table += tgroup

        # Define column specifications
        for _ in range(4):
            tgroup += nodes.colspec(colwidth=1)

        # Table header
        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        for header in ["Type", "PDR Field", "Value", "Comment"]:
            entry = nodes.entry()
            entry += nodes.paragraph(text=header)
            header_row += entry
        thead += header_row

        # Table body
        tbody = nodes.tbody()
        tgroup += tbody

        for path, value in fields:
            row = nodes.row()
            path_list = path.split('.')
            field_name = path_list[-1]

            # Type column
            field_type = get_type(type_map, path_list) or "unknown"
            entry = nodes.entry()
            entry += nodes.paragraph(text=field_type)
            row += entry

            # PDR Field column
            entry = nodes.entry()
            entry += nodes.paragraph(text=path)
            row += entry

            # Value column
            entry = nodes.entry()
            entry += nodes.paragraph(text=str(value))
            row += entry

            # Comment column (parsed as RST for rich text)
            comment_key = f"{field_name}_comment"
            comment_text = comments.get(comment_key, "")
            entry = nodes.entry()
            if comment_text:
                temp_section = nodes.section()
                self.state.nested_parse(StringList([comment_text]), 0, temp_section)
                entry += temp_section.children
            else:
                entry += nodes.paragraph()
            row += entry

            tbody += row

        return [table]

def setup(app):
    """Register the custom directive with Sphinx."""
    app.add_directive('pdr-table', PdrTableDirective)
    return {'version': '0.1', 'parallel_read_safe': True}