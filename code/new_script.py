#!/usr/bin/env python3
"""
Generate a pre-built PDR blob, index table, and access macros for all PLDM PDR JSON files.
Usage: python gen_script.py <json_dir> <c_scan_dir> <output_header.h>
"""
import os
import json
import sys
import argparse

# -----------------------------------------------------------------------------
# Define all your PDR field types and order here in code. Do NOT generate C structs;
# you will manually add them to your C headers.
FIELD_TYPES = {
    'CompactNumericSensorPDR': [
        ('recordHandle',            'uint32'),
        ('PDRHeaderVersion',        'uint8'),
        ('PDRType',                 'uint8'),
        ('recordChangeNumber',      'uint8'),
        ('dataLength',              'uint16'),
        ('PLDMTerminusHandle',      'uint8'),
        ('sensorID',                'uint16'),
        ('entityType',              'uint16'),
        ('entityInstanceNumber',    'uint16'),
        ('containerID',             'uint16'),
        ('sensorNameStringByteLength', 'uint16'),
        ('baseUnit',                'uint16'),
        ('unitModifier',            'uint16'),
        ('occurrenceRate',          'uint8'),
        ('rangeFieldSupport',       'uint8'),
        ('warningHigh',             'uint8'),
        ('warningLow',              'uint8'),
        ('criticalHigh',            'uint8'),
        ('criticalLow',             'uint8'),
        ('fatalHigh',               'uint8'),
        ('fatalLow',                'uint8'),
        ('sensorNameString',        'strUTF8'),
    ],
    # ...add other PDR types as needed...
}

# -----------------------------------------------------------------------------

def load_json_records(json_dir):
    """Load all JSON PDR definitions as (record_dict, basename, index) tuples."""
    records = []
    for root, _, files in os.walk(json_dir):
        for fname in files:
            if not fname.endswith('.json'):
                continue
            path = os.path.join(root, fname)
            with open(path, 'r') as f:
                data = json.load(f)
            base = os.path.splitext(fname)[0]
            if isinstance(data, list):
                for idx, rec in enumerate(data):
                    records.append((rec, base, idx))
            elif isinstance(data, dict):
                records.append((data, base, 0))
    return records


def has_pdr_use(c_dir):
    """Scan C sources for the PDR_USE marker."""
    for root, _, files in os.walk(c_dir):
        for fname in files:
            if not (fname.endswith('.c') or fname.endswith('.h')):
                continue
            path = os.path.join(root, fname)
            with open(path, 'r', errors='ignore') as f:
                if '#define PDR_USE' in f.read():
                    return True
    return False


def pack_field(value, ftype):
    """Convert a field value to little-endian bytes based on its type."""
    if ftype == 'uint8':
        return int(value).to_bytes(1, 'little')
    if ftype == 'uint16':
        return int(value).to_bytes(2, 'little')
    if ftype == 'uint32':
        return int(value).to_bytes(4, 'little')
    if ftype == 'strUTF8':
        s = str(value).encode('utf-8')
        return s + b'\x00'
    raise ValueError(f"Unsupported field type '{ftype}'")


def build_blob_and_index(records):
    """Build the binary blob and index entries from JSON records."""
    blob = bytearray()
    index = []  # list of (record_handle, offset)
    # Track per-record offsets for macro generation
    offsets = []  # list of (base, idx, pdr_type, offset)

    for rec, base, idx in records:
        offset = len(blob)
        pdr_type = rec.get('pdr_type')
        if pdr_type not in FIELD_TYPES:
            raise ValueError(f"Unknown pdr_type '{pdr_type}' in {base}.json")
        # Pack each field in order
        for fname, ftype in FIELD_TYPES[pdr_type]:
            if fname not in rec:
                raise KeyError(f"Missing field '{fname}' for record '{base}_{idx}'")
            blob.extend(pack_field(rec[fname], ftype))
        # Record the handle and offset
        handle = rec.get('recordHandle')
        index.append((handle, offset))
        offsets.append((base, idx, pdr_type, offset))

    return blob, index, offsets


def format_blob(blob):
    """Return C initializer list for the blob (hex bytes, 12 per line)."""
    lines = []
    for i in range(0, len(blob), 12):
        chunk = blob[i:i+12]
        line = ', '.join(f'0x{b:02X}' for b in chunk)
        lines.append('    ' + line)
    return ',
'.join(lines)


def generate_header(records, blob, index, offsets, out_path):
    """Generate the C header with blob, index, and access macros."""
    with open(out_path, 'w') as hdr:
        hdr.write('#pragma once\n')
        hdr.write('#ifdef PDR_USE\n\n')
        hdr.write('#include <stdint.h>\n#include <stddef.h>\n\n')

        # PDRIndexEntry definition
        hdr.write('typedef struct { uint32_t record_handle; uint32_t offset; } PDRIndexEntry;\n\n')

        # Blob
        hdr.write('__attribute__((section(".pdr_data")))\n')
        hdr.write('static const uint8_t pdr_blob[] = {\n')
        hdr.write(format_blob(blob) + '\n');
        hdr.write('};\n\n')

        # Blob size
        hdr.write('static const size_t pdr_blob_size = sizeof(pdr_blob);\n\n')

        # Index table
        hdr.write('static const PDRIndexEntry pdr_index[] = {\n')
        for (handle, offset) in index:
            hdr.write(f'    {{ {handle}, {offset} }},\n')
        hdr.write('};\n\n')

        # Record count
        hdr.write('#define pdr_record_count (sizeof(pdr_index)/sizeof(pdr_index[0]))\n\n')

        # Offsets and field macros
        for base, idx, pdr_type, offset in offsets:
            name = f"{base}_{idx}"
            # offset macro
            hdr.write(f'#define {name}_offset ({offset})\n')
            # field macros
            for fname, _ in FIELD_TYPES[pdr_type]:
                hdr.write(f'#define {name}_{fname} \\
')
                hdr.write(f'    ((({pdr_type}*)(pdr_blob + {name}_offset))->')
                hdr.write(f'{fname})\n')
            hdr.write('\n')

        hdr.write('#endif // PDR_USE\n')


def main():
    parser = argparse.ArgumentParser(description='Generate PDR binary blob and macros')
    parser.add_argument('json_dir', help='Directory with PDR JSON files')
    parser.add_argument('c_scan_dir', help='Directory to scan for #define PDR_USE')
    parser.add_argument('output_header', help='Path to write generated header (.h)')
    args = parser.parse_args()

    if not has_pdr_use(args.c_scan_dir):
        print('No #define PDR_USE found: skipping PDR header generation.')
        sys.exit(0)

    records = load_json_records(args.json_dir)
    blob, index, offsets = build_blob_and_index(records)
    generate_header(records, blob, index, offsets, args.output_header)
    print(f'Generated PDR header: {args.output_header} ({len(blob)} bytes, {len(index)} records)')

if __name__ == '__main__':
    main()
