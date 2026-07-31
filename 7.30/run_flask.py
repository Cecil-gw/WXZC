"""项目启动入口。

使用方式：`python run_flask.py`，默认监听 0.0.0.0:5000，debug=True 热重载。
"""
from app import create_app
from app.core.config import settings

app = create_app()

if __name__ == "__main__":
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG,
    )
