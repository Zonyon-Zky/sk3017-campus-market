from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapped


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT id,username,password,nickname FROM users WHERE username=%s", (username,))
            user = cur.fetchone()
        if not user or not check_password_hash(user["password"], password):
            flash("用户名或密码错误", "error")
        else:
            session.clear()
            session.update(user_id=user["id"], username=user["username"], nickname=user["nickname"])
            target = request.args.get("next") or url_for("market.index")
            if not target.startswith("/"):
                target = url_for("market.index")
            return redirect(target)
    return render_template("login.html")


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        nickname = request.form.get("nickname", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(username) > 20:
            flash("用户名长度应为3-20位", "error")
        elif not nickname or len(nickname) > 30:
            flash("昵称不能为空且不超过30位", "error")
        elif len(password) < 6:
            flash("密码至少6位", "error")
        else:
            db = get_db()
            try:
                with db.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users(username,password,nickname) VALUES(%s,%s,%s)",
                        (username, generate_password_hash(password), nickname),
                    )
                    user_id = cur.lastrowid
                db.commit()
                session.clear()
                session.update(user_id=user_id, username=username, nickname=nickname)
                return redirect(url_for("market.index"))
            except Exception as exc:
                db.rollback()
                if getattr(exc, "args", [None])[0] == 1062:
                    flash("用户名已存在", "error")
                else:
                    raise
    return render_template("register.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("market.index"))
