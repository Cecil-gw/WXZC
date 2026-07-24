# 用户登录与注册接口

from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)
app.json.ensure_ascii = False 
# 配置会话密钥
app.secret_key = secrets.token_hex(16)

#模拟数据库
users_db = {}

@app.route("/auth/register", methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"code": 400, "msg": "请提供 username 和 password"}), 400
    
    username = data['username']
    password = data['password']
    
    if username in users_db:
        return jsonify({"code": 400, "msg": "用户名已存在"}), 400
    
    # 核心安全操作：对密码进行哈希加盐存储
    password_hash = generate_password_hash(password)
    users_db[username] = {
        "password_hash": password_hash,
        "role": "user",
        "status": "active"
    }
    return jsonify({"code": 200, "msg": "注册成功"})


@app.route("/auth/login", methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"code": 400, "msg": "请提供 username 和 password"}), 400
    
    username = data['username']
    password = data['password']
    
    if username not in users_db:
        return jsonify({"code": 401, "msg": "用户名不存在"}), 401
    
    #核心验证：对比铭文密码与存储的哈希值是否一致
    if not check_password_hash(users_db[username]["password_hash"], password):
        return jsonify({"code": 401, "msg": "密码错误"}), 401    
    # 登录成功，设置会话，将用户名和其他相关信息存入session
    session["username"] = username
    session["role"] = users_db[username]["role"]
    return jsonify({"code": 200, "msg": "登录成功", "username": username, "role": session["role"]})
    
    

@app.route("/auth/profile")
def profile():
    if "username"==None:
        return jsonify({"code": 401, "msg": "未登录"}), 401
    return jsonify({"code": 200, "msg": "用户信息", "username": session["username"], "role": session["role"]})

@app.route("/auth/logout")
def logout():
    session.pop("username", None)
    session.pop("role", None)
    return jsonify({"code": 200, "msg": "退出登录成功"})


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5003, debug=True)
