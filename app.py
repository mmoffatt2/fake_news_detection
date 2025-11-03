# how to ssh into ec2 instance
# ssh -i ~/mturk-key.pem ubuntu@3.145.123.180

# app.py
from flask import Flask, request, jsonify, render_template
import pandas as pd
import sqlite3
import json
import random
import string
from datetime import datetime
from model import predict_fake_news

app = Flask(__name__)

# Load CSV (title, text, date, label)
df = pd.read_csv("study_dataset.csv")

# --------- DATABASE SETUP -----------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id TEXT,
        completion_code TEXT,
        trial_id INTEGER,
        title TEXT,
        text TEXT,
        date TEXT,
        ground_truth TEXT,
        human_label TEXT,
        ai_label TEXT,
        ai_confidence REAL,
        response_time REAL,
        confidence_rating REAL,
        condition TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# --------- ROUTES -----------

def generate_code():
    return "C-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

@app.route("/task/baseline")
def baseline():
    worker_id = request.args.get("workerId") or request.args.get("worker_id") or "unknown"
    completion_code = generate_code()
    trials = df.sample(15).to_dict(orient="records")
    return render_template(
        "baseline.html",
        worker_id=worker_id,
        completion_code=completion_code,
        trials=json.dumps(trials)
    )

@app.route("/task/assisted")
def assisted():
    worker_id = request.args.get("workerId") or request.args.get("worker_id") or "unknown"
    completion_code = generate_code()
    trials = df.sample(15).to_dict(orient="records")
    return render_template("assisted.html",
                           worker_id=worker_id,
                           completion_code=completion_code,
                           trials=json.dumps(trials))

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    title = data["title"]
    text_field = data["text"]
    label, conf = predict_fake_news(title, text_field)
    return jsonify({"label": label, "confidence": conf})

@app.route("/submit_trial", methods=["POST"])
def submit_trial():
    data = request.json
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
    INSERT INTO responses (worker_id, completion_code, trial_id, title, text, date, ground_truth,
                           human_label, ai_label, ai_confidence, response_time,
                           confidence_rating, condition, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("worker_id"),
        data.get("completion_code"),
        data["trial_id"],
        data["title"],
        data["text"],
        data["date"],
        data["ground_truth"],
        data["human_label"],
        data.get("ai_label", None),
        data.get("ai_confidence", None),
        data["response_time"],
        data["confidence_rating"],
        data["condition"],
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route("/complete")
def complete():
    code = request.args.get("completion_code", "ERROR")
    return f"Thank you! Your completion code is:<br><b>{code}</b>"

if __name__ == "__main__":
    # important for EC2
    app.run(host="0.0.0.0", port=5000)
