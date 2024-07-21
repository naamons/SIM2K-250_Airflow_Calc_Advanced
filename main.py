import streamlit as st
import pandas as pd
import numpy as np
import struct
from definitions import definitions  # Import the definitions from a separate file

# Read 16-bit or 8-bit values from the .bin file
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

# Read a map from the .bin file
def read_map(bin_data, location, rows, cols, bit, math_func):
    data = []
    for i in range(rows):
        row = read_bin_data(bin_data, location + i * cols * (bit // 8), cols, bit)
        data.append([math_func(x) for x in row])
    return np.array(data)

# Read an inverse map from the .bin file (12x16)
def read_inverse_map(bin_data, location, rows, cols, bit, math_func):
    data = []
    for i in range(cols):
        col = read_bin_data(bin_data, location + i * rows * (bit // 8), rows, bit)
        data.append([math_func(x) for x in col])
    return np.array(data).T

# Write 16-bit or 8-bit values to the .bin file
def write_bin_data(bin_data, location, data, bit):
    if bit == 16:
        fmt = 'H'
    elif bit == 8:
        fmt = 'B'
    else:
        raise ValueError("Unsupported bit size")

    for i, value in enumerate(data):
        struct.pack_into(fmt, bin_data, location + i * (bit // 8), int(value))

# Write a map to the .bin file
def write_map(bin_data, location, data, bit, inverse_math_func):
    rows, cols = data.shape
    for i in range(rows):
        row_data = [inverse_math_func(value) for value in data[i]]
        write_bin_data(bin_data, location + i * cols * (bit // 8), row_data, bit)

# Write an inverse map to the .bin file (12x16)
def write_inverse_map(bin_data, location, data, bit, inverse_math_func):
    rows, cols = data.shape
    for i in range(cols):
        col_data = [inverse_math_func(value) for value in data[:, i]]
        write_bin_data(bin_data, location + i * rows * (bit // 8), col_data, bit)

def main():
    st.title("ECU Map Rescaler - Advanced Mode")

    st.header("Step 1: Upload the ECU .bin File")
    uploaded_bin = st.file_uploader("Upload your ECU .bin file", type="bin")

    if uploaded_bin is not None:
        bin_data = uploaded_bin.read()

        st.header("Step 2: Select Definition")
        definition = st.selectbox("Select the definition:", list(definitions.keys()))

        if definition:
            def_details = definitions[definition]

            # Read the airflow map and its axes
            airflow_map = read_inverse_map(bin_data, def_details["airflow_map"]["location"], 
                                           def_details["airflow_map"]["size"][0], def_details["airflow_map"]["size"][1], 
                                           def_details["airflow_map"]["bit"], def_details["airflow_map"]["math"])
            airflow_rpm_axis = read_bin_data(bin_data, def_details["airflow_rpm_axis"]["location"], 
                                             def_details["airflow_rpm_axis"]["size"], def_details["airflow_rpm_axis"]["bit"])
            airflow_rpm_axis = [def_details["airflow_rpm_axis"]["math"](x) for x in airflow_rpm_axis]
            airflow_torque_axis = read_bin_data(bin_data, def_details["airflow_torque_axis"]["location"], 
                                                def_details["airflow_torque_axis"]["size"], def_details["airflow_torque_axis"]["bit"])
            airflow_torque_axis = [def_details["airflow_torque_axis"]["math"](x) for x in airflow_torque_axis]

            st.write("### Original Airflow Map")
            df_airflow = pd.DataFrame(airflow_map, columns=airflow_rpm_axis, index=airflow_torque_axis)
            st.dataframe(df_airflow)

            # Debugging: Show the raw data read from the bin file
            st.write("#### Raw Airflow Map Data")
            st.write(airflow_map)
            st.write("#### Raw Airflow RPM Axis Data")
            st.write(airflow_rpm_axis)
            st.write("#### Raw Airflow Torque Axis Data")
            st.write(airflow_torque_axis)

            # Read the reference torque map and its axes
            reference_torque_map = read_inverse_map(bin_data, def_details["reference_torque_map"]["location"], 
                                                    def_details["reference_torque_map"]["size"][0], def_details["reference_torque_map"]["size"][1], 
                                                    def_details["reference_torque_map"]["bit"], def_details["reference_torque_map"]["math"])
            reference_torque_rpm_axis = read_bin_data(bin_data, def_details["reference_torque_rpm_axis"]["location"], 
                                                      def_details["reference_torque_rpm_axis"]["size"], def_details["reference_torque_rpm_axis"]["bit"])
            reference_torque_rpm_axis = [def_details["reference_torque_rpm_axis"]["math"](x) for x in reference_torque_rpm_axis]
            reference_torque_airflow_axis = read_bin_data(bin_data, def_details["reference_torque_airflow_axis"]["location"], 
                                                          def_details["reference_torque_airflow_axis"]["size"], def_details["reference_torque_airflow_axis"]["bit"])
            reference_torque_airflow_axis = [def_details["reference_torque_airflow_axis"]["math"](x) for x in reference_torque_airflow_axis]

            st.write("### Original Reference Torque Map")
            df_reference_torque = pd.DataFrame(reference_torque_map, columns=reference_torque_rpm_axis, index=reference_torque_airflow_axis)
            st.dataframe(df_reference_torque)

            # Debugging: Show the raw data read from the bin file
            st.write("#### Raw Reference Torque Map Data")
            st.write(reference_torque_map)
            st.write("#### Raw Reference Torque RPM Axis Data")
            st.write(reference_torque_rpm_axis)
            st.write("#### Raw Reference Torque Airflow Axis Data")
            st.write(reference_torque_airflow_axis)

            # Display the extracted torque axis as a text area
            st.header("Step 3: Input New Torque Axis for Airflow Map")
            st.write("The values below are extracted from the uploaded template. You can edit them if needed.")
            
            torque_axis_str1 = "\n".join(map(str, airflow_torque_axis))
            new_torque_axis_input1 = st.text_area("New Torque Axis (one value per line)", torque_axis_str1)
            new_torque_axis1 = [float(torque.strip()) for torque in new_torque_axis_input1.split("\n")]

            if st.button("Generate New Maps and Update .bin"):
                # Calculate new airflow values using the new torque axis
                airflow_per_torque = np.array(airflow_map) / np.array(airflow_torque_axis)[:, np.newaxis]
                new_airflow_values = airflow_per_torque * np.array(new_torque_axis1)[:, np.newaxis]

                # Create a DataFrame to display the results
                result_df1 = pd.DataFrame(new_airflow_values, columns=airflow_rpm_axis, index=new_torque_axis1)
                result_df1.index.name = "Torque (Nm)"

                st.write("### New Airflow Map")
                st.dataframe(result_df1)

                # Update the .bin file with new airflow map values
                write_inverse_map(bin_data, def_details["airflow_map"]["location"], new_airflow_values, def_details["airflow_map"]["bit"], lambda x: int(x / 0.042389562829))

                # Calculate new reference torque values using the new torque axis
                reference_torque_per_factor = np.array(reference_torque_map) / np.array(reference_torque_airflow_axis)[:, np.newaxis]
                new_reference_torque_values = reference_torque_per_factor * np.array(new_torque_axis1)[:, np.newaxis]

                # Create a DataFrame to display the results
                result_df2 = pd.DataFrame(new_reference_torque_values, columns=reference_torque_rpm_axis, index=new_torque_axis1)
                result_df2.index.name = "Reference Torque (Nm)"

                st.write("### New Reference Torque Map")
                st.dataframe(result_df2)

                # Update the .bin file with new reference torque map values
                write_inverse_map(bin_data, def_details["reference_torque_map"]["location"], new_reference_torque_values, def_details["reference_torque_map"]["bit"], lambda x: int(x / 0.03125))

                # Provide option to download the updated .bin file
                st.header("Step 4: Download the Updated .bin File")
                st.download_button(label
