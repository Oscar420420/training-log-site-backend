from __future__ import annotations
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user

from . import db
from .models import Period, Block, Week, Day, ExerciseEntry, Media

main_bp = Blueprint("main", __name__)

# -------------------- Helpers --------------------

def require_coach():
    if current_user.role != "coach":
        flash("Coach account required for that action.", "error")
        return False
    return True

def is_safe_external_url(url: str) -> bool:
    # Basic sanity check
    try:
        u = urlparse(url)
        return u.scheme in ("http","https") and bool(u.netloc)
    except Exception:
        return False

# -------------------- Views --------------------

@main_bp.get("/")
@login_required
def index():
    periods = Period.query.order_by(Period.created_at.desc()).all()
    return render_template("index.html", periods=periods)

@main_bp.get("/p/<int:period_id>")
@login_required
def period_view(period_id: int):
    period = Period.query.get_or_404(period_id)
    return render_template("period.html", period=period)

@main_bp.get("/b/<int:block_id>")
@login_required
def block_view(block_id: int):
    block = Block.query.get_or_404(block_id)
    return render_template("block.html", block=block)

@main_bp.get("/w/<int:week_id>")
@login_required
def week_view(week_id: int):
    week = Week.query.get_or_404(week_id)
    return render_template("week.html", week=week)

@main_bp.get("/d/<int:day_id>")
@login_required
def day_view(day_id: int):
    day = Day.query.get_or_404(day_id)
    return render_template("day.html", day=day)

@main_bp.get("/e/<int:entry_id>")
@login_required
def entry_view(entry_id: int):
    entry = ExerciseEntry.query.get_or_404(entry_id)
    return render_template("entry.html", entry=entry)

# -------------------- Create structure (coach only) --------------------

@main_bp.post("/period/create")
@login_required
def period_create():
    if not require_coach(): return redirect(url_for("main.index"))
    name = request.form.get("name","").strip()
    if not name:
        flash("Period name required", "error")
        return redirect(url_for("main.index"))
    p = Period(name=name)
    db.session.add(p)
    db.session.commit()
    flash("Period created", "ok")
    return redirect(url_for("main.period_view", period_id=p.id))

@main_bp.post("/block/create")
@login_required
def block_create():
    if not require_coach(): return redirect(url_for("main.index"))
    period_id = int(request.form.get("period_id"))
    number = int(request.form.get("number"))
    b = Block(period_id=period_id, number=number)
    db.session.add(b)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Block already exists for that period", "error")
        return redirect(url_for("main.period_view", period_id=period_id))
    flash("Block created", "ok")
    return redirect(url_for("main.block_view", block_id=b.id))

@main_bp.post("/week/create")
@login_required
def week_create():
    if not require_coach(): return redirect(url_for("main.index"))
    block_id = int(request.form.get("block_id"))
    number = int(request.form.get("number"))
    w = Week(block_id=block_id, number=number)
    db.session.add(w)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Week already exists for that block", "error")
        return redirect(url_for("main.block_view", block_id=block_id))
    flash("Week created", "ok")
    return redirect(url_for("main.week_view", week_id=w.id))

@main_bp.post("/day/create")
@login_required
def day_create():
    if not require_coach(): return redirect(url_for("main.index"))
    week_id = int(request.form.get("week_id"))
    number = int(request.form.get("number"))
    label = request.form.get("label","").strip() or None
    d = Day(week_id=week_id, number=number, label=label)
    db.session.add(d)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Day already exists for that week", "error")
        return redirect(url_for("main.week_view", week_id=week_id))
    flash("Day created", "ok")
    return redirect(url_for("main.day_view", day_id=d.id))

@main_bp.post("/exercise/create")
@login_required
def exercise_create():
    if not require_coach(): return redirect(url_for("main.index"))
    day_id = int(request.form.get("day_id"))
    name = request.form.get("name","").strip()
    work = request.form.get("work","").strip() or None
    if not name:
        flash("Exercise name required", "error")
        return redirect(url_for("main.day_view", day_id=day_id))
    e = ExerciseEntry(day_id=day_id, name=name, work=work)
    db.session.add(e)
    db.session.commit()
    flash("Exercise created", "ok")
    return redirect(url_for("main.entry_view", entry_id=e.id))

# -------------------- Delete (coach only) --------------------

@main_bp.post("/period/<int:period_id>/delete")
@login_required
def period_delete(period_id:int):
    if not require_coach(): return redirect(url_for("main.index"))
    p = Period.query.get_or_404(period_id)
    db.session.delete(p)
    db.session.commit()
    flash("Period deleted", "ok")
    return redirect(url_for("main.index"))

@main_bp.post("/block/<int:block_id>/delete")
@login_required
def block_delete(block_id:int):
    if not require_coach(): return redirect(url_for("main.index"))
    b = Block.query.get_or_404(block_id)
    pid = b.period_id
    db.session.delete(b)
    db.session.commit()
    flash("Block deleted", "ok")
    return redirect(url_for("main.period_view", period_id=pid))

@main_bp.post("/week/<int:week_id>/delete")
@login_required
def week_delete(week_id:int):
    if not require_coach(): return redirect(url_for("main.index"))
    w = Week.query.get_or_404(week_id)
    bid = w.block_id
    db.session.delete(w)
    db.session.commit()
    flash("Week deleted", "ok")
    return redirect(url_for("main.block_view", block_id=bid))

@main_bp.post("/day/<int:day_id>/delete")
@login_required
def day_delete(day_id:int):
    if not require_coach(): return redirect(url_for("main.index"))
    d = Day.query.get_or_404(day_id)
    wid = d.week_id
    db.session.delete(d)
    db.session.commit()
    flash("Day deleted", "ok")
    return redirect(url_for("main.week_view", week_id=wid))

@main_bp.post("/exercise/<int:entry_id>/delete")
@login_required
def exercise_delete(entry_id:int):
    if not require_coach(): return redirect(url_for("main.index"))
    e = ExerciseEntry.query.get_or_404(entry_id)
    did = e.day_id
    db.session.delete(e)
    db.session.commit()
    flash("Exercise deleted", "ok")
    return redirect(url_for("main.day_view", day_id=did))

# -------------------- Editing comments/work (both roles) --------------------

@main_bp.post("/exercise/<int:entry_id>/update")
@login_required
def exercise_update(entry_id:int):
    e = ExerciseEntry.query.get_or_404(entry_id)
    # Both can edit their own field; coach can edit everything.
    work = request.form.get("work","").strip()
    lifter_comment = request.form.get("lifter_comment","").strip()
    coach_comment = request.form.get("coach_comment","").strip()

    if current_user.role == "coach":
        e.work = work or None
        e.lifter_comment = lifter_comment or None
        e.coach_comment = coach_comment or None
    else:
        # lifter can edit lifter_comment; work stays coach-controlled
        e.lifter_comment = lifter_comment or None

    db.session.commit()
    flash("Saved", "ok")
    return redirect(url_for("main.entry_view", entry_id=e.id))

# -------------------- Media: upload file or add link --------------------

@main_bp.post("/exercise/<int:entry_id>/media/upload")
@login_required
def media_upload(entry_id:int):
    e = ExerciseEntry.query.get_or_404(entry_id)

    file = request.files.get("file")
    if not file or not file.filename:
        flash("No file selected", "error")
        return redirect(url_for("main.entry_view", entry_id=entry_id))

    # Keep original extension
    ext = Path(file.filename).suffix.lower()[:10]
    safe_ext = ext if ext and all(c.isalnum() or c == "." for c in ext) else ""

    # Unique filename
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    fname = f"entry{entry_id}_{ts}_{os.urandom(4).hex()}{safe_ext}"

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, fname)
    file.save(file_path)

    m = Media(entry_id=entry_id, kind="file", url=f"/media/{fname}", original_name=file.filename)
    db.session.add(m)
    db.session.commit()
    flash("Uploaded", "ok")
    return redirect(url_for("main.entry_view", entry_id=entry_id))

@main_bp.post("/exercise/<int:entry_id>/media/link")
@login_required
def media_link(entry_id:int):
    e = ExerciseEntry.query.get_or_404(entry_id)
    url = request.form.get("url","").strip()
    if not is_safe_external_url(url):
        flash("Paste a valid http(s) link", "error")
        return redirect(url_for("main.entry_view", entry_id=entry_id))
    m = Media(entry_id=entry_id, kind="link", url=url)
    db.session.add(m)
    db.session.commit()
    flash("Link added", "ok")
    return redirect(url_for("main.entry_view", entry_id=entry_id))

@main_bp.post("/media/<int:media_id>/delete")
@login_required
def media_delete(media_id:int):
    m = Media.query.get_or_404(media_id)
    entry_id = m.entry_id

    if current_user.role != "coach":
        flash("Coach account required to delete media.", "error")
        return redirect(url_for("main.entry_view", entry_id=entry_id))

    if m.kind == "file" and m.url.startswith("/media/"):
        fname = m.url.replace("/media/","",1)
        fpath = os.path.join(current_app.config["UPLOAD_FOLDER"], fname)
        try:
            os.remove(fpath)
        except FileNotFoundError:
            pass

    db.session.delete(m)
    db.session.commit()
    flash("Deleted", "ok")
    return redirect(url_for("main.entry_view", entry_id=entry_id))

@main_bp.get("/media/<path:filename>")
@login_required
def media_serve(filename: str):
    # Serve uploaded files from instance/uploads
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=False)
