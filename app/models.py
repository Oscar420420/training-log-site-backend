from __future__ import annotations
from datetime import datetime
import os

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from . import db, login_manager

# -------------------- Auth --------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="lifter")  # lifter | coach

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))

def bootstrap_users_if_configured():
    """
    Optional convenience:
    If you set env vars, the app will ensure these users exist on startup.

    BOOTSTRAP_COACH_USER / PASS
    BOOTSTRAP_LIFTER_USER / PASS
    """
    coach_u = os.environ.get("BOOTSTRAP_COACH_USER")
    coach_p = os.environ.get("BOOTSTRAP_COACH_PASS")
    lifter_u = os.environ.get("BOOTSTRAP_LIFTER_USER")
    lifter_p = os.environ.get("BOOTSTRAP_LIFTER_PASS")

    if coach_u and coach_p:
        _ensure_user(coach_u, coach_p, "coach")
    if lifter_u and lifter_p:
        _ensure_user(lifter_u, lifter_p, "lifter")

def _ensure_user(username: str, password: str, role: str):
    u = User.query.filter_by(username=username).first()
    if u:
        # Do not overwrite passwords automatically (safer).
        return
    u = User(username=username, role=role)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()

# -------------------- Training structure --------------------

class Period(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    blocks = db.relationship("Block", backref="period", cascade="all, delete-orphan", order_by="Block.number")

class Block(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey("period.id"), nullable=False)
    number = db.Column(db.Integer, nullable=False)

    weeks = db.relationship("Week", backref="block", cascade="all, delete-orphan", order_by="Week.number")

    __table_args__ = (db.UniqueConstraint("period_id", "number", name="uq_block_period_number"),)

class Week(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    block_id = db.Column(db.Integer, db.ForeignKey("block.id"), nullable=False)
    number = db.Column(db.Integer, nullable=False)

    days = db.relationship("Day", backref="week", cascade="all, delete-orphan", order_by="Day.number")

    __table_args__ = (db.UniqueConstraint("block_id", "number", name="uq_week_block_number"),)

class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week_id = db.Column(db.Integer, db.ForeignKey("week.id"), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    label = db.Column(db.String(200), nullable=True)

    exercises = db.relationship("ExerciseEntry", backref="day", cascade="all, delete-orphan", order_by="ExerciseEntry.name")

    __table_args__ = (db.UniqueConstraint("week_id", "number", name="uq_day_week_number"),)

class ExerciseEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_id = db.Column(db.Integer, db.ForeignKey("day.id"), nullable=False)

    name = db.Column(db.String(200), nullable=False)
    work = db.Column(db.Text, nullable=True)

    lifter_comment = db.Column(db.Text, nullable=True)
    coach_comment = db.Column(db.Text, nullable=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    media = db.relationship("Media", backref="entry", cascade="all, delete-orphan", order_by="Media.created_at")

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey("exercise_entry.id"), nullable=False)

    kind = db.Column(db.String(10), nullable=False)  # "file" or "link"
    url = db.Column(db.Text, nullable=False)         # link URL or /media/<filename>

    original_name = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
