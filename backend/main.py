from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import logging
import asyncio
import os
import joblib
import pandas as pd
import paho.mqtt.client as mqtt
import random
import librosa
import numpy as np
import urllib.parse

# -----------------
# System Config
# -----------------
class Config:
    BROKER = "127.0.0.1"
    PORT = 1883
    TOPIC = "sdv/obd/live"
    MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model"))
    AUDIO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "raw", "car diagnostics dataset", "idle state"))
    
    # Predictive Model Sensitivity
    CRITICAL_RUL = 5.0     # Final warning threshold (reduced for reliability)
    WARNING_RUL = 55.0     # Maintenance alert threshold
    WARM_UP_CYCLES = 35    # Initial grace period buffer

# -----------------
# Setup & Logging
# -----------------
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s | [%(levelname)s] | %(name)s | %(message)s"
)
logger = logging.getLogger("SDV_BACKEND")

app = FastAPI(title="SDV_KNK API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------
# State Management
# -----------------
MODELS = {}
MAPPINGS = {}
SECURITY_MODEL = None
ACOUSTIC_MODEL = None
AUDIO_CLASSES = []

frame_counter = 0  # Global count to track demo "warm-up"

class TelemetryManager:
    """Orchestrates real-time data streaming over WebSockets."""
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections:
            self.active_connections.remove(ws)

    async def broadcast(self, payload: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception:
                pass 

telemetry_hub = TelemetryManager()

# -----------------
# Initialization
# -----------------
def init_system():
    global SECURITY_MODEL, ACOUSTIC_MODEL, AUDIO_CLASSES, MAPPINGS
    
    # Load dynamic NASA mappings from train phase
    map_file = os.path.join(Config.MODEL_PATH, "sensor_mappings.json")
    if os.path.exists(map_file):
        with open(map_file, "r") as f:
            MAPPINGS = json.load(f)
            logger.info("Successfully loaded sensor mappings from JSON.")

    # Load serialized models
    for domain in ["engine", "brakes", "tires", "battery"]:
        path = os.path.join(Config.MODEL_PATH, f"lgbm_{domain}_model.pkl")
        if os.path.exists(path):
            MODELS[domain] = joblib.load(path)
            logger.info(f"Initialized inference engine for: {domain}")
            
    # Optional Security & Audio layers
    sec_path = os.path.join(Config.MODEL_PATH, "isolation_forest.pkl")
    if os.path.exists(sec_path):
        SECURITY_MODEL = joblib.load(sec_path)
        
    audio_path = os.path.join(Config.MODEL_PATH, "audio_mlp.pkl")
    if os.path.exists(audio_path):
        try:
            audio_blob = joblib.load(audio_path)
            ACOUSTIC_MODEL = audio_blob["model"]
            AUDIO_CLASSES = audio_blob["classes"]
        except Exception:
            logger.error("Acoustic node encountered an error during startup.")

init_system()

if os.path.exists(Config.AUDIO_PATH):
    app.mount("/audio_samples", StaticFiles(directory=Config.AUDIO_PATH), name="audio_samples")

# -----------------
# Utils
# -----------------
def get_metrics():
    path = os.path.join(Config.MODEL_PATH, "model_metrics.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def extract_mapped_val(data, domain, sensory_tag):
    """Safely extracts a value from the incoming telemetry stream."""
    key_target = f"{domain.capitalize()}_{sensory_tag}"
    for entry in data:
        if entry.get("name") == key_target:
            return entry["value"]
    return 0.0

# -----------------
# Core Logic
# -----------------
def process_message(raw_msg):
    global frame_counter
    try:
        frame = json.loads(raw_msg)
        data_packets = frame.get("data", [])
        
        # Self-resetting heartbeat check
        # If the simulator loops back to start, we reset our suppression counter
        for item in data_packets:
            if item.get("name") == "internal_cycle" and item.get("value") == 1:
                if frame_counter > 50: # Avoid resetting on every packet at start
                    logger.info("Lifecycle restart detected. Resetting safety suppression.")
                    frame_counter = 0
                    
        frame_counter += 1
        predictions = {}
        processed_metrics = {}

        # Multi-domain inference loop
        for domain, meta in MAPPINGS.items():
            if domain in MODELS:
                feats = meta["features"]
                tags = meta["display_names"]
                
                # Assemble input vector
                input_vec = []
                for f in feats:
                    val = extract_mapped_val(data_packets, domain, tags[f])
                    input_vec.append(val)
                    # Normalize keys to snake_case for the frontend
                    processed_metrics[f"{domain}_{tags[f].lower()}"] = val
                
                df_input = pd.DataFrame([input_vec], columns=feats)
                predictions[domain] = float(MODELS[domain].predict(df_input)[0])

        output = {
            "mode": "01",
            "timestamp": frame.get("timestamp"),
            "can_id": frame.get("can_response_id", "0x7E8"),
            "live_metrics": processed_metrics,
            "rul_predictions": predictions,
            "ai_metadata": get_metrics(),
            "status": "NORMAL",
            "acoustic_state": global_acoustic_state,
            "acoustic_url": global_acoustic_url
        }
        
        # Predictive Maintenance Rule Hub
        if predictions:
            critical_domain = min(predictions, key=predictions.get)
            current_low_rul = predictions[critical_domain]
            
            # SUPPRESS CRITICAL FAULTS during warm-up phase to avoid  frustration
            is_warmed_up = frame_counter > Config.WARM_UP_CYCLES
            
            if current_low_rul < Config.CRITICAL_RUL and is_warmed_up:
                output["mode"] = "02"
                output["status"] = "SYSTEM_FAULT"
                output["freeze_frame"] = {
                    "domain": critical_domain,
                    "rul_value": round(current_low_rul, 2),
                    "snapshot": processed_metrics
                }
            elif current_low_rul < Config.WARNING_RUL:
                output["mode"] = "03"
                output["status"] = "MAINTENANCE_REQUIRED"
                output["dtc"] = f"DT_{critical_domain[0].upper()}{int(current_low_rul)}"
                output["target_domain"] = critical_domain

        return output
    except Exception as e:
        logger.error(f"Inference failure: {e}")
        return None

# -----------------
# BackGround Tasks
# -----------------
global_acoustic_state = "IDLE..."
global_acoustic_url = None
main_event_loop = None

@app.on_event("startup")
async def register_loop():
    global main_event_loop
    main_event_loop = asyncio.get_running_loop()

async def audio_cycle():
    global global_acoustic_state, global_acoustic_url
    while True:
        await asyncio.sleep(6.0) # Polling interval
        if ACOUSTIC_MODEL and os.path.exists(Config.AUDIO_PATH):
            try:
                folders = [d for d in os.listdir(Config.AUDIO_PATH) if os.path.isdir(os.path.join(Config.AUDIO_PATH, d))]
                if not folders: continue
                
                cat = random.choice(folders)
                base_path = os.path.join(Config.AUDIO_PATH, cat)
                files = [f for f in os.listdir(base_path) if f.endswith(".wav")]
                if not files: continue
                
                f = random.choice(files)
                f_path = os.path.join(base_path, f)
                global_acoustic_url = f"http://127.0.0.1:8000/audio_samples/{urllib.parse.quote(cat)}/{urllib.parse.quote(f)}"
                
                audio, sr = librosa.load(f_path, sr=22050)
                mfccs = np.mean(librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40).T, axis=0)
                
                pred = ACOUSTIC_MODEL.predict([mfccs])[0]
                global_acoustic_state = AUDIO_CLASSES[pred].replace("_", " ").upper()
            except Exception:
                pass 

def handle_mqtt(client, userdata, msg):
    try:
        body = msg.payload.decode('utf-8')
        result = process_message(body)
        if result and main_event_loop:
            asyncio.run_coroutine_threadsafe(telemetry_hub.broadcast(result), main_event_loop)
    except Exception as e:
        logger.error(f"MQTT handler error: {e}")

# -----------------
# Entry Point
# -----------------
mqtt_sub = mqtt.Client("sdv_listener")
mqtt_sub.on_message = handle_mqtt
mqtt_sub.connect(Config.BROKER, Config.PORT, 60)
mqtt_sub.subscribe(Config.TOPIC)
mqtt_sub.loop_start()

@app.on_event("startup")
async def launch_services():
    asyncio.create_task(audio_cycle())

@app.websocket("/ws/telemetry")
async def telemetry_stream(ws: WebSocket):
    await telemetry_hub.connect(ws)
    try:
        while True: await asyncio.sleep(1)
    except WebSocketDisconnect:
        telemetry_hub.disconnect(ws)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
