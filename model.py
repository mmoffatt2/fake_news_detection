# model.py
import os
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Path to your trained model folder
MODEL_PATH = os.getenv("TRAINED_MODEL_DIR", "./trained_model")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load trained tokenizer + model
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH).to(DEVICE)
model.eval()

def predict_fake_news(title: str, text_field: str):
    combined = f"[NEWS] {title or ''} || {text_field or ''}".strip()

    inputs = tokenizer(
        combined,
        return_tensors="pt",
        truncation=True,
        max_length=384
    ).to(DEVICE)

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = F.softmax(logits, dim=1)[0]

    # Dynamically identify correct indexes based on config
    id2label = {int(k): v for k, v in model.config.id2label.items()}
    false_idx = [i for i, v in id2label.items() if v.lower() == "false"][0]
    true_idx  = [i for i, v in id2label.items() if v.lower() == "true"][0]

    false_prob = probs[false_idx].item()
    true_prob  = probs[true_idx].item()

    pred_label = "REAL" if true_prob >= false_prob else "FAKE"
    confidence = round(max(true_prob, false_prob) * 100, 2)

    return pred_label, confidence
