import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/")
def home():
    return jsonify(status="ok", message="Hello from Flask on Render!")

@app.get("/health")
def health():
    return jsonify(ok=True)

if __name__ == "__main__":
    # Local dev only. Render uses gunicorn to run the app.
    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port, debug=True)