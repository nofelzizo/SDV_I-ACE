import os
import json
import joblib
import logging
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Local imports for NASA data handling
from preprocess import load_nasa_data, calculate_rul, get_top_sensors, get_sensor_mapping

# -----------------
# Setup & Paths
# -----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | [TRAINING] | %(message)s")
logger = logging.getLogger("SDV_TRAINER")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
MODEL_DIR = os.path.dirname(__file__)

# Mapping each domain to a NASA CMAPSS dataset for the SDV demo
# FD001: Simple Conditions | FD002: Complex Conditions | FD003: Simple + Faults | FD004: Complex + Faults
DOMAIN_DATASETS = {
    "engine": "train_FD001.txt",
    "brakes": "train_FD002.txt",
    "battery": "train_FD003.txt",
    "tires": "train_FD004.txt"
}

def execute_training_pipeline():
    """Builds and serializes RUL models for 4 vehicle domains."""
    logger.info("Initializing multi-domain training sequence...")
    
    performance_metrics = {}
    system_mappings = {}

    for domain, source_file in DOMAIN_DATASETS.items():
        filepath = os.path.join(DATA_DIR, source_file)
        logger.info(f"Training node [{domain}] using source: {source_file}")

        # 1. Data Ingestion
        df = load_nasa_data(filepath)
        if df.empty:
            logger.error(f"Failed to ingest {source_file}. Path may be invalid.")
            continue

        # 2. Logic: Calculate Remaining Useful Life (RUL)
        df = calculate_rul(df)
        
        # 3. Dynamic Feature Selection (identifying most correlated sensors)
        # We select 10 sensors to keep the simulation real-time and responsive.
        top_features = get_top_sensors(df, n=10)
        friendly_mapping = get_sensor_mapping(top_features)
        
        system_mappings[domain] = {
            "features": top_features,
            "display_names": friendly_mapping
        }

        X = df[top_features]
        y = df['RUL']
        
        # 4. Training Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)

        # 5. Model Definition
        # Using LightGBM for its high performance with tabular data and low memory footprint in the backend.
        model = lgb.LGBMRegressor(
            n_estimators=150,
            learning_rate=0.07,  # Balanced for convergence and speed
            max_depth=12,
            random_state=42,
            n_jobs=-1,
            verbosity=-1
        )
        
        model.fit(X_train, y_train)

        # 6. Evaluation
        preds = model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        mae = mean_absolute_error(y_test, preds)
        
        logger.info(f"Node [{domain}] Performance -> RMSE: {rmse:.2f} | MAE: {mae:.2f}")

        # 7. Serialization
        joblib.dump(model, os.path.join(MODEL_DIR, f"lgbm_{domain}_model.pkl"))
        
        performance_metrics[f"{domain}_rmse"] = round(float(rmse), 2)
        performance_metrics[f"{domain}_mae"] = round(float(mae), 2)

    # Export metadata for the live simulation and dashboard
    with open(os.path.join(MODEL_DIR, "model_metrics.json"), "w") as f:
        json.dump(performance_metrics, f, indent=4)
        
    with open(os.path.join(MODEL_DIR, "sensor_mappings.json"), "w") as f:
        json.dump(system_mappings, f, indent=4)
        
    logger.info("Pipeline complete. Models and registry synchronized.")

if __name__ == "__main__":
    execute_training_pipeline()
