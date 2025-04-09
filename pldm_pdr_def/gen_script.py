import argparse
import yaml
import json

def generate_auto_gen(field_def):
    """
    Recursively generate 'auto-gen' values for a field definition.
    """
    if isinstance(field_def, str):
        # Simple field type (e.g., "uint16")
        return "auto-gen"
    elif isinstance(field_def, dict):
        # Nested structure (e.g., {"languageTag": "strASCII"})
        return {k: generate_auto_gen(v) for k, v in field_def.items()}
    elif isinstance(field_def, list):
        # List of items (e.g., [{"languageTag": "strASCII", "name": "strUTF-16BE"}])
        return [generate_auto_gen(item) for item in field_def]
    else:
        raise ValueError(f"Invalid field definition: {field_def}")

def generate_pdr_json(yaml_path, output_json_path):
    """
    Generate a PDR JSON file from a YAML definition.
    """
    # Load YAML content
    with open(yaml_path, "r") as f:
        pdr_def = yaml.safe_load(f)

    # Extract PDR type (e.g., "EntityAuxiliaryNames")
    pdr_type_key = list(pdr_def.keys())[0]
    pdr_type = pdr_type_key.replace("PDR", "")

    header_def = {k: v for k, v in pdr_def[pdr_type_key].items() if k == "commonHeader"}
    body_def = {k: v for k, v in pdr_def[pdr_type_key].items() if k != "commonHeader"}

    # Generate the body with "auto-gen" values
    body = generate_auto_gen(body_def)


    # Construct the full PDR JSON structure
    pdr_json = {
        "pdr_type": pdr_type,
        "header": header_def,
        "body": body
    }

    # Write to the output JSON file
    with open(output_json_path, "w") as f:
        json.dump(pdr_json, f, indent=4)
    print(f"Generated JSON file: {output_json_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PDR JSON from YAML.")
    parser.add_argument("yaml_path", type=str, help="Path to the input YAML file.")
    parser.add_argument("output_json_path", type=str, help="Path to the output JSON file.")
    args = parser.parse_args()
    generate_pdr_json(args.yaml_path, args.output_json_path)