from flask import request, jsonify
import jwt
from functools import wraps
from datetime import datetime, timedelta

SECRET_KEY = "123456"
TOKEN_EXPIRE = timedelta(hours=2)

# 新增注册函数
def register_routes(app,db):


    def admin_required(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"code":403, "message":"未登录"}),403
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                if payload.get("role") != "admin":
                    return jsonify({"code":403, "message":"权限不足"}),403
            except Exception:
                return jsonify({"code":403,"message":"Token非法或过期"}),403
            return f(*args, **kwargs)
        return wrapper
    
    @app.route('/login',methods=["POST"])
    def login():
        username="admin"
        role= "admin"
        password="admin123"

        data = request.get_json()
        if data['username'] == username and data['password'] == password:
            payload={
              "username":username,
              "role":role,
              "exp": datetime.utcnow() + TOKEN_EXPIRE,
            }
            token= jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            return jsonify({
              'code':200,
              'message':'登录成功',
              "data":{"token":token}
            })
        else:
            return jsonify({
              'code':401,
              'message':'用户名或密码错误'
            }),401

    @admin_required
    @app.route('/admin/news',methods=["POST"])
    def post_news():
        data = request.get_json()
        title = data.get("title")
        content = data.get("content")
        category = data.get("category")

        if not all([title,content,category]):
          return jsonify({"code":400,"message":"title、content、category不能为空"}),400
        if title and content and category:
          db.append({
            "id":len(db)+1,
            "title":title,
            "content":content,
            "category":category
          })

        return jsonify({
          'code':200,
          'message':'发布成功',
          "data":{"title":title,"content":content,"category":category}
        })

    @admin_required
    @app.route('/admin/news/<int:id>',methods=["DELETE"])
    def delete_news(id):
      for item in db:
        if item.get("id") == id:
            db.remove(item)
            return jsonify({
                "code":200,
                "message":f"成功删除id={id}的新闻"
            })
      return jsonify({
          "code":404,
          "message":"找不到该新闻"
      }),404
          