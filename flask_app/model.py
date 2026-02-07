import os
import pandas as pd
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_PATH, "dataset.csv")

MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "credibility_model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "factual_encoder.pkl")

# Load CSV & model
df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
df.columns = [c.strip().lower() for c in df.columns]

model = joblib.load(MODEL_PATH)
factual_encoder = joblib.load(ENCODER_PATH)

DEFAULT_SCORE = 0.3
DEFAULT_TRUST = 30
DEFAULT_LABEL = "fake"

def extract_domain(url):
    if not url:
        return None
    if "://" in url:
        url = url.split("://", 1)[1]
    domain = url.split("/", 1)[0]
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.lower()

def verify_url_logic(url):
    domain = extract_domain(url)

    if not domain:
        return {
            "domain": "invalid",
            "credibility_score": DEFAULT_SCORE,
            "trust": DEFAULT_TRUST,
            "label": DEFAULT_LABEL
        }

    row = df[df["source"] == domain]

    if row.empty:
        # For unseen domains, use default
        return {
            "domain": domain,
            "credibility_score": DEFAULT_SCORE,
            "trust": DEFAULT_TRUST,
            "label": DEFAULT_LABEL
        }

    factual_val = factual_encoder.transform([row.iloc[0]["factual_reporting"]])[0]

    X_input = [[
        row.iloc[0]["credibility_score"],
        row.iloc[0]["trust"],
        factual_val
    ]]

    predicted_label = model.predict(X_input)[0]

    return {
        "domain": domain,
        "credibility_score": float(row.iloc[0]["credibility_score"]),
        "trust": float(row.iloc[0]["trust"]),
        "label": predicted_label
    }
