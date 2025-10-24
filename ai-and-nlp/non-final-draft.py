from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd
import numpy as np
import spacy
import joblib
import logging
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# CONFIGURATION

app = FastAPI(title="🩺 Medical Triage Severity API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development: allow all origins. In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globals for model and embedder
clf = None
embedder = None

LOG_FILE = "triage_logs.txt"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "triage2.csv")
MODEL_PATH = "severity_classifier.joblib"
EMBEDDER_PATH = "embedder_model"

# Logging setup
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)


# INPUT MODEL
class TriageInput(BaseModel):
    text: str

# TEXT PREPROCESSING
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def preprocess(text: str) -> str:
    doc = nlp(text.lower())
    return " ".join([t.lemma_ for t in doc if t.is_alpha and not t.is_stop])


# LOAD OR TRAIN MODEL
def load_or_train_model():
    if os.path.exists(MODEL_PATH) and os.path.exists(EMBEDDER_PATH):
        clf_local = joblib.load(MODEL_PATH)
        embedder_local = SentenceTransformer(EMBEDDER_PATH)
        print("✅ Model and embedder loaded.")
    else:
        print(" Training model for the first time...")
        df = pd.read_csv(DATA_PATH)
        df["text"] = df["text"].astype(str).fillna("")
        df["cleaned"] = df["text"].apply(preprocess)

        X = df["cleaned"].tolist()
        y = df["severity"].tolist()

        embedder_local = SentenceTransformer("all-MiniLM-L6-v2")
        X_embeddings = embedder_local.encode(X, show_progress_bar=True)

        X_train, X_test, y_train, y_test = train_test_split(
            X_embeddings, y, test_size=0.2, random_state=42, stratify=y
        )

        clf_local = LogisticRegression(max_iter=2000, class_weight="balanced", C=2.0)
        clf_local.fit(X_train, y_train)

        y_pred = clf_local.predict(X_test)
        print("\n🔍 Classification Report:\n", classification_report(y_test, y_pred))

        joblib.dump(clf_local, MODEL_PATH)
        embedder_local.save(EMBEDDER_PATH)
        print("✅ Model and embedder saved.")

    return clf_local, embedder_local


# STARTUP EVENT
@app.on_event("startup")
def startup_event():
    global clf, embedder
    clf, embedder = load_or_train_model()


# ROUTES
@app.get("/")
def home():
    return {"message": "🩺 Triage Severity Classifier is running", "version": "1.0"}

@app.post("/predict")
async def predict(data: TriageInput):
    try:
        user_input = data.text.strip()
        cleaned = preprocess(user_input)
        user_vec = embedder.encode([cleaned])
        pred = clf.predict(user_vec)[0]
        probs = clf.predict_proba(user_vec)[0]
        conf = float(np.max(probs))

        # Log to file
        logging.info(f"Input: {user_input} | Prediction: {pred} | Confidence: {conf:.2f}")

        result = {
            "input": user_input,
            "predicted_severity": pred,
            "confidence": round(conf, 2)
        }

        return JSONResponse(content=result)

    except Exception as e:
        logging.error(f"Error processing input: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

# RUN APP
if __name__ == "__main__":
    # Run Uvicorn server directly
    uvicorn.run("non-final-draft:app", host="0.0.0.0", port=5000, reload=True)
