import os
import joblib
import numpy as np
import logging
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split

import warnings
warnings.filterwarnings('ignore')
import librosa

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("Acoustic_DNN")

# Path to the real Kaggle Dataset provided
AUDIO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "raw", "car diagnostics dataset"))
MODEL_DIR = os.path.dirname(__file__)

def extract_mfcc(file_path):
    try:
        # sr=22050 is the standard for Mel-Spectrogram extraction
        audio, sr = librosa.load(file_path, sr=22050)
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        # Average the features over the time axis
        mfccs_mean = np.mean(mfccs.T, axis=0)
        return mfccs_mean
    except Exception as e:
        logger.warning(f"Failed to process {file_path}: {e}")
        return None

def train_acoustic_mlp():
    logger.info("Initializing I-ACE Acoustic Deep Learning Compiler...")
    
    if not os.path.exists(AUDIO_DIR):
        logger.error(f"Kaggle Audio directory not found at {AUDIO_DIR}!")
        return

    X = []
    y = []
    classes = []

    logger.info("Parsing Kaggle Car Diagnostics Audio Directory...")
    
    state_dirs = ["idle state", "startup state", "braking state"]
    
    for state in state_dirs:
        state_dir = os.path.join(AUDIO_DIR, state)
        if not os.path.exists(state_dir):
            continue
            
        logger.info(f"Scanning {state.upper()}...")
        categories = [d for d in os.listdir(state_dir) if os.path.isdir(os.path.join(state_dir, d))]
        
        for category in categories:
            if category not in classes:
                classes.append(category)
            class_idx = classes.index(category)
            
            cat_path = os.path.join(state_dir, category)
            # Find .wav or .mp3
            audio_files = [f for f in os.listdir(cat_path) if f.endswith(".wav") or f.endswith(".mp3")]
            
            if audio_files:
                logger.info(f"Extracting signatures for Acoustic Fault Class: {category.upper()} ({len(audio_files)} files)")
            
            for filename in audio_files:
                file_path = os.path.join(cat_path, filename)
                features = extract_mfcc(file_path)
                if features is not None:
                    X.append(features)
                    y.append(class_idx)
                        
    if len(X) == 0:
        logger.error("No valid audio features extracted. Check if the folders contain .wav/.mp3 files.")
        return

    X = np.array(X)
    y = np.array(y)
    
    logger.info(f"Spectrometer calibration complete. Extracted 40-dimensional MFCCs for {len(X)} audio clips.")
    logger.info(f"Discovered {len(classes)} Acoustic Failure Profiles: {classes}")

    if len(np.unique(y)) < 2:
        logger.error("Need at least 2 mechanical classes to train the classifier!")
        return

    test_sz = 0.2 if len(X) > 10 else 0.0
    
    if test_sz > 0:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_sz, random_state=42)
    else:
        X_train, y_train = X, y

    logger.info("Training Multi-Layer Perceptron (MLP) Deep Neural Network for Audio Diagnostics...")
    mlp = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, alpha=0.01, solver='adam', random_state=42)
    mlp.fit(X_train, y_train)
    
    if test_sz > 0:
        accuracy = mlp.score(X_test, y_test)
        logger.info(f"Acoustic AI Neural Accuracy against blind test data: {accuracy * 100:.2f}%")

    # Serialize Model State and the Class Mapping Dictionary
    model_data = {
        "model": mlp,
        "classes": classes
    }
    
    model_path = os.path.join(MODEL_DIR, "audio_mlp.pkl")
    joblib.dump(model_data, model_path)
    logger.info(f"Acoustic AI successfully serialized to {model_path}. The mechanic's ear is permanently online.")

if __name__ == "__main__":
    train_acoustic_mlp()
