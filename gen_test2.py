import json
import os
from docutils import nodes
from docutils.statemachine import ViewList
from sphinx.util.nodes import nested_parse_with_titles

class PDRField:
    """Represents a field within a PDR, handling both simple fields and nested structs."""
    def __init__(self, field_dict):
        self.name = field_dict['name']
        self.type = field_dict['type']
        self.fields = [PDRField(sub_field) for sub_field in field_dict.get('fields', [])]
        self.comment = field_dict.get('comment', "No comment provided.")
        if 'computed' in field_dict and field_dict['computed']:
            self.value = "Computed"
        elif 'value' in field_dict:
            self.value = field_dict['value']
        elif 'default' in field_dict:
            self.value = field_dict['default']
        else:
            self.value = "N/A"

    def get_leaf_fields(self):
        """Yield all leaf fields, flattening any nested structs."""
        if self.type == "struct":
            for sub_field in self.fields:
                yield from sub_field.get_leaf_fields()
        else:
            yield self

class PDRDefinition:
    """Represents a PDR definition, including its type, description, and fields."""
    def __init__(self, pdr_dict):
        self.pdr_type = pdr_dict['pdr_type']
        self.pdr_type_value = pdr_dict['pdr_type_value']
        self.description = pdr_dict['description']
        self.fields = [PDRField(field) for field in pdr_dict['fields']]

    def to_sphinx_table(self, state, parent):
        """Generate Sphinx table nodes for this PDR definition."""
        # Add title
        title = nodes.title(text=f"{self.pdr_type} PDR (Type {self.pdr_type_value})")
        parent += title
        # Add description
        desc = nodes.paragraph(text=self.description)
        parent += desc
        # Create table
        table = nodes.table()
        tgroup = nodes.tgroup(cols=4)
        table += tgroup
        for _ in range(4):
            tgroup += nodes.colspec(colwidth=1)
        # Table header
        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        for header in ["type", "PDR field", "Value", "comment"]:
            entry = nodes.entry()
            entry += nodes.paragraph(text=header)
            header_row += entry
        thead += header_row
        # Table body
        tbody = nodes.tbody()
        tgroup += tbody
        for field in self.get_all_fields():
            row = nodes.row()
            for text in [field.type, field.name, field.value]:
                entry = nodes.entry()
                entry += nodes.paragraph(text=text)
                row += entry
            # Comment cell with RST parsing
            comment_entry = nodes.entry()
            viewlist = ViewList()
            viewlist.append(field.comment, '<generated>')
            nested_parse_with_titles(state, viewlist, comment_entry)
            row += comment_entry
            tbody += row
        parent += table

    def get_all_fields(self):
        """Get all leaf fields from the PDR, including those in nested structs."""
        for field in self.fields:
            yield from field.get_leaf_fields()

def pdr_directive(name, arguments, options, content, lineno, content_offset, block_text, state, state_machine):
    """Custom directive to generate PDR tables from JSON files."""
    app = state.document.settings.env.app
    json_files = [os.path.join(app.srcdir, arg) for arg in arguments]
    parent = nodes.section()
    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
            for pdr_dict in data:
                pdr = PDRDefinition(pdr_dict)
                pdr.to_sphinx_table(state, parent)
    return parent.children

def setup(app):
    """Register the custom directive with Sphinx."""
    app.add_directive('pldm-pdr-tables', pdr_directive)
    return {"version": "1.0", "parallel_read_safe": True}
