
import math
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template,
    request, session, url_for,
)

from .auth import login_required
from .db import get_db

bp = Blueprint("market", __name__)
PAGE_SIZE = 10
STATUS_LABELS = {"on_sale": "在售", "sold": "已售", "offline": "已下架"}


def positive_int(value, default=None):
    if value in (None, ""):
        return default
    if not str(value).isdigit() or int(value) < 1:
        abort(400)
    return int(value)


def page_number(value):
    if value in (None, ""):
        return 1
    if not str(value).isdigit() or int(value) < 1:
        abort(400)
    return int(value)


def like_value(keyword):
    # Use '=' as the SQL LIKE escape char so MySQL backslash settings do not matter.
    escaped = keyword.replace("=", "==").replace("%", "=%").replace("_", "=_")
    return f"%{escaped}%"


def product_row(cursor, product_id):
    cursor.execute(
        """
        SELECT p.*,c.name AS category_name,u.nickname AS seller_name,u.phone AS seller_phone
        FROM products p
        JOIN categories c ON c.id=p.category_id
        JOIN users u ON u.id=p.seller_id
        WHERE p.id=%s
        """,
        (product_id,),
    )
    return cursor.fetchone()


@bp.route("/")
def index():
    page = page_number(request.args.get("page"))
    category_id = positive_int(request.args.get("category_id"))
    keyword = request.args.get("q", "").strip()
    if len(keyword) > 50:
        abort(400)

    where = ["1=1"]
    params = []
    if category_id:
        where.append("p.category_id=%s")
        params.append(category_id)
    if keyword:
        pattern = like_value(keyword)
        where.append("(p.title LIKE %s ESCAPE '=' OR p.description LIKE %s ESCAPE '=')")
        params.extend([pattern, pattern])
    clause = " AND ".join(where)

    db = get_db()
    with db.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS total FROM products p WHERE {clause}", params)
        total = cur.fetchone()["total"]
        pages = max(1, math.ceil(total / PAGE_SIZE))
        offset = (page - 1) * PAGE_SIZE
        cur.execute(
            f"""
            SELECT p.*,c.name AS category_name,u.nickname AS seller_name,
                   (SELECT pi.path FROM product_images pi
                    WHERE pi.product_id=p.id ORDER BY pi.sort,pi.id LIMIT 1) AS cover
            FROM products p
            JOIN categories c ON c.id=p.category_id
            JOIN users u ON u.id=p.seller_id
            WHERE {clause}
            ORDER BY p.created_at DESC,p.id DESC
            LIMIT %s OFFSET %s
            """,
            params + [PAGE_SIZE, offset],
        )
        products = cur.fetchall()
        cur.execute("SELECT c.*,COUNT(p.id) AS product_count FROM categories c LEFT JOIN products p ON p.category_id=c.id GROUP BY c.id,c.name,c.sort ORDER BY c.sort")
        categories = cur.fetchall()

    return render_template(
        "index.html", products=products, categories=categories,
        total=total, page=page, pages=pages, q=keyword, category_id=category_id,
        status_labels=STATUS_LABELS,
    )


@bp.route("/products/<int:product_id>")
def detail(product_id):
    db = get_db()
    with db.cursor() as cur:
        product = product_row(cur, product_id)
        if not product:
            abort(404)
        cur.execute("SELECT * FROM product_images WHERE product_id=%s ORDER BY sort,id", (product_id,))
        images = cur.fetchall()
        cur.execute("SELECT COUNT(*) AS total FROM favorites WHERE product_id=%s", (product_id,))
        favorite_count = cur.fetchone()["total"]
        is_favorite = False
        if session.get("user_id"):
            cur.execute("SELECT id FROM favorites WHERE user_id=%s AND product_id=%s",
                        (session["user_id"], product_id))
            is_favorite = cur.fetchone() is not None
        cur.execute(
            """
            SELECT m.*,u.nickname FROM messages m JOIN users u ON u.id=m.user_id
            WHERE m.product_id=%s ORDER BY m.created_at,m.id
            """,
            (product_id,),
        )
        rows = cur.fetchall()

    threads = [row for row in rows if row["parent_id"] is None]
    replies = {}
    for row in rows:
        if row["parent_id"] is not None:
            replies.setdefault(row["parent_id"], []).append(row)

    return render_template(
        "detail.html", product=product, images=images, favorite_count=favorite_count,
        is_favorite=is_favorite, threads=threads, replies=replies,
        status_labels=STATUS_LABELS, is_seller=session.get("user_id") == product["seller_id"],
    )


@bp.route("/products/<int:product_id>/favorite", methods=["POST"])
@login_required
def favorite(product_id):
    db = get_db()
    with db.cursor() as cur:
        if not product_row(cur, product_id):
            abort(404)
        cur.execute("SELECT id FROM favorites WHERE user_id=%s AND product_id=%s",
                    (session["user_id"], product_id))
        if cur.fetchone():
            flash("已经收藏过该商品", "info")
        else:
            cur.execute("INSERT INTO favorites(user_id,product_id) VALUES(%s,%s)",
                        (session["user_id"], product_id))
            db.commit()
            flash("收藏成功", "success")
    return redirect(url_for("market.detail", product_id=product_id))


@bp.route("/products/<int:product_id>/messages", methods=["POST"])
@login_required
def add_message(product_id):
    content = request.form.get("content", "").strip()
    if not content or len(content) > 500:
        flash("留言内容应为1-500个字符", "error")
        return redirect(url_for("market.detail", product_id=product_id))
    db = get_db()
    with db.cursor() as cur:
        if not product_row(cur, product_id):
            abort(404)
        cur.execute("INSERT INTO messages(product_id,user_id,content) VALUES(%s,%s,%s)",
                    (product_id, session["user_id"], content))
    db.commit()
    flash("留言已发布", "success")
    return redirect(url_for("market.detail", product_id=product_id))


@bp.route("/messages/<int:message_id>/reply", methods=["POST"])
@login_required
def reply_message(message_id):
    content = request.form.get("content", "").strip()
    if not content or len(content) > 500:
        flash("回复内容应为1-500个字符", "error")
        return redirect(request.referrer or url_for("market.index"))
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT m.id,m.product_id,p.seller_id
            FROM messages m JOIN products p ON p.id=m.product_id
            WHERE m.id=%s
            """,
            (message_id,),
        )
        message = cur.fetchone()
        if not message:
            abort(404)
        if message["seller_id"] != session["user_id"]:
            abort(403)
        cur.execute(
            "INSERT INTO messages(product_id,user_id,parent_id,content) VALUES(%s,%s,%s,%s)",
            (message["product_id"], session["user_id"], message_id, content),
        )
    db.commit()
    flash("回复已发布", "success")
    return redirect(url_for("market.detail", product_id=message["product_id"]))


def validate_price(value):
    try:
        price = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    if not price.is_finite() or price <= 0 or price.as_tuple().exponent < -2:
        return None
    return price.quantize(Decimal("0.01"))


def validate_images(files):
    files = [f for f in files if f and f.filename]
    if not files:
        return None, "请上传 1-3 张商品图片"
    if len(files) > 3:
        return None, "最多上传 3 张图片"
    valid = []
    for file in files:
        filename = file.filename.lower()
        ext = Path(filename).suffix
        if ext not in {".jpg", ".jpeg", ".png"}:
            return None, "仅支持 JPG、JPEG、PNG 格式"
        data = file.read(current_app.config["MAX_IMAGE_BYTES"] + 1)
        if len(data) > current_app.config["MAX_IMAGE_BYTES"]:
            return None, "单张图片不能超过 2MB"
        if ext == ".png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
            return None, "PNG 图片格式不正确"
        if ext in {".jpg", ".jpeg"} and not data.startswith(b"\xff\xd8\xff"):
            return None, "JPG 图片格式不正确"
        valid.append((data, "png" if ext == ".png" else "jpg"))
    return valid, None


@bp.route("/publish", methods=["GET", "POST"])
@login_required
def publish():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM categories ORDER BY sort")
        categories = cur.fetchall()

    if request.method == "GET":
        return render_template("publish.html", categories=categories, form={})

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    price = validate_price(request.form.get("price", ""))
    category_id = positive_int(request.form.get("category_id"))
    images, image_error = validate_images(request.files.getlist("images"))

    error = image_error
    if not title or len(title) > 100:
        error = "标题应为1-100个字符"
    elif not description or len(description) > 1000:
        error = "描述应为1-1000个字符"
    elif price is None:
        error = "价格必须大于0且最多两位小数"
    elif not category_id:
        error = "请选择商品分类"
    elif error is None:
        with db.cursor() as cur:
            cur.execute("SELECT id FROM categories WHERE id=%s", (category_id,))
            if not cur.fetchone():
                error = "商品分类不存在"

    if error:
        return render_template("publish.html", categories=categories, form=request.form, error=error), 400

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_paths = []
    for data, ext in images:
        filename = f"{uuid.uuid4().hex}.{ext}"
        (upload_dir / filename).write_bytes(data)
        saved_paths.append(f"uploads/{filename}")

    try:
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO products(seller_id,category_id,title,description,price) VALUES(%s,%s,%s,%s,%s)",
                (session["user_id"], category_id, title, description, price),
            )
            product_id = cur.lastrowid
            for sort, path in enumerate(saved_paths):
                cur.execute("INSERT INTO product_images(product_id,path,sort) VALUES(%s,%s,%s)",
                            (product_id, path, sort))
        db.commit()
    except Exception:
        db.rollback()
        for path in saved_paths:
            (upload_dir / Path(path).name).unlink(missing_ok=True)
        raise

    flash("商品发布成功", "success")
    return redirect(url_for("market.detail", product_id=product_id))


@bp.route("/products/<int:product_id>/status", methods=["POST"])
@login_required
def update_status(product_id):
    status = request.form.get("status")
    if status not in STATUS_LABELS:
        abort(400)
    db = get_db()
    with db.cursor() as cur:
        product = product_row(cur, product_id)
        if not product:
            abort(404)
        if product["seller_id"] != session["user_id"]:
            abort(403)
        cur.execute("UPDATE products SET status=%s WHERE id=%s", (status, product_id))
    db.commit()
    flash("商品状态已更新", "success")
    return redirect(url_for("market.detail", product_id=product_id))


@bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    db = get_db()
    with db.cursor() as cur:
        product = product_row(cur, product_id)
        if not product:
            abort(404)
        if product["seller_id"] != session["user_id"]:
            abort(403)
        cur.execute("SELECT path FROM product_images WHERE product_id=%s", (product_id,))
        paths = [row["path"] for row in cur.fetchall()]
        cur.execute("DELETE FROM products WHERE id=%s", (product_id,))
    db.commit()
    for path in paths:
        if path.startswith("uploads/"):
            (Path(current_app.static_folder) / path).unlink(missing_ok=True)
    flash("商品已删除", "success")
    return redirect(url_for("market.profile", tab="published"))


@bp.route("/profile")
@login_required
def profile():
    tab = request.args.get("tab", "published")
    if tab not in {"published", "favorites", "messages"}:
        abort(400)
    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            """
            SELECT p.*,c.name AS category_name,
                   (SELECT path FROM product_images WHERE product_id=p.id ORDER BY sort,id LIMIT 1) AS cover
            FROM products p JOIN categories c ON c.id=p.category_id
            WHERE p.seller_id=%s ORDER BY p.created_at DESC
            """,
            (session["user_id"],),
        )
        published = cur.fetchall()
        cur.execute(
            """
            SELECT p.*,c.name AS category_name,
                   (SELECT path FROM product_images WHERE product_id=p.id ORDER BY sort,id LIMIT 1) AS cover
            FROM favorites f JOIN products p ON p.id=f.product_id
            JOIN categories c ON c.id=p.category_id
            WHERE f.user_id=%s ORDER BY f.created_at DESC
            """,
            (session["user_id"],),
        )
        favorites = cur.fetchall()
        cur.execute(
            """
            SELECT m.*,p.title AS product_title,u.nickname AS author,
                   (SELECT COUNT(*) FROM messages r WHERE r.parent_id=m.id) AS reply_count
            FROM messages m JOIN products p ON p.id=m.product_id JOIN users u ON u.id=m.user_id
            WHERE p.seller_id=%s AND m.parent_id IS NULL AND m.user_id<>%s
            ORDER BY m.created_at DESC
            """,
            (session["user_id"], session["user_id"]),
        )
        received_messages = cur.fetchall()
    return render_template(
        "profile.html", tab=tab, published=published, favorites=favorites,
        received_messages=received_messages, status_labels=STATUS_LABELS,
    )
