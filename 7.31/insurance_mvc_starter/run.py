from app import create_app

app = create_app()

if __name__ == "__main__":
    # debug=True: 代码修改自动重载 + 报错时浏览器显示调试信息
    # host="0.0.0.0": 允许局域网访问（教学时学生可以手机连）
    app.run(host="0.0.0.0", port=5000, debug=True)