from flask import Flask, render_template

from .config import Config
from .db import init_app as init_db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    init_db(app)

    from .auth import bp as auth_bp
    from .market import bp as market_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(market_bp)

    @app.errorhandler(400)
    def bad_request(_error):
        return render_template("error.html", code=400, message="请求参数不正确"), 400

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, message="没有权限执行此操作"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="页面或商品不存在"), 404

    @app.errorhandler(413)
    def too_large(_error):
        return render_template("error.html", code=413, message="上传内容超过大小限制"), 413

    @app.errorhandler(500)
    def server_error(_error):
        return render_template("error.html", code=500, message="服务器内部错误"), 500

    return app
