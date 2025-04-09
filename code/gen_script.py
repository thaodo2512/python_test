import os
import json
import yaml
import re

def load_yaml_files(yaml_dir):
    """Load all YAML files from a directory into a dictionary by PDR type."""
    yaml_data = {}
    for root, _, files in os.walk(yaml_dir):
        for file in files:
            if file.endswith('.yaml'):
                with open(os.path.join(root, file), 'r') as f:
                    data = yaml.safe_load(f)
                pdr_type = list(data.keys())[0]
                yaml_data[pdr_type] = data[pdr_type]
    return yaml_data

def load_json_files(json_dir):
    """Load all JSON files from a directory into a list of PDR data."""
    json_data = [] # list of list of dictionaries
    for root, _, files in os.walk(json_dir):
        for file in files:
            if file.endswith('.json'):
                file_name = os.path.splitext(file)[0]
                with open(os.path.join(root, file), 'r') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    temp = [{"file_name": file_name}]
                    temp.extend(data)  # Modifies temp in place
                    json_data.append(temp)  # Add the sublist to json_data
                else:
                    data = [{"file_name": file_name}, data]
                    json_data.append(data)
    return json_data

def get_value(data_dict, key):
    # Check if the key is directly in the main dictionary
    if key in data_dict:
        return data_dict[key]
    # Check if 'commonHeader' exists and if the key is in the sub-dictionary
    elif 'commonHeader' in data_dict and key in data_dict['commonHeader']:
        return data_dict['commonHeader'][key]
    # Return None if the key is not found in either place
    else:
        return "unknown"

def generate_binary_data(pdr_data, field_types):
    """Convert PDR data to binary format."""
    binary_data = bytearray()
    for field, value in pdr_data.items():
        if isinstance(value, dict):
            sub_binary_data = generate_binary_data(value, field_types)
            binary_data.extend(sub_binary_data)
        else:
            field_type = get_value(field_types, field)
            if field_type == 'uint8':
                binary_data.extend(int(value).to_bytes(1, 'little'))
            elif field_type == 'uint16':
                binary_data.extend(int(value).to_bytes(2, 'little'))
            elif field_type == 'uint32':
                binary_data.extend(int(value).to_bytes(4, 'little'))
            elif field_type == 'sint8':
                binary_data.extend(int(value).to_bytes(1, 'little', signed=True))
            elif field_type == 'sint16':
                binary_data.extend(int(value).to_bytes(2, 'little', signed=True))
            elif field_type == 'sint32':
                binary_data.extend(int(value).to_bytes(4, 'little', signed=True))
            elif field_type == 'float':
                binary_data.extend(float(value).hex().encode('utf-8') + b'\0')
            elif field_type == 'strUTF8':
                binary_data.extend(value.encode('utf-8') + b'\0')
            elif field_type == 'strUTF16':
                binary_data.extend(value.encode('utf-16') + b'\0')
            elif field_type == 'strUTF32':
                binary_data.extend(value.encode('utf-32') + b'\0')
            elif field_type == 'strASCII':
                binary_data.extend(value.encode('ascii') + b'\0')
        # Add more field types as needed
    return binary_data

def generate_macros(pdr_data, pdr_file_name, index, field_name):
    """Generate #define macros based on PDR data."""
    macros = []
    for field, value in pdr_data.items():
        if isinstance(value, dict):
            for sub_field, sub_value in value.items():
                field = sub_field
                value = sub_value
                if field != field_name:
                    # Skip the field that does not matche the field_name
                    continue
                macro_name = f"{pdr_file_name}_{index}_{field}"
                macros.append(f"#define {macro_name} {value}")
    return macros

def process_c_files(c_files_dir, pdr_data_list):
    """Process C files to detect PDR_USE and generate macros."""
    macros = []
    for root, _, files in os.walk(c_files_dir):
        for file in files:
            if file.endswith('.c'):
                with open(os.path.join(root, file), 'r') as f:
                    content = f.read()
                if "#define PDR_USE" in content:
                    # Find all GET_PDR_FIELD_VALUE macros
                    macro_defs = re.findall(r'#define GET_PDR_FIELD_VALUE\((\w+),\s*(\w+),\s*(\w+)\)', content)
                    for macro_def in macro_defs:
                        if macro_def:
                            pdr_file_name = macro_def[0]
                            index = macro_def[1]
                            field_name = macro_def[2]
                            if index.isdigit():
                                index = int(index)
                                if 0 <= index < len(pdr_data_list):
                                    pdr_data = [d for d in pdr_data_list if d[0].get("file_name", "") == pdr_file_name]
                                    pdr_data = pdr_data[0]
                                    pdr_data = pdr_data[ + 1]
                                    macros.extend(generate_macros(pdr_data, pdr_file_name, index, field_name))
    return macros

def generate_output(pdr_data_list, yaml_data, macros, output_header_path, output_src_path):
    """Generate a C header file with binary data and macros."""
    binary_data = bytearray()
    for pdr in pdr_data_list:
        if isinstance(pdr, list):
            for sub_pdr in pdr:
                pdr_type = sub_pdr.get('pdr_type', None) if isinstance(sub_pdr, dict) else None
                if pdr_type is None:
                    continue
                field_types = yaml_data.get(pdr_type, {})
                binary_data.extend(generate_binary_data(sub_pdr, field_types))
        elif isinstance(pdr, dict):
            pdr_type = pdr.get('pdr_type', None)
            if pdr_type is None:
                continue
            field_types = yaml_data.get(pdr_type, {})
            binary_data.extend(generate_binary_data(pdr, field_types))
        else:
            continue

    binary_array = ', '.join(f'0x{b:02x}' for b in binary_data)

    with open(output_src_path, 'w') as f:
        f.write("const char pdr_binary_data[] = {\n")
        f.write(f"    {binary_array}\n")
        f.write("};\n\n")

    with open(output_header_path, 'w') as f:
        f.write("#ifndef PDR_DATA_H\n#define PDR_DATA_H\n\n")
        f.write("const char pdr_binary_data[] = {\n")
        # f.write(f"    {binary_array}\n")
        f.write("};\n\n")
        for macro in macros:
            f.write(f"{macro}\n")
        f.write("\n#endif /* PDR_DATA_H */\n")

def main(yaml_dir, json_dir, c_files_dir, output_header_path, output_src_path):
    """Main function to process all files and generate output."""
    yaml_data = load_yaml_files(yaml_dir)
    pdr_data_list = load_json_files(json_dir)
    macros = process_c_files(c_files_dir, pdr_data_list)
    generate_output(pdr_data_list, yaml_data, macros, output_header_path, output_src_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 6:
        print("Usage: python script.py <yaml_dir> <json_dir> <c_files_dir> <output_header>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])