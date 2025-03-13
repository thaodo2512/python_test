import json
from abc import ABC, abstractmethod
from typing import List
from docutils import nodes
from docutils.statemachine import ViewList
from sphinx.application import Sphinx
from sphinx.util.nodes import nested_parse_with_titles

class PDRField:
    """Represents a field within a PDR."""
    def __init__(self, name: str, field_type: str, default: str = None, fields: List[dict] = None, comment: str = None):
        self.name = name
        self.type = field_type
        self.default = default
        self.fields = fields or []
        self.comment = comment or "No comment provided."

    def get_size(self) -> int:
        """Calculate the size of the field in bytes."""
        sizes = {"uint8": 1, "uint16": 2, "uint32": 4, "enum8": 1, "strASCII": len(self.default) if self.default else 0}
        if self.type == "struct":
            return sum(PDRField(**sub_field).get_size() for sub_field in self.fields)
        return sizes.get(self.type, 0)

class PDRDefinition(ABC):
    """Abstract base class for PDR definitions."""
    def __init__(self, pdr_type: str, pdr_type_value: str, description: str, fields: List[dict]):
        self.pdr_type = pdr_type
        self.pdr_type_value = pdr_type_value
        self.description = description
        self.fields = [PDRField(**field) for field in fields]

    @abstractmethod
    def to_sphinx_table(self, state, parent: nodes.Element) -> None:
        """Generate a Sphinx table for this PDR."""
        pass

class StandardPDRDefinition(PDRDefinition):
    """Concrete implementation for standard PDR definitions."""
    def to_sphinx_table(self, state, parent: nodes.Element) -> None:
        """Generate a Sphinx table with type, PDR field, value, and comment columns."""
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
        for header in ["type", "PDR field", "Value", "comment"]:
            entry = nodes.entry()
            header_row += entry
            entry += nodes.paragraph(text=header)
        thead += header_row

        # Table body
        tbody = nodes.tbody()
        tgroup += tbody

        # Populate table rows
        for field in self.fields:
            if field.type == "struct":
                for sub_field in field.fields:
                    self._add_field_row(tbody, state, sub_field)
            else:
                self._add_field_row(tbody, state, field)

        # Add title and description above the table
        title = nodes.title(text=f"{self.pdr_type} PDR (Type {self.pdr_type_value})")
        desc = nodes.paragraph(text=self.description)
        parent += title
        parent += desc
        parent += table

    def _add_field_row(self, tbody: nodes.tbody, state, field: PDRField) -> None:
        """Add a row to the table, handling multi-line comments."""
        default = field.default if field.default and not hasattr(field, 'computed') else "Computed" if hasattr(field, 'computed') else "N/A"
        comment_lines = field.comment.split("\n")

        # First row with all columns
        row = nodes.row()
        for text in [field.type, field.name, default, comment_lines[0]]:
            entry = nodes.entry()
            row += entry
            viewlist = ViewList()
            viewlist.append(text, "<pldm_pdr_sphinx>")
            paragraph = nodes.paragraph()
            nested_parse_with_titles(state, viewlist, paragraph)
            entry += paragraph
        tbody += row

        # Additional rows for multi-line comments
        for extra_line in comment_lines[1:]:
            row = nodes.row()
            for _ in range(3):  # Empty cells for type, field, value
                row += nodes.entry()
            entry = nodes.entry()
            row += entry
            viewlist = ViewList()
            viewlist.append(extra_line, "<pldm_pdr_sphinx>")
            paragraph = nodes.paragraph()
            nested_parse_with_titles(state, viewlist, paragraph)
            entry += paragraph
            tbody += row

class PDRParser:
    """Parses multiple JSON files and generates tables."""
    def __init__(self, json_files: List[str]):
        self.pdr_definitions = []
        for json_file in json_files:
            with open(json_file, 'r') as f:
                data = json.load(f)
                self.pdr_definitions.extend([StandardPDRDefinition(**pdr) for pdr in data['pdr_definitions']])

    def generate_sphinx_tables(self, app: Sphinx, state, parent: nodes.Element):
        """Generate tables for all PDR definitions."""
        for pdr in self.pdr_definitions:
            pdr.to_sphinx_table(state, parent)

def pdr_directive(name: str, arguments: List[str], options: dict, content: List[str],
                  lineno: int, content_offset: int, block_text: str, state, state_machine):
    """Custom directive to generate PDR tables."""
    json_files = arguments  # Arguments are the list of JSON files
    if not json_files:
        raise ValueError("At least one JSON file must be provided as an argument")
    parser = PDRParser(json_files)
    parent = nodes.section()
    parser.generate_sphinx_tables(state.app, state, parent)
    return parent.children

def setup(app: Sphinx):
    """Register the custom directive with Sphinx."""
    app.add_directive('pldm-pdr-tables', pdr_directive)
    return {"version": "1.0", "parallel_read_safe": True}

if __name__ == "__main__":
    # For testing outside Sphinx
    from sphinx.testing.util import SphinxTestApp
    app = SphinxTestApp()
    json_files = ["pdr_definitions.json"]  # Replace with your JSON files
    parser = PDRParser(json_files)
    parent = nodes.section()
    parser.generate_sphinx_tables(app, app.builder.env.temp_data.get('state'), parent)
    print(parent.pformat())