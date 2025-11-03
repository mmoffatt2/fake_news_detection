# app.py
from flask import Flask, request, jsonify, render_template
import pandas as pd
import sqlite3
import json
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

@app.route("/task/baseline")
def baseline():
    worker_id = request.args.get("worker_id", "unknown")
    trials = df.sample(20).to_dict(orient="records")
    return render_template("baseline.html",
                           worker_id=worker_id,
                           trials=json.dumps(trials))

@app.route("/task/assisted")
def assisted():
    worker_id = request.args.get("worker_id", "unknown")
    trials = df.sample(20).to_dict(orient="records")
    return render_template("assisted.html",
                           worker_id=worker_id,
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
    INSERT INTO responses (worker_id, trial_id, title, text, date, ground_truth,
                           human_label, ai_label, ai_confidence, response_time,
                           confidence_rating, condition, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["worker_id"],
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
    code = "COMPLETE-" + datetime.utcnow().strftime("%H%M%S")
    return f"Thank you! Your completion code is: <b>{code}</b>"

if __name__ == "__main__":
    # important for EC2
    app.run(host="0.0.0.0", port=5000)
