# SDV_KNK: Software-Defined Vehicle Predictive Maintenance Platform

**SDV_KNK** is a high-fidelity, real-time telemetry and health monitoring ecosystem for modern Software-Defined Vehicles. By integrating the **NASA CMAPSS** (Turbofan Engine Degradation) dataset with a custom OBD-II simulation layer, this platform provides real-time **Remaining Useful Life (RUL)** predictions across four critical vehicle domains: Engine, Brakes, Battery, and Tires, using numerical and acoustic data.

---

## 4-Layer Architecture

The platform is engineered using a decoupled, event-driven architecture to simulate authentic automotive data flows.

1.  **Simulation Layer (`simulator/`)**: A multi-component NASA CMAPSS replayer that streams heavy-duty sensor telemetry (FD001-FD004) over MQTT as synchronized CAN-Bus frames.
2.  **Inference Engine (`backend/`)**: A FastAPI powerhouse that performs real-time RUL regression using **LightGBM**. It features a dynamic Rules Engine for triggering **DTC (Diagnostic Trouble Codes)** and **Mode $02 Freeze Frame** alerts upon critical degradation.
3.  **Acoustic Diagnostic Node**: A secondary MLP-based classifier that analyzes engine acoustics (MFCC extraction) to detect mechanical anomalies like piston slap or rod knock from audio samples.
4.  **Premium Dashboard (`frontend/`)**: A high-end React dashboard built with **Glassmorphism** aesthetics. It provides interactive SVG gauges, Recharts-powered performance matrices, and Framer Motion stagger animations for a true "A.I. Command Center" experience.

---

## Getting Started

### 1. Environment Setup
Create a Python virtual environment and install the required dependencies:
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Dataset Preparation
Download the **NASA CMAPSS** dataset and place the `.txt` files in `data/raw/`. Ensure you have:
- `train_FD001.txt` ... `train_FD004.txt`

### 3. Execution Sequence
Start the platform in the following order (utilizing separate terminal windows):

**I. Launch the Backend API**
```bash
python backend/main.py
```

**II. Start the NASA Simulator**
```bash
python simulator/replay.py
```

**III. Boot the Frontend Dashboard**
```bash
cd frontend
npm install
npm run dev
```

---

## Key Features

- **Predictive Analytics**: Multi-domain RUL regression provides exact "Cycles to Failure" counts.
- **Cybersecurity IDS**: An Isolation Forest firewall detects spoofed CAN payload injections.
- **Acoustic Waveform**: Visualizes mechanical health trends through audio-inference waveforms.
- **Command Center UI**: A dark-mode, glass-morphic interface designed for mission-critical monitoring.

---

## Model Performance
| Domain | Model Type | RMSE (Test) | MAE (Test) |
| :--- | :--- | :--- | :--- |
| **Engine** | LightGBM Regressor | ~12.5 | ~9.2 |
| **Brakes** | LightGBM Regressor | ~18.6 | ~13.4 |
| **Battery** | LightGBM Regressor | ~14.1 | ~10.5 |
| **Tires** | LightGBM Regressor | ~16.8 | ~12.1 |

---

## Author
Developed by the **KNK team** for advanced SDV research and predictive maintenance optimization. This platform focuses on deep health analytics and RUL prediction rather than basic functional status monitoring.
