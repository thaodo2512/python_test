import yaml
import json
from jsonschema import validate, ValidationError
from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.util.docutils import SphinxDirective

class PldmPdrTableDirective(SphinxDirective):
    required_arguments = 2  # YAML file path, JSON schema file path
    has_content = False

    def run(self):
        yaml_path = self.arguments[0]
        schema_path = self.arguments[1]

        # Load YAML data
        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise self.error(f"Failed to load YAML file '{yaml_path}': {e}")

        # Load JSON schema
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
        except Exception as e:
            raise self.error(f"Failed to load JSON schema '{schema_path}': {e}")

        # Strip comments and unwrap sub-dicts for validation
        def strip_comments(data):
            if isinstance(data, dict):
                if 'value' in data and isinstance(data['value'], (int, float, str, bool, type(None))):
                    return data['value']  # Unwrap scalar values
                return {k: strip_comments(v) for k, v in data.items() if k != 'comment'}
            elif isinstance(data, list):
                return [strip_comments(item) for item in data]
            return data

        plain_data = strip_comments(data)

        # Validate plain_data against schema
        try:
            validate(instance=plain_data, schema=schema)
        except ValidationError as e:
            raise self.error(f"Validation failed for '{yaml_path}' against '{schema_path}': {e}")

        # Check conditionals
        def check_conditionals(sch, dat, parent_key=''):
            for key, key_schema in sch.get('properties', {}).items():
                full_key = f"{parent_key}.{key}" if parent_key else key
                if 'conditional' in key_schema:
                    group = key_schema['conditional'].get('group')
                    bit = key_schema['conditional'].get('bit')
                    if group is None or bit is None:
                        continue
                    dep_value = self.get_nested_value(dat, group)  # Assuming group is at root; adjust if nested
                    if dep_value is None:
                        raise self.error(f"Missing dependency '{group}' for conditional field '{full_key}'")
                    expected_present = (dep_value & (1 << bit)) != 0
                    actual_present = key in dat
                    if actual_present != expected_present:
                        if actual_present:
                            raise self.error(f"Field '{full_key}' is present but bit {bit} not set in '{group}' ({dep_value})")
                        else:
                            raise self.error(f"Field '{full_key}' is missing but bit {bit} set in '{group}' ({dep_value})")
                # Recurse for nested schemas
                if key_schema.get('type') == 'object' and key in dat:
                    check_conditionals(key_schema, dat[key], full_key)

        check_conditionals(schema, plain_data)

        # Helper to get nested value by dot-notation path
        def get_nested_value(d, path):
            parts = path.split('.')
            val = d
            for part in parts:
                if isinstance(val, dict):
                    val = val.get(part)
                else:
                    return None
            return val

        # Flatten the data into table rows
        rows = []

        def flatten(data, parent_key='', schema=schema):
            if isinstance(data, dict):
                for key, value in data.items():
                    full_key = f"{parent_key}.{key}" if parent_key else key
                    # Get subschema for this key
                    key_schema = schema.get('properties', {}).get(key, {})
                    # Get type: handle anyOf/oneOf specially
                    if 'anyOf' in key_schema or 'oneOf' in key_schema:
                        variant_key = 'anyOf' if 'anyOf' in key_schema else 'oneOf'
                        types = [sub.get('description', sub.get('type', 'unknown')) for sub in key_schema[variant_key]]
                        field_type = ' | '.join(types)
                    else:
                        field_type = key_schema.get('type', 'unknown')
                        if isinstance(field_type, list):
                            field_type = '/'.join(field_type)
                    # Resolve type if typeResolver defined
                    if 'typeResolver' in key_schema:
                        resolver = key_schema['typeResolver']
                        dep_path = resolver.get('dependsOn')
                        if dep_path:
                            dep_value = get_nested_value(plain_data, dep_path)
                            if dep_value is not None:
                                str_dep_value = str(dep_value)  # Mapping keys are strings
                                mapped_type = resolver.get('mapping', {}).get(str_dep_value)
                                if mapped_type:
                                    field_type = mapped_type
                    # Resolve format (binaryFormat or formatResolver)
                    if 'formatResolver' in key_schema:
                        resolver = key_schema['formatResolver']
                        dep_path = resolver.get('dependsOn')
                        if dep_path:
                            dep_value = get_nested_value(plain_data, dep_path)
                            if dep_value is not None:
                                str_dep_value = str(dep_value)
                                resolved_format = resolver.get('mapping', {}).get(str_dep_value)
                    else:
                        resolved_format = key_schema.get('binaryFormat', 'unknown')
                    if resolved_format and resolved_format != 'unknown':
                        field_type = f"{field_type} [{resolved_format}]"
                    # Get fallback description
                    fallback_comment = key_schema.get('description', '')
                    # Handle sub-dict structure
                    if isinstance(value, dict) and 'value' in value:
                        comment = value.get('comment', fallback_comment)  # Fallback if missing/empty
                        if comment is None or comment == '':
                            comment = fallback_comment
                        rows.append([field_type, key, str(value['value']), comment])
                    # Handle direct scalar values (no sub-dict)
                    elif not isinstance(value, (dict, list)):
                        rows.append([field_type, key, str(value), fallback_comment])
                    else:
                        # Recurse for nested dicts/lists
                        subschema = key_schema
                        flatten(value, full_key, subschema)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    full_key = f"{parent_key}[{i}]"
                    # Assume array items have a schema under 'items'
                    subschema = schema.get('items', {})
                    flatten(item, full_key, subschema)

        flatten(data)

        if not rows:
            raise self.error("No data found to generate table.")

        # Sort rows if binaryOrder is defined (header fields first, then body in order)
        if 'binaryOrder' in schema:
            order_map = {k: i for i, k in enumerate(schema['binaryOrder'])}
            def sort_key(row):
                field = row[1]  # Field Name
                return order_map.get(field, -1)  # -1 for non-body (e.g., pdrHeader subfields)
            rows.sort(key=sort_key)

        # Generate RST table
        table = nodes.table()
        tgroup = nodes.tgroup(cols=4)
        for _ in range(4):
            tgroup += nodes.colspec(colwidth=1)
        table += tgroup

        # Header row
        thead = nodes.thead()
        row = nodes.row()
        for header in ['Type', 'Field Name', 'Value', 'Comment']:
            entry = nodes.entry()
            entry += nodes.paragraph(text=header)
            row += entry
        thead += row
        tgroup += thead

        # Body rows
        tbody = nodes.tbody()
        for row_data in rows:
            row = nodes.row()
            for i, cell in enumerate(row_data):
                entry = nodes.entry()
                if i == 3:  # Comment column (index 3)
                    # Parse comment as RST (handles long text, links, directives)
                    self.state.nested_parse(cell.splitlines(), 0, entry)
                else:
                    # Other columns as plain text
                    entry += nodes.paragraph(text=cell)
                row += entry
            tbody += row
        tgroup += tbody

        return [table]

def setup(app):
    app.add_directive('pldm-pdr-table', PldmPdrTableDirective)
    return {'version': '0.1', 'parallel_read_safe': True}
