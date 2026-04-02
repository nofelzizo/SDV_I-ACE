import os
import joblib
import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("Cyber_Trainer")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "raw"))
DATA_FILE = os.path.join(DATA_DIR, "EV_Predictive_Maintenance_Dataset_15min.csv")
MODEL_DIR = os.path.dirname(__file__)

def train_isolation_forest():
    logger.info("Initializing I-ACE Unsupervised Cyber-Reconnaissance Trainer...")
    
    if not os.path.exists(DATA_FILE):
        logger.error(f"EVIoT dataset not found at {DATA_FILE}")
        return

    logger.info("Loading Massive EVIoT Telemetry DB into memory to construct Trust baseline...")
    try:
        df = pd.read_csv(DATA_FILE)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return

    # We extract all numeric OBD-II CAN bus signals
    # The Isolation Forest will algorithmically map a hyper-dimensional boundary 
    # encompassing normal, healthy car physics.
    features = [
        "Motor_RPM", "Motor_Temperature", "Motor_Vibration", "Motor_Torque", "Power_Consumption", "Driving_Speed",
        "Brake_Pad_Wear", "Brake_Pressure", "Reg_Brake_Efficiency",
        "Tire_Pressure", "Tire_Temperature", "Suspension_Load", "Route_Roughness",
        "SoH", "SoC", "Battery_Voltage", "Battery_Current", "Battery_Temperature", "Charge_Cycles"
    ]
    
    # Drop rows missing features entirely to prevent crashing the fit module
    df = df.dropna(subset=features)
    X = df[features]
    
    logger.info(f"Targeting physical arrays. Matrix dimensions: {X.shape}")

    # Isolation Forest Configuration
    # contamination=0.01 tells the model to conservatively assume about 1% of our raw data might be natural outliers
    model = IsolationForest(
        n_estimators=150,
        max_samples='auto',
        contamination=0.01,
        max_features=1.0,
        bootstrap=False,
        n_jobs=-1,
        random_state=42
    )

    logger.info("Compiling Unsupervised Neural Web (Isolation Forest)...")
    model.fit(X)

    # Validate mathematically
    predictions = model.predict(X)
    
    # IsolationForest outputs 1 for normal, -1 for anomaly
    anomalies = (predictions == -1).sum()
    total = len(predictions)
    logger.info(f"Calibration Complete! Naturally isolated anomalies: {anomalies} out of {total} ({100.0 * anomalies/total:.2f}%)")

    # Serialize Model State to Binary (.pkl) for the API Backend
    model_filename = "isolation_forest.pkl"
    model_path = os.path.join(MODEL_DIR, model_filename)
    joblib.dump(model, model_path)
    
    logger.info(f"Saved binary zero-day cyber-weights to {model_path}")
    logger.info("Cybersecurity Phase 1 Complete. Ready for Backend deployment.")

if __name__ == "__main__":
    train_isolation_forest()
