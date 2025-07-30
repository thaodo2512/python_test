import sys
import yaml

# Enum mappings for type
PLDM_TYPE_MAP = {
    'COMPACT_SENSOR': 'PLDM_COMPACT_SENSOR',
    'NUMERIC_SENSOR': 'PLDM_NUMERIC_SENSOR',
    'STATE_SENSOR': 'PLDM_STATE_SENSOR',
    'NUMERIC_EFFECTOR': 'PLDM_NUMERIC_EFFECTOR',
    'STATE_EFFECTOR': 'PLDM_STATE_EFFECTOR',
    'FILE_TRANSFER_SENSOR': 'PLDM_FILE_TRANSFER_SENSOR'
}

# Enum mappings for base_unit
PLDM_BASE_UNIT_MAP = {
    'UNSPECIFIED': 'PLDM_UNIT_UNSPECIFIED',
    'BYTES': 'PLDM_UNIT_BYTES',
    'DEGREES_C': 'PLDM_UNIT_DEGREES_C'
}

# Enum mappings for sensor_init
PLDM_SENSOR_INIT_MAP = {
    'NO_INIT': 'PLDM_SENSOR_NO_INIT',
    'USE_INIT_PDR': 'PLDM_SENSOR_USE_INIT_PDR',
    'ENABLE': 'PLDM_SENSOR_ENABLE',
    'DISABLE': 'PLDM_SENSOR_DISABLE'
}

def main(yaml_file, output_c):
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)
    
    objects = data.get('pldm_objects', [])
    if not objects:
        sys.exit("No pldm_objects defined in YAML")
    
    # Validate basics (ignore missing non-required)
    ids = set()
    for obj in objects:
        obj_id = obj.get('common_config', {}).get('id', 0)
        if obj_id in ids:
            sys.exit(f"Duplicate id: {obj_id}")
        ids.add(obj_id)
        type_str = obj.get('type')
        if type_str and type_str not in PLDM_TYPE_MAP:
            sys.exit(f"Invalid type '{type_str}'. Valid: {list(PLDM_TYPE_MAP.keys())}")
    
    with open(output_c, 'w') as f:
        f.write('#include "pldm_objects.h"\n\n')  # Assume header name
        f.write('const PldmObject pldm_objects[] = {\n')
        for obj in objects:
            type_enum = PLDM_TYPE_MAP.get(obj.get('type', 'COMPACT_SENSOR'), 'PLDM_COMPACT_SENSOR')
            common_config = obj.get('common_config', {})
            specific_config = obj.get('specific_config', {})
            common_data = obj.get('common_data', {})
            specific_data = obj.get('specific_data', {})
            
            f.write('    {\n')
            f.write(f'        .type = {type_enum},\n')
            
            # Common config (defaults for missing)
            f.write('        .common_config = {\n')
            f.write(f'            .id = {common_config.get("id", 0)},\n')
            f.write(f'            .entity_type = {common_config.get("entity_type", 0)},\n')
            f.write(f'            .entity_instance = {common_config.get("entity_instance", 0)},\n')
            f.write(f'            .container_id = {common_config.get("container_id", 0)},\n')
            f.write(f'            .enabled = {str(common_config.get("enabled", false)).lower()},\n')
            base_unit_str = common_config.get("base_unit", 'UNSPECIFIED')
            base_unit = PLDM_BASE_UNIT_MAP.get(base_unit_str, 'PLDM_UNIT_UNSPECIFIED')
            f.write(f'            .base_unit = {base_unit},\n')
            f.write(f'            .unit_modifier = {common_config.get("unit_modifier", 0)}\n')
            f.write('        },\n')
            
            # Specific config (union, select based on type; ignore missing subfields)
            f.write('        .specific_config = {\n')
            if 'numeric_sensor' in specific_config:
                ns = specific_config['numeric_sensor']
                init_str = ns.get('init', 'NO_INIT')
                init_enum = PLDM_SENSOR_INIT_MAP.get(init_str, 'PLDM_SENSOR_NO_INIT')
                thresholds = ns.get('thresholds', [0.0] * 6)
                thresh_str = '{' + ', '.join(f'{{ .real32 = {t}f }}' for t in thresholds) + '}'
                supp_thresh = ns.get('supported_thresholds', {})
                f.write(f'            .numeric_sensor = {{\n')
                f.write(f'                .init = {init_enum},\n')
                f.write(f'                .data_size = {ns.get("data_size", 0)},\n')
                f.write(f'                .resolution = {ns.get("resolution", 0.0)}f,\n')
                f.write(f'                .offset = {ns.get("offset", 0.0)}f,\n')
                f.write(f'                .accuracy = {ns.get("accuracy", 0.0)}f,\n')
                f.write(f'                .plus_tolerance = {ns.get("plus_tolerance", 0.0)}f,\n')
                f.write(f'                .minus_tolerance = {ns.get("minus_tolerance", 0.0)}f,\n')
                f.write(f'                .hysteresis = {ns.get("hysteresis", 0.0)}f,\n')
                f.write(f'                .supported_thresholds = {{\n')
                f.write(f'                    .lower_fatal = {str(supp_thresh.get("lower_fatal", false)).lower()},\n')
                f.write(f'                    .lower_critical = {str(supp_thresh.get("lower_critical", false)).lower()},\n')
                f.write(f'                    .lower_warning = {str(supp_thresh.get("lower_warning", false)).lower()},\n')
                f.write(f'                    .upper_warning = {str(supp_thresh.get("upper_warning", false)).lower()},\n')
                f.write(f'                    .upper_critical = {str(supp_thresh.get("upper_critical", false)).lower()},\n')
                f.write(f'                    .upper_fatal = {str(supp_thresh.get("upper_fatal", false)).lower()},\n')
                f.write(f'                    .reserved = 0\n')
                f.write('                }},\n')
                f.write(f'                .thresholds = {thresh_str},\n')
                f.write(f'                .is_linear = {str(ns.get("is_linear", false)).lower()}\n')
                f.write('            }\n')
            elif 'state_sensor' in specific_config:
                ss = specific_config['state_sensor']
                possible_states = ss.get('possible_states', [[0] * 32] * 8)
                ps_str = '{' + ', '.join('{' + ', '.join(str(b) for b in ps) + '}' for ps in possible_states) + '}'
                f.write(f'            .state_sensor = {{\n')
                f.write(f'                .state_set_id = {ss.get("state_set_id", 0)},\n')
                f.write(f'                .composite_count = {ss.get("composite_count", 0)},\n')
                f.write(f'                .possible_states = {ps_str}\n')
                f.write('            }\n')
            elif 'numeric_effector' in specific_config:
                ne = specific_config['numeric_effector']
                f.write(f'            .numeric_effector = {{\n')
                f.write(f'                .data_size = {ne.get("data_size", 0)},\n')
                f.write(f'                .min_set = {{ .real32 = {ne.get("min_set", 0.0)}f }},\n')
                f.write(f'                .max_set = {{ .real32 = {ne.get("max_set", 0.0)}f }},\n')
                f.write(f'                .default_set = {{ .real32 = {ne.get("default_set", 0.0)}f }}\n')
                f.write('            }\n')
            elif 'state_effector' in specific_config:
                se = specific_config['state_effector']
                possible_states = se.get('possible_states', [0] * 32)
                ps_str = '{' + ', '.join(str(b) for b in possible_states) + '}'
                f.write(f'            .state_effector = {{\n')
                f.write(f'                .state_set_id = {se.get("state_set_id", 0)},\n')
                f.write(f'                .possible_states = {ps_str}\n')
                f.write('            }\n')
            f.write('        },\n')
            
            # Common data
            f.write('        .common_data = {\n')
            f.write(f'            .present_value = {{ .real32 = {common_data.get("present_value", 0.0)}f }},\n')
            f.write(f'            .operational_state = {common_data.get("operational_state", 0)},\n')
            f.write(f'            .event_state = {common_data.get("event_state", 0)}\n')
            f.write('        },\n')
            
            # Specific data
            f.write('        .specific_data = {\n')
            if 'numeric_data' in specific_data:
                nd = specific_data['numeric_data']
                readings = nd.get('readings', [0.0] * 8)
                read_str = '{' + ', '.join(f'{{ .real32 = {r}f }}' for r in readings) + '}'
                thresh_ex = nd.get('threshold_exceeded', [false] * 6)
                te_str = '{' + ', '.join(str(te).lower() for te in thresh_ex) + '}'
                f.write(f'            .numeric_data = {{\n')
                f.write(f'                .readings = {read_str},\n')
                f.write(f'                .threshold_exceeded = {te_str}\n')
                f.write('            }\n')
            elif 'state_data' in specific_data:
                sd = specific_data['state_data']
                curr_states = sd.get('current_states', [0] * 8)
                prev_states = sd.get('previous_states', [0] * 8)
                cs_str = '{' + ', '.join(str(s) for s in curr_states) + '}'
                ps_str = '{' + ', '.join(str(s) for s in prev_states) + '}'
                f.write(f'            .state_data = {{\n')
                f.write(f'                .current_states = {cs_str},\n')
                f.write(f'                .previous_states = {ps_str}\n')
                f.write('            }\n')
            elif 'numeric_effector_data' in specific_data:
                ned = specific_data['numeric_effector_data']
                f.write(f'            .numeric_effector_data = {{\n')
                f.write(f'                .current_setting = {{ .real32 = {ned.get("current_setting", 0.0)}f }}\n')
                f.write('            }\n')
            elif 'state_effector_data' in specific_data:
                sed = specific_data['state_effector_data']
                f.write(f'            .state_effector_data = {{\n')
                f.write(f'                .current_state = {sed.get("current_state", 0)}\n')
                f.write('            }\n')
            f.write('        }\n')
            f.write('    },\n')
        f.write('};\n')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit("Usage: python generate_pldm_table.py <yaml_file> <output_c>")
    main(sys.argv[1], sys.argv[2])
