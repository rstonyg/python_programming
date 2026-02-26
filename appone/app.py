import os
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from flask import Flask, render_template, request, redirect, url_for, abort, flash
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "postage_reversals.db")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

# DB: uses DATABASE_URL if provided (Render Postgres), otherwise local SQLite file
db_url = os.environ.get("DATABASE_URL")
if db_url:
    db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


STATUS_OPTIONS = [
    "Requested",
    "Submitted",
    "In Review",
    "Approved",
    "Rejected",
    "Completed",
]


class PostageReversal(db.Model):
    __tablename__ = "postage_reversals"

    id = db.Column(db.Integer, primary_key=True)

    date_requested = db.Column(db.Date, nullable=False)

    requested_by = db.Column(db.String(120), nullable=False)
    mailing_facility = db.Column(db.String(120), nullable=False)

    client = db.Column(db.String(120), nullable=False)
    job_number = db.Column(db.String(64), nullable=False)
    job_name = db.Column(db.String(200), nullable=False)

    postage_statement_id = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # store cents accurately as integer
    postage_amount_cents = db.Column(db.Integer, nullable=False)

    reason = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(32), nullable=False, default="Requested")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def touch(self):
        self.updated_at = datetime.utcnow()

    @property
    def postage_amount(self) -> str:
        # display dollars
        dollars = Decimal(self.postage_amount_cents) / Decimal(100)
        return f"{dollars:,.2f}"


with app.app_context():
    db.create_all()


def parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None


def parse_money_to_cents(value: str) -> int | None:
    # Accept "123.45" or "$123.45" or "1,234.56"
    if not value:
        return None
    cleaned = value.strip().replace("$", "").replace(",", "")
    try:
        amt = Decimal(cleaned)
        if amt < 0:
            return None
        cents = int((amt * 100).quantize(Decimal("1")))
        return cents
    except (InvalidOperation, ValueError):
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Create a new reversal request
        date_requested = parse_date(request.form.get("date_requested", ""))
        requested_by = (request.form.get("requested_by") or "").strip()
        mailing_facility = (request.form.get("mailing_facility") or "").strip()
        client = (request.form.get("client") or "").strip()
        job_number = (request.form.get("job_number") or "").strip()
        job_name = (request.form.get("job_name") or "").strip()
        postage_statement_id = (request.form.get("postage_statement_id") or "").strip()
        reason = (request.form.get("reason") or "").strip()
        notes = (request.form.get("notes") or "").strip()

        qty_raw = (request.form.get("quantity") or "").strip()
        amount_raw = (request.form.get("postage_amount") or "").strip()

        # Validate required fields
        errors = []
        if not date_requested:
            errors.append("Date Requested is required (YYYY-MM-DD).")
        if not requested_by:
            errors.append("Requested By is required.")
        if not mailing_facility:
            errors.append("Mailing Facility is required.")
        if not client:
            errors.append("Client is required.")
        if not job_number:
            errors.append("Job Number is required.")
        if not job_name:
            errors.append("Job Name is required.")
        if not postage_statement_id:
            errors.append("Postage Statement ID is required.")
        if not reason:
            errors.append("Reason is required.")

        try:
            quantity = int(qty_raw)
            if quantity <= 0:
                raise ValueError
        except Exception:
            errors.append("Quantity must be a positive whole number.")
            quantity = 0

        cents = parse_money_to_cents(amount_raw)
        if cents is None:
            errors.append("Postage Amount must be a valid number like 123.45.")

        if errors:
            for e in errors:
                flash(e, "error")
            # fall through to GET rendering with current list
        else:
            rec = PostageReversal(
                date_requested=date_requested,
                requested_by=requested_by,
                mailing_facility=mailing_facility,
                client=client,
                job_number=job_number,
                job_name=job_name,
                postage_statement_id=postage_statement_id,
                quantity=quantity,
                postage_amount_cents=cents,
                reason=reason,
                notes=notes if notes else None,
                status="Requested",
            )
            db.session.add(rec)
            db.session.commit()
            return redirect(url_for("index"))

    reversals = PostageReversal.query.order_by(PostageReversal.created_at.desc()).all()
    return render_template("index.html", reversals=reversals, statuses=STATUS_OPTIONS)


@app.route("/reversal/<int:reversal_id>", methods=["GET", "POST"])
def reversal_detail(reversal_id: int):
    rec = PostageReversal.query.get(reversal_id)
    if not rec:
        abort(404)

    if request.method == "POST":
        # Update status + notes (and optionally other fields)
        status = (request.form.get("status") or "").strip()
        notes = (request.form.get("notes") or "").strip()

        if status not in STATUS_OPTIONS:
            flash("Invalid status.", "error")
        else:
            rec.status = status
            rec.notes = notes if notes else None
            rec.touch()
            db.session.commit()
            flash("Updated.", "ok")
            return redirect(url_for("reversal_detail", reversal_id=rec.id))

    return render_template("reversal.html", rec=rec, statuses=STATUS_OPTIONS)


@app.route("/delete/<int:reversal_id>", methods=["POST"])
def delete_reversal(reversal_id: int):
    rec = PostageReversal.query.get(reversal_id)
    if not rec:
        abort(404)
    db.session.delete(rec)
    db.session.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port, debug=True)