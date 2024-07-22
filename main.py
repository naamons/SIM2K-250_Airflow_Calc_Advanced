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
        col_data = []
        for j, value in enumerate(data[:, i]):
            try:
                if np.isnan(value):
                    st.warning(f"NaN value encountered at row {j}, column {i}")
                    continue  # Skip this value
                converted_value = inverse_math_func(value)
                if not np.isfinite(converted_value):
                    raise ValueError(f"Converted value is not finite: {converted_value}")
                col_data.append(converted_value)
            except Exception as e:
                st.error(f"Error converting value: {value} at row {j}, column {i}. Error: {str(e)}")
                st.error(f"Data type: {type(value)}")
                return
        if not col_data:
            st.error(f"No valid data in column {i}")
            return
        try:
            write_bin_data(bin_data, location + i * rows * (bit // 8), col_data, bit)
        except Exception as e:
            st.error(f"Error writing data to binary. Error: {str(e)}")
            st.error(f"Column {i}, data: {col_data}")
            return

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

            st.header("Step 3: Input New Torque Axis for Airflow Map")
            st.write("The values below are extracted from the uploaded template. You can edit them if needed.")
            
            torque_axis_str1 = "\n".join(map(str, airflow_torque_axis))
            new_torque_axis_input1 = st.text_area("New Torque Axis (one value per line)", torque_axis_str1)
            new_torque_axis1 = [float(torque.strip()) for torque in new_torque_axis_input1.split("\n")]

            if st.button("Generate New Airflow Map and New Torque Map"):
                # Calculate new airflow values using the new torque axis
                airflow_per_torque = np.array(airflow_map) / np.array(airflow_torque_axis)[:, np.newaxis]
                new_airflow_values = airflow_per_torque * np.array(new_torque_axis1)[:, np.newaxis]

                # Create a DataFrame to display the results
                result_df1 = pd.DataFrame(new_airflow_values, columns=airflow_rpm_axis, index=new_torque_axis1)
                result_df1.index.name = "Torque (Nm)"

                st.write("### New Airflow Map")
                st.dataframe(result_df1)

                # Calculate the suggested new torque map by averaging each row of the new airflow map
                suggested_new_torque_axis = np.mean(new_airflow_values, axis=1)

                # Calculate new torque map values using the suggested new torque axis
                new_torque_map_values = np.array(new_airflow_values) * suggested_new_torque_axis[:, np.newaxis]

                # Create a DataFrame to display the new torque map
                result_df2 = pd.DataFrame(new_torque_map_values, columns=airflow_rpm_axis, index=suggested_new_torque_axis)
                result_df2.index.name = "Suggested Torque (Nm)"

                st.write("### New Torque Map")
                st.dataframe(result_df2)

                # Display the new airflow values for debugging
                st.write("New Airflow Values:")
                st.write(new_airflow_values)

                # Display the new torque map values for debugging
                st.write("New Torque Map Values:")
                st.write(new_torque_map_values)

if __name__ == "__main__":
    main()
