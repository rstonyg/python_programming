import os
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from flask import Flask, render_template, request, redirect, url_for, abort, flash
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "postage_reversals.db")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

# Database: Render Postgres via DATABASE_URL, else local SQLite
db_url = os.environ.get("DATABASE_URL")
if db_url:
    # Render sometimes uses postgres:// which SQLAlchemy doesn't like
    db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

STATUS_OPTIONS = ["Requested", "Submitted", "In Review", "Approved", "Rejected", "Completed"]


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

    # store money as cents (integer) to avoid float issues
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
    """
    Accepts: 123.45, $123.45, 1,234.56
    Returns cents as int or None if invalid.
    """
    if not value:
        return None
    cleaned = value.strip().replace("$", "").replace(",", "")
    try:
        amt = Decimal(cleaned)
        if amt < 0:
            return None
        return int((amt * 100).quantize(Decimal("1")))
    except (InvalidOperation, ValueError):
        return None


def parse_positive_int(value: str) -> int | None:
    try:
        n = int((value or "").strip())
        if n <= 0:
            return None
        return n
    except Exception:
        return None


@app.route("/", methods=["GET", "POST"])
def index():
    # Create a new request
    if request.method == "POST":
        form = request.form

        date_requested = parse_date(form.get("date_requested", ""))
        requested_by = (form.get("requested_by") or "").strip()
        mailing_facility = (form.get("mailing_facility") or "").strip()
        client = (form.get("client") or "").strip()
        job_number = (form.get("job_number") or "").strip()
        job_name = (form.get("job_name") or "").strip()
        postage_statement_id = (form.get("postage_statement_id") or "").strip()
        quantity = parse_positive_int(form.get("quantity"))
        cents = parse_money_to_cents(form.get("postage_amount") or "")
        reason = (form.get("reason") or "").strip()
        notes = (form.get("notes") or "").strip()

        errors = []
        if not date_requested:
            errors.append("Date Requested is required.")
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
        if quantity is None:
            errors.append("Quantity must be a positive whole number.")
        if cents is None:
            errors.append("Postage Amount must be a valid number like 123.45.")
        if not reason:
            errors.append("Reason for the reversal is required.")

        if errors:
            for e in errors:
                flash(e, "danger")
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
            flash(f"Created reversal request #{rec.id}.", "success")
            return redirect(url_for("index"))

    reversals = PostageReversal.query.order_by(PostageReversal.created_at.desc()).all()
    return render_template("index.html", reversals=reversals, statuses=STATUS_OPTIONS)


@app.route("/reversal/<int:reversal_id>", methods=["GET", "POST"])
def reversal_detail(reversal_id: int):
    rec = PostageReversal.query.get(reversal_id)
    if not rec:
        abort(404)

    if request.method == "POST":
        form = request.form

        date_requested = parse_date(form.get("date_requested", ""))
        requested_by = (form.get("requested_by") or "").strip()
        mailing_facility = (form.get("mailing_facility") or "").strip()
        client = (form.get("client") or "").strip()
        job_number = (form.get("job_number") or "").strip()
        job_name = (form.get("job_name") or "").strip()
        postage_statement_id = (form.get("postage_statement_id") or "").strip()
        quantity = parse_positive_int(form.get("quantity"))
        cents = parse_money_to_cents(form.get("postage_amount") or "")
        reason = (form.get("reason") or "").strip()
        notes = (form.get("notes") or "").strip()
        status = (form.get("status") or "").strip()

        errors = []
        if not date_requested:
            errors.append("Date Requested is required.")
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
        if quantity is None:
            errors.append("Quantity must be a positive whole number.")
        if cents is None:
            errors.append("Postage Amount must be a valid number like 123.45.")
        if not reason:
            errors.append("Reason for the reversal is required.")
        if status not in STATUS_OPTIONS:
            errors.append("Status is invalid.")

        if errors:
            for e in errors:
                flash(e, "danger")
        else:
            rec.date_requested = date_requested
            rec.requested_by = requested_by
            rec.mailing_facility = mailing_facility
            rec.client = client
            rec.job_number = job_number
            rec.job_name = job_name
            rec.postage_statement_id = postage_statement_id
            rec.quantity = quantity
            rec.postage_amount_cents = cents
            rec.reason = reason
            rec.notes = notes if notes else None
            rec.status = status
            rec.touch()

            db.session.commit()
            flash("Saved changes.", "success")
            return redirect(url_for("reversal_detail", reversal_id=rec.id))

    return render_template("reversal.html", rec=rec, statuses=STATUS_OPTIONS)


@app.route("/delete/<int:reversal_id>", methods=["POST"])
def delete_reversal(reversal_id: int):
    rec = PostageReversal.query.get(reversal_id)
    if not rec:
        abort(404)
    db.session.delete(rec)
    db.session.commit()
    flash(f"Deleted reversal request #{reversal_id}.", "warning")
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="127.0.0.1", port=port, debug=True)