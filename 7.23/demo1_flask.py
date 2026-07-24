from flask import Flask, request, jsonify

app = Flask(__name__)

# 模拟数据库
users_db = []

# 请求JSON参考格式
"""
{
  "username": "张三",
  "password": "123456",
  "cookie": "xxxxx"
}
"""

# 1. 注册接口 POST /api/register
@app.route("/api/register", methods=["POST"])
def register():
    # 获取前端发送的json数据
    req_data = request.get_json()
    # 修正后的参数校验
    if not req_data or "username" not in req_data or "password" not in req_data:
        return jsonify({
            "code": 400,
            "msg": "缺少username或者password参数",
            "data": None
        })
    username = req_data["username"]
    password = req_data["password"]
    # 同时存入用户名+密码
    users_db.append({"username": username, "password": password})
    
    return jsonify({
        "code": 200,
        "msg": "注册成功",
        "data": {"username": username, "password": password}
    })

# 2. 获取用户列表 GET /api/users?page=1&limit=5
@app.route("/api/users", methods=["GET"])
def get_users():
    # 打印完整访问地址到控制台
    print("完整访问URL：", request.url)
    print("路由路径path：", request.path)

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 5))
    
    start = (page - 1) * limit
    end = start + limit
    page_data = users_db[start:end]

    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": {
            "list": page_data,
            "total": len(users_db),
            "page": page,
            "limit": limit,
            "visit_url": request.url  # 直接把URL返回给Postman查看
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)