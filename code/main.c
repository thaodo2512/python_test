////


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include "pdr_data.h"

#define PDR_USE
#define GET_FIELD_TOKEN(x, y, z) x ## _ ## y ## _ ## z
#define GET_PDR_FIELD_VALUE(sensor_test, 0, sensorID)
#define GET_PDR_FIELD_VALUE(sensor_test_2, 0, sensorID)


int main(int argc, char *argv[]) {
    printf("Hello, World!\n");
    printf("This is a test program.\n");

    // Example usage of the macro
    int sensor_id = GET_FIELD_TOKEN(sensor_test, 0, sensorID);
    return 0;
}