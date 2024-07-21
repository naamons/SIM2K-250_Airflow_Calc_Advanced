import struct
import numpy as np

# Definition for the CNPNJM___T3A maps
definition = {
    "airflow_map": {"location": 0x255D1C, "size": (12, 16), "math": lambda x: 0.042389562829 * x, "bit": 16},
    "airflow_rpm_axis": {"location": 0x25417A, "size": 16, "math": lambda x: x, "bit": 16},
    "airflow_torque_axis": {"location": 0x25424A, "size": 12, "math": lambda x: 0.03125 * x, "bit": 16},
    "reference_torque_map": {"location": 0x257B04, "size": (12, 16), "math": lambda x: 0.03125 * x, "bit": 16},
    "reference_torque_rpm_axis": {"location": 0x257AE2, "size": 16, "math": lambda x: x, "bit": 16},
    "reference_torque_airflow_axis": {"location": 0x25403E, "size": 12, "math": lambda x: 0.042389562829 * x, "bit": 16}
}

# Helper functions to read binary data
def read_bin_data(bin_data, location, size, bit):
    if bit == 16:
        fmt = 'H'
    elif bit == 8:
        fmt = 'B'
    else:
        raise ValueError("Unsupported bit size")
    
    data = []
    for i in range(size):
        value, = struct.unpack_from(fmt, bin_data, location + i * (bit // 8))
        data.append(value)
    return data

def read_map(bin_data, location, rows, cols, bit, math_func):
    data = []
    for i in range(rows):
        row = read_bin_data(bin_data, location + i * cols * (bit // 8), cols, bit)
        data.append([math_func(x) for x in row])
    return np.array(data)

# Read the binary file
bin_file_path = 'SXTHNK [Elantra N Engine (Original)] [CNPNJM___T3A][csokay].bin'
with open(bin_file_path, 'rb') as f:
    bin_data = f.read()

# Extract the maps and axes using the definition
airflow_map = read_map(bin_data, definition["airflow_map"]["location"], 
                       definition["airflow_map"]["size"][0], definition["airflow_map"]["size"][1], 
                       definition["airflow_map"]["bit"], definition["airflow_map"]["math"])
airflow_rpm_axis = read_bin_data(bin_data, definition["airflow_rpm_axis"]["location"], 
                                 definition["airflow_rpm_axis"]["size"], definition["airflow_rpm_axis"]["bit"])
airflow_rpm_axis = [definition["airflow_rpm_axis"]["math"](x) for x in airflow_rpm_axis]
airflow_torque_axis = read_bin_data(bin_data, definition["airflow_torque_axis"]["location"], 
                                    definition["airflow_torque_axis"]["size"], definition["airflow_torque_axis"]["bit"])
airflow_torque_axis = [definition["airflow_torque_axis"]["math"](x) for x in airflow_torque_axis]

reference_torque_map = read_map(bin_data, definition["reference_torque_map"]["location"], 
                                definition["reference_torque_map"]["size"][0], definition["reference_torque_map"]["size"][1], 
                                definition["reference_torque_map"]["bit"], definition["reference_torque_map"]["math"])
reference_torque_rpm_axis = read_bin_data(bin_data, definition["reference_torque_rpm_axis"]["location"], 
                                          definition["reference_torque_rpm_axis"]["size"], definition["reference_torque_rpm_axis"]["bit"])
reference_torque_rpm_axis = [definition["reference_torque_rpm_axis"]["math"](x) for x in reference_torque_rpm_axis]
reference_torque_airflow_axis = read_bin_data(bin_data, definition["reference_torque_airflow_axis"]["location"], 
                                              definition["reference_torque_airflow_axis"]["size"], definition["reference_torque_airflow_axis"]["bit"])
reference_torque_airflow_axis = [definition["reference_torque_airflow_axis"]["math"](x) for x in reference_torque_airflow_axis]

# Print the extracted data for verification
print("Airflow Map:")
print(airflow_map)
print("Airflow RPM Axis:")
print(airflow_rpm_axis)
print("Airflow Torque Axis:")
print(airflow_torque_axis)
print("Reference Torque Map:")
print(reference_torque_map)
print("Reference Torque RPM Axis:")
print(reference_torque_rpm_axis)
print("Reference Torque Airflow Axis:")
print(reference_torque_airflow_axis)
