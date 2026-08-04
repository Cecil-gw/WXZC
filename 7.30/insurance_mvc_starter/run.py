"""MVC 教学骨架入口。

使用方式：cd insurance_mvc_starter && python run.py
默认监听 0.0.0.0:5001。
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
