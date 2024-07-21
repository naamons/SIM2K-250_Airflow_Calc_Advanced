# definitions.py
definitions = {
    "CNPNJM___T3A": {
        "airflow_map": {"location": 0x255D1C, "size": (12, 16), "math": lambda x: 0.042389562829 * x, "bit": 16},
        "airflow_rpm_axis": {"location": 0x25417A, "size": 16, "math": lambda x: x, "bit": 16},
        "airflow_torque_axis": {"location": 0x25424A, "size": 12, "math": lambda x: 0.03125 * x, "bit": 16},
        "reference_torque_map": {"location": 0x257B04, "size": (12, 16), "math": lambda x: 0.03125 * x, "bit": 16},
        "reference_torque_rpm_axis": {"location": 0x257AE2, "size": 16, "math": lambda x: x, "bit": 16},
        "reference_torque_airflow_axis": {"location": 0x25403E, "size": 12, "math": lambda x: 0.042389562829 * x, "bit": 16}
    }
}
