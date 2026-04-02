import pandas as pd
import time
import json
import logging
import paho.mqtt.client as mqtt
import os
import sys

# -----------------
# Configuration
# -----------------
MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
OBD_TOPIC = "sdv/obd/live"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
META_DIR = os.path.join(BASE_DIR, "model")

# NASA CMAPSS Sensor Columns (consistent with preprocess.py)
COLUMNS = ['engine_id', 'cycle', 'op1', 'op2', 'op3'] + [f'sensor_{i}' for i in range(1, 22)]

logging.basicConfig(level=logging.INFO, format="%(asctime)s | [SIMULATOR] | %(message)s")
logger = logging.getLogger("SDV_SIM")

def load_system_meta():
    """Load sensor mappings generated during the model training phase."""
    path = os.path.join(META_DIR, "sensor_mappings.json")
    if not os.path.exists(path):
        logger.error(f"Metadata missing at {path}. Please run training first.")
        sys.exit(1)
    with open(path, "r") as f:
        return json.load(f)

def get_telemetry_frame(dfs, indices, mappings):
    """Assembles a synchronized CAN-bus frame from multiple component life-cycles."""
    payload = {
        "mode": "01",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "can_response_id": "0x7E8",
        "data": []
    }

    for domain, df in dfs.items():
        # Cycle through unit 1 data for deterministic demo
        unit_data = df[df['engine_id'] == 1].reset_index(drop=True)
        current_idx = indices[domain]
        
        if current_idx >= len(unit_data):
            indices[domain] = 0
            current_idx = 0
            logger.info(f"Domain [{domain}] data cycle reset.")

        row = unit_data.iloc[current_idx]
        indices[domain] += 1

        meta = mappings.get(domain, {})
        features = meta.get("features", [])
        names = meta.get("display_names", {})

        # Include cycle count in metadata for synchronization
        if domain == "engine":
            payload["data"].append({
                "name": "internal_cycle",
                "value": int(row['cycle'])
            })

        for f in features:
            val = float(row[f])
            friendly_name = names.get(f, f)
            payload["data"].append({
                "name": f"{domain.capitalize()}_{friendly_name}",
                "value": val
            })
            
    return payload

def start_simulation():
    mappings = load_system_meta()
    
    datasets = {
        "engine": "train_FD001.txt",
        "brakes": "train_FD002.txt",
        "battery": "train_FD003.txt",
        "tires": "train_FD004.txt"
    }

    dfs = {}
    for domain, file in datasets.items():
        path = os.path.join(DATA_DIR, file)
        if os.path.exists(path):
            dfs[domain] = pd.read_csv(path, sep=r'\s+', header=None, names=COLUMNS)
            logger.info(f"Initialized data-stream for {domain}")
        else:
            logger.warning(f"Missing dataset for {domain}: {file}")

    if not dfs:
        logger.error("No valid datasets found in data/raw. Aborting.")
        return

    # Tracking simulation state
    indices = {k: 0 for k in dfs.keys()}
    client = mqtt.Client("sdv_knk_simulator")

    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        logger.info(f"Connected to MQTT Broker at {MQTT_HOST}")
        
        while True:
            frame = get_telemetry_frame(dfs, indices, mappings)
            client.publish(OBD_TOPIC, json.dumps(frame))
            
            # Simulated 1Hz CAN frequency
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        logger.info("Simulation halted by user.")
    except Exception as e:
        logger.error(f"Simulation runner crashed: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    start_simulation()
