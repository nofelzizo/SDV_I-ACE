import pandas as pd
import numpy as np
import os

# NASA C-MAPSS dataset features
COLUMNS = ['engine_id', 'cycle', 'op_setting_1', 'op_setting_2', 'op_setting_3'] + \
          [f'sensor_{i}' for i in range(1, 22)]

# Generic EV names to map for UI / Dashboard
GENERIC_EV_MAPPING = [
    "Temperature", "Pressure", "Vibration", "Voltage", 
    "Current", "Speed", "Strain", "Flow", "Load", "Efficiency"
]

def load_nasa_data(filepath: str) -> pd.DataFrame:
    """Loads NASA C-MAPSS space-separated dataset."""
    if not os.path.exists(filepath):
        return pd.DataFrame()
    return pd.read_csv(filepath, sep=r'\s+', header=None, names=COLUMNS)

def calculate_rul(df: pd.DataFrame, max_rul: int = 125) -> pd.DataFrame:
    """Calculates piecewise RUL for NASA datasets."""
    if df.empty: return df
    
    # Calculate RUL per engine
    max_cycles = df.groupby('engine_id')['cycle'].max().reset_index()
    max_cycles.rename(columns={'cycle': 'max_cycle'}, inplace=True)
    df_merged = df.merge(max_cycles, on='engine_id', how='left')
    df_merged['RUL'] = df_merged['max_cycle'] - df_merged['cycle']
    
    # Piecewise linear cap (improves predictive performance for health indicators)
    df_merged['RUL'] = df_merged['RUL'].apply(lambda x: min(x, max_rul))
    df_merged.drop(columns=['max_cycle'], inplace=True)
    return df_merged

def get_top_sensors(df: pd.DataFrame, target: str = 'RUL', n: int = 10) -> list:
    """Identifies top N sensors by absolute correlation with RUL."""
    sensors = [f'sensor_{i}' for i in range(1, 22)]
    # Drop sensors with zero variance (common in NASA datasets)
    valid_sensors = [s for s in sensors if df[s].nunique() > 1]
    
    correlations = df[valid_sensors + [target]].corr()[target].abs().sort_values(ascending=False)
    # The first element is RUL (correlation 1.0), so we take the next N
    top_n = correlations.index[1:n+1].tolist()
    return top_n

def get_sensor_mapping(top_sensors: list) -> dict:
    """Maps specific NASA sensors to generic EV terms for the UI."""
    mapping = {}
    for i, sensor in enumerate(top_sensors):
        if i < len(GENERIC_EV_MAPPING):
            mapping[sensor] = GENERIC_EV_MAPPING[i]
        else:
            mapping[sensor] = f"Sensor_{i+1}"
    return mapping

if __name__ == "__main__":
    print("Preprocess module ready for NASA CMAPSS integration.")
