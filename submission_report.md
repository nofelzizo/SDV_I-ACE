# SDV_KNK: Technical Implementation Report
**Category**: Predictive Maintenance & Advanced Telemetry
**Organization**: KNK Team

---

## 1. Executive Summary
SDV_KNK (Software-Defined(or Diagnostic) Vehicle ) is a robust analytical framework designed to shift vehicle maintenance from reactive to proactive. By utilizing the NASA CMAPSS dataset for RUL (Remaining Useful Life) regression and real-time audio-inference for mechanical diagnostics, the platform offers a 360-degree view of vehicle health through a mission-critical "Command Center" dashboard.

## 2. System Architecture (4-Layer Model)
The project utilizes a decoupled, event-driven infrastructure:

1.  **Vehicle Simulation Layer**:
    - **Dataset**: NASA CMAPSS (Turbofan Engine Degradation).
    - **Implementation**: A multi-threaded Python simulator streams 21 sensor channels across 4 distinct domains (Engine, Brakes, Battery, Tires) via MQTT.
2.  **Telemetry Broker**:
    - **Implementation**: Mosquitto (MQTT).
    - **Payload**: Synchronized CAN-Bus frame emulation (0x7E8) formatted in JSON for real-time processing.
3.  **Inference & Rules Engine**:
    - **Backend**: FastAPI (Python).
    - **Regression**: Independent LightGBM nodes for each vehicle domain.
    - **Security**: Isolation Forest model for Intrusion Detection (IDS) on the CAN-bus.
    - **Acoustics**: MLP-based classifier analyzing MFCC features for instantaneous engine knock detection.
4.  **UI/UX Visualization**:
    - **Frontend**: React.js with Tailwind CSS.
    - **Aesthetics**: High-fidelity Glassmorphism design with Framer Motion animations.
    - **Analytics**: Recharts-powered performance matrices.

## 3. Data Methodology
### 3.1 Dataset Integration
We utilized all four NASA CMAPSS sub-datasets (FD001-FD004) to simulate various operational conditions (Sea Level, High Altitude, High Frequency).
- **Preprocessing**: Feature correlation analysis was used to identify the top 10 most relevant sensors per domain (e.g., T48 temperature, P15 pressure).
- **RUL Calculation**: Piecewise linear RUL (capped at 125 cycles) was implemented to handle early-life stable regimes and late-life degradation curves.

### 3.2 Feature Engineering
- **Numerical**: Min-Max scaling and sliding window averages were applied to filter noise.
- **Acoustic**: Audio samples were transformed using MFCC (Mel-frequency cepstral coefficients) to capture the frequency-domain signatures of various mechanical states (Normal vs. Knock).

## 4. Machine Learning Pipeline
### 4.1 RUL Regression (LightGBM)
Chosen for its exceptionally low inference latency (critical for real-time SDV apps) and high accuracy on tabular data.
- **Hyperparameters**: `n_estimators=150`, `learning_rate=0.07`, `max_depth=12`.
- **Validation**: 85/15 train-test split per NASA domain.

### 4.2 Intrusion Detection (Isolation Forest)
We treat CAN-Bus spoofing as an anomaly detection problem. The Isolation Forest model monitors incoming data payloads for statistically improbable sensor spikes or "impossible" transitions (e.g., RPM jumping from 1k to 10k in 1ms).

## 5. User Interaction & Visualization
The dashboard is designed for high-stress monitoring environments:
- **SVG Gauges**: Real-time visualization of "Cycles to Failure" with color-coded safety zones.
- **Performance Matrix**: A synchronized area chart mapping Engine Speed vs Temperature to identify thermal runaway patterns.
- **Acoustic Waveform**: A dynamic visual representation of the audio-inference engine's confidence.

## 6. Conclusion
SDV_KNK demonstrates the feasibility of combining heavy industrial datasets (NASA) with consumer-facing web technologies (React/FastAPI). It provides a scalable blueprint for future vehicle fleets to reduce downtime, enhance safety, and lower operational costs through intelligent, data-driven maintenance.
