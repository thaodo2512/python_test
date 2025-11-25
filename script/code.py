import sys
import json
import yaml
import struct
import jsonschema

# Struct format map
TYPE_TO_FMT = {
    "uint8": "B", "sint8": "b",
    "uint16": "H", "sint16": "h",
    "uint32": "I", "sint32": "i",
    "uint64": "Q", "sint64": "q",
    "real32": "f"
}

# String type handling
STRING_HANDLERS = {
    "strASCII":    lambda s: s.encode('iso-8859-1') + b'\x00',
    "strUTF-8":    lambda s: s.encode('utf-8')       + b'\x00',
    "strUTF-16":   lambda s: b'\xFF\xFE' + s.encode('utf-16le') + b'\x00\x00',  # BOM + LE + null
    "strUTF-16LE": lambda s: s.encode('utf-16le')    + b'\x00\x00',
    "strUTF-16BE": lambda s: s.encode('utf-16be')    + b'\x00\x00',
}

def pack_string(value, string_type):
    if not value:
        # Empty string handling per type
        if string_type in ["strUTF-16", "strUTF-16LE", "strUTF-16BE"]:
            return b'\x00\x00' if string_type != "strUTF-16" else b'\xFF\xFE\x00\x00'
        else:
            return b'\x00'
    
    encoder = STRING_HANDLERS[string_type]
    encoded = encoder(value)
    
    # Enforce max length (including null terminator)
    max_len = 256
    if len(encoded) > max_len:
        print(f"Warning: String '{value}' truncated to {max_len} bytes", file=sys.stderr)
        encoded = encoded[:max_len-1] + b'\x00' if string_type.startswith("strUTF-16") else encoded[:max_len-1] + b'\x00'
    
    return encoded

# ... [keep all previous functions: strip_comments, replace_tbd_and_defaults, resolve_format, etc.]

def generate_c_array(schema_path, yaml_path, array_name='pdr_data'):
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    plain_data = strip_comments(data)
    plain_data = replace_tbd_and_defaults(plain_data, schema)

    try:
        jsonschema.validate(instance=plain_data, schema=schema)
    except jsonschema.exceptions.ValidationError as e:
        raise ValueError(f"Validation failed for {yaml_path}: {e}")

    data_format = '<'
    data_values = []
    binary_order = schema.get("binaryOrder", [])
    properties = schema["properties"]

    i = 0
    while i < len(binary_order):
        field_name = binary_order[i]
        if field_name == "pdrHeader":
            i += 1
            continue

        prop = properties.get(field_name)
        if not prop:
            raise ValueError(f"Missing schema property: {field_name}")

        value = plain_data.get(field_name)

        # === STRING HANDLING ===
        if "stringType" in prop:
            if value is None:
                value = ""
            if not isinstance(value, str):
                raise ValueError(f"Field {field_name} must be string, got {type(value)}")
            
            encoded_str = pack_string(value, prop["stringType"])
            # Strings are variable length → we cannot use struct.pack with format string
            # So we collect raw bytes separately
            data_values.append(encoded_str)  # Will be concatenated later
            data_format += f'{len(encoded_str)}s'  # Dynamic format
            i += 1
            continue

        # === RANGE FIELD SUPPORT (same as before) ===
        if field_name == "rangeFieldSupport":
            range_support = compute_range_field_support(plain_data, schema)
            plain_data["rangeFieldSupport"] = range_support
            fmt = prop["binaryFormat"]
            data_format += fmt
            data_values.append(range_support)
            i += 1
            # Append actual range fields
            for range_field in binary_order[i:]:
                if range_field in plain_data:
                    rprop = properties[range_field]
                    rfmt = resolve_format(range_field, plain_data, rprop)
                    data_format += rfmt
                    data_values.append(plain_data[range_field])
            break

        # === NORMAL FIELD ===
        fmt = resolve_format(field_name, plain_data, prop)
        data_format += fmt
        data_values.append(value)
        i += 1

    # Pack everything (handling mixed fixed + variable strings)
    packed_parts = []
    val_idx = 0
    for part in data_format[1:]:  # Skip initial '<'
        if part.endswith('s'):
            size = int(part[:-1])
            packed_parts.append(data_values[val_idx][:size])
            val_idx += 1
        else:
            # Fixed size field
            packed_parts.append(struct.pack('<' + part, data_values[val_idx]))
            val_idx += 1

    packed_data = b''.join(packed_parts)
    data_length = len(packed_data)

    # Update header
    plain_data["pdrHeader"]["dataLength"] = data_length

    # Pack header (always fixed)
    header_format = '<IBBHH'
    packed_header = struct.pack(header_format,
        plain_data["pdrHeader"].get("recordHandle", 0),
        plain_data["pdrHeader"].get("PDRHeaderVersion", 1),
        plain_data["pdrHeader"].get("PDRType", 0),
        plain_data["pdrHeader"].get("recordChangeNumber", 0),
        data_length
    )

    full_packed = packed_header + packed_data

    hex_bytes = ', '.join(f'0x{b:02X}' for b in full_packed)
    return f'const uint8_t {array_name}[] = {{ {hex_bytes} }};'

# ... [keep the multi-file main block from previous version]
