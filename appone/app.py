import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "names.db")

app = Flask(__name__)

# SQLite database file stored alongside app.py
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class NameEntry(db.Model):
    __tablename__ = "name_entries"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

with app.app_context():
    db.create_all()
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()

        # Basic validation
        if name:
            db.session.add(NameEntry(name=name))
            db.session.commit()

        return redirect(url_for("index"))

    entries = NameEntry.query.order_by(NameEntry.created_at.desc()).all()
    return render_template("index.html", entries=entries)

@app.route("/reset", methods=["POST"])
def reset():
    # Convenience: clears the table
    db.session.query(NameEntry).delete()
    db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    # Create tables the first time the app runs
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port, debug=True)