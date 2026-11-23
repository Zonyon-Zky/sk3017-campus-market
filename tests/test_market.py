
from io import BytesIO

from conftest import PNG_BYTES, db_connection, login


def test_home_lists_ten_products_and_pagination(client):
    response = client.get("/")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "共 24 件" in text
    assert text.count('class="product-card"') == 10
    assert "下一页" in text


def test_search_handles_literal_percent_and_quote(client):
    percent = client.get("/", query_string={"q": "%"})
    assert percent.status_code == 200
    assert "100%全新" in percent.get_data(as_text=True)
    assert "共 1 件" in percent.get_data(as_text=True)

    quote = client.get("/", query_string={"q": "'"})
    assert quote.status_code == 200
    assert "O&#39;Reilly" in quote.get_data(as_text=True)


def test_invalid_pagination_and_filters_rejected(client):
    assert client.get("/?page=abc").status_code == 400
    assert client.get("/?page=0").status_code == 400
    assert client.get("/?category_id=abc").status_code == 400
    assert client.get("/?q=" + "a" * 51).status_code == 400


def test_register_login_logout(client, app):
    response = client.post("/auth/register", data={
        "username": "new_user", "nickname": "新同学", "password": "123456"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "新同学" in response.get_data(as_text=True)
    client.get("/auth/logout")
    assert client.get("/publish").status_code == 302


def test_publish_requires_login_and_valid_images(client, app):
    assert client.get("/publish").status_code == 302
    login(client, "buyer")
    no_image = client.post("/publish", data={
        "category_id": "1", "title": "无图商品", "description": "测试", "price": "10.00"
    })
    assert no_image.status_code == 400
    assert "上传" in no_image.get_data(as_text=True)

    too_large = client.post("/publish", data={
        "category_id": "1", "title": "超大图片", "description": "测试", "price": "10.00",
        "images": (BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * (2 * 1024 * 1024)), "large.png"),
    }, content_type="multipart/form-data")
    assert too_large.status_code == 400
    assert "2MB" in too_large.get_data(as_text=True)

    wrong_format = client.post("/publish", data={
        "category_id": "1", "title": "错误格式", "description": "测试", "price": "10.00",
        "images": (BytesIO(b"hello"), "note.txt"),
    }, content_type="multipart/form-data")
    assert wrong_format.status_code == 400
    assert "仅支持" in wrong_format.get_data(as_text=True)


def test_publish_success_saves_product_and_images(app, client, tmp_path):
    login(client, "buyer")
    response = client.post("/publish", data={
        "category_id": "1",
        "title": "TDD 测试商品",
        "description": "通过测试先行的方式发布。",
        "price": "12.50",
        "images": [(BytesIO(PNG_BYTES), "one.png"), (BytesIO(PNG_BYTES), "two.png")],
    }, content_type="multipart/form-data")
    assert response.status_code == 302
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM products WHERE title=%s", ("TDD 测试商品",))
            product = cursor.fetchone()
            cursor.execute("SELECT path FROM product_images WHERE product_id=%s ORDER BY sort", (product["id"],))
            images = cursor.fetchall()
    assert len(images) == 2
    assert all((tmp_path / "uploads" / image["path"].split("/")[-1]).exists() for image in images)


def test_favorite_duplicate_is_friendly(client):
    login(client, "buyer")
    first = client.post("/products/1/favorite", follow_redirects=True)
    second = client.post("/products/1/favorite", follow_redirects=True)
    assert first.status_code == 200 and second.status_code == 200
    assert "已经收藏" in second.get_data(as_text=True)
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM favorites WHERE user_id=2 AND product_id=1")
            assert cursor.fetchone()["total"] == 1


def test_message_and_seller_reply_permissions(app):
    buyer = app.test_client(); login(buyer, "buyer")
    response = buyer.post("/products/1/messages", data={"content": "可以今天面交吗？"}, follow_redirects=True)
    assert response.status_code == 200
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM messages WHERE product_id=1 AND content=%s", ("可以今天面交吗？",))
            message_id = cursor.fetchone()["id"]

    demo = app.test_client(); login(demo, "demo")
    reply = demo.post(f"/messages/{message_id}/reply", data={"content": "可以，晚上七点。"}, follow_redirects=True)
    assert reply.status_code == 200
    assert "晚上七点" in reply.get_data(as_text=True)

    denied = buyer.post(f"/messages/{message_id}/reply", data={"content": "非卖家回复"})
    assert denied.status_code == 403


def test_only_owner_can_change_status_and_delete(app):
    buyer = app.test_client(); login(buyer, "buyer")
    assert buyer.post("/products/1/status", data={"status": "sold"}).status_code == 403
    assert buyer.post("/products/1/delete").status_code == 403

    demo = app.test_client(); login(demo, "demo")
    changed = demo.post("/products/1/status", data={"status": "sold"}, follow_redirects=True)
    assert changed.status_code == 200
    assert "已售" in changed.get_data(as_text=True)
    deleted = demo.post("/products/1/delete", follow_redirects=True)
    assert deleted.status_code == 200
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM products WHERE id=1")
            assert cursor.fetchone()["total"] == 0


def test_profile_tabs_show_published_favorites_and_messages(app):
    demo = app.test_client(); login(demo, "demo")
    published = demo.get("/profile?tab=published").get_data(as_text=True)
    assert "高等数学教材" in published
    messages = demo.get("/profile?tab=messages").get_data(as_text=True)
    assert "教材还有吗" in messages

    buyer = app.test_client(); login(buyer, "buyer")
    favorites = buyer.get("/profile?tab=favorites").get_data(as_text=True)
    assert "高等数学教材" in favorites
