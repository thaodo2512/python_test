# PDR Type Mappings
# Defines the field names and their data types for each PDR type

PDR_TYPES = {
    1: {  # Terminus Locator PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "terminusValidity": "uint8",
        "tid": "uint8",
        "containerId": "uint16",
        "terminusLocatorType": "uint8",
        "terminusLocatorValueSize": "uint8",
        "terminusLocatorValue": {
            "terminusInstance": "uint8",
            "uuid": "uint8"
        }
    },
    2: {  # Numeric Sensor PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "sensorId": "uint16",
        "entityType": "uint16",
        "entityInstanceNumber": "uint16",
        "containerId": "uint16",
        "sensorInit": "uint8",
        "sensorHysteresis": "uint8",
        "sensorType": "uint8",
        "sensorReadingType": "uint8",
        "eventMessageGlobalEnable": "uint8",
        "sensorEventMessageEnable": "uint8",
        "baseUnit": "uint8",
        "unitModifier": "int8",
        "sensorAuxiliaryNamesPdr": "uint32"
    },
    3: {  # Numeric Sensor Initialization PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "sensorId": "uint16",
        "initState": "uint8",
        "rangeMin": "real32",
        "rangeMax": "real32",
        "resolution": "real32"
    },
    4: {  # State Sensor PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "sensorId": "uint16",
        "entityType": "uint16",
        "entityInstanceNumber": "uint16",
        "containerId": "uint16",
        "stateSetId": "uint16",
        "stateValue": "uint8"
    },
    5: {  # State Sensor Initialization PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "sensorId": "uint16",
        "initState": "uint8",
        "possibleStates": "uint8"
    },
    6: {  # Sensor Auxiliary Names PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "sensorId": "uint16",
        "name": "strASCII",
        "languageTag": "strASCII"
    },
    7: {  # OEM Unit PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "oemUnitId": "uint16",
        "unitDescription": "strASCII"
    },
    8: {  # OEM State Set PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "oemStateSetId": "uint16",
        "stateDescription": "strASCII"
    },
    9: {  # Numeric Effecter PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "effecterId": "uint16",
        "entityType": "uint16",
        "entityInstanceNumber": "uint16",
        "containerId": "uint16",
        "effecterValue": "real32",
        "units": "strASCII"
    },
    10: {  # Numeric Effecter Initialization PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "effecterId": "uint16",
        "initState": "uint8",
        "rangeMin": "real32",
        "rangeMax": "real32"
    },
    11: {  # State Effecter PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "effecterId": "uint16",
        "entityType": "uint16",
        "entityInstanceNumber": "uint16",
        "containerId": "uint16",
        "stateSetId": "uint16",
        "stateValue": "uint8"
    },
    12: {  # State Effecter Initialization PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "effecterId": "uint16",
        "initState": "uint8",
        "possibleStates": "uint8"
    },
    13: {  # Effecter Auxiliary Names PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "effecterId": "uint16",
        "name": "strASCII",
        "languageTag": "strASCII"
    },
    14: {  # OEM Effecter Semantic PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "effecterId": "uint16",
        "oemSemanticId": "uint16",
        "description": "strASCII"
    },
    15: {  # Entity Association PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "containerEntityType": "uint16",
        "containerEntityInstance": "uint16",
        "containedEntityType": "uint16",
        "containedEntityInstance": "uint16"
    },
    16: {  # Entity Auxiliary Names PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "entityType": "uint16",
        "entityInstance": "uint16",
        "name": "strASCII",
        "languageTag": "strASCII"
    },
    17: {  # OEM EntityID PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "oemEntityId": "uint16",
        "description": "strASCII"
    },
    18: {  # Interrupt Association PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "interruptId": "uint16",
        "entityType": "uint16",
        "entityInstance": "uint16"
    },
    19: {  # Event Log PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "eventLogId": "uint16",
        "timestamp": "uint64",
        "eventData": "strASCII"
    },
    20: {  # FRU Record Set PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "fruRecordSetId": "uint16",
        "entityType": "uint16",
        "entityInstance": "uint16",
        "fruData": "strASCII"
    },
    21: {  # OEM Device PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "oemDeviceId": "uint16",
        "deviceDescription": "strASCII"
    },
    22: {  # OEM PDR
        "recordHandle": "uint32",
        "version": "uint8",
        "pdrType": "uint8",
        "recordChangeNumber": "uint16",
        "dataLength": "uint16",
        "terminusHandle": "uint16",
        "oemId": "uint16",
        "customData": "strASCII"
    }
}

from pdr_type_mappings import PDR_TYPES

# Example usage
def print_pdr_types(pdr_type):
    type_map = PDR_TYPES.get(pdr_type, {})
    for field, field_type in type_map.items():
        if isinstance(field_type, dict):
            print(f"{field}: (nested structure)")
            for sub_field, sub_type in field_type.items():
                print(f"  {sub_field}: {sub_type}")
        else:
            print(f"{field}: {field_type}")

# Test the function
print_pdr_types(2)
