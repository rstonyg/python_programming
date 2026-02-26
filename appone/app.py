import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "names.db")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Person(db.Model):
    __tablename__ = "people"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def touch(self):
        self.updated_at = datetime.utcnow()

with app.app_context():
    db.create_all()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if name:
            db.session.add(Person(name=name))
            db.session.commit()
        return redirect(url_for("index"))

    people = Person.query.order_by(Person.created_at.desc()).all()
    return render_template("index.html", people=people)

@app.route("/person/<int:person_id>", methods=["GET", "POST"])
def person_detail(person_id: int):
    person = Person.query.get(person_id)
    if not person:
        abort(404)

    if request.method == "POST":
        note = (request.form.get("note") or "").strip()
        person.note = note
        person.touch()
        db.session.commit()
        return redirect(url_for("person_detail", person_id=person.id))

    return render_template("person.html", person=person)

@app.route("/reset", methods=["POST"])
def reset():
    db.session.query(Person).delete()
    db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port, debug=True)