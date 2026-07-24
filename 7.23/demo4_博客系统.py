from flask import Flask, request, jsonify, session
from datetime import datetime
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.json.ensure_ascii = False 

# 模拟数据库
posts_db = {}
next_id = 1

#登录
@app.route('/login', methods=['POST'])
def login_temp():

    session['username'] = 'admin'
    session['role'] = 'user'
    return jsonify({"code": 200, "msg": "临时登录成功(user:admin)"})

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"code": 401, "msg": "请先登录"}), 401
        return f(*args, **kwargs)
    return decorated

#发布新博客
@app.route('/api/posts', methods=['POST'])
@login_required
def create_post():
    global next_id
    data = request.get_json()
    if not data.get('title') or not data.get('content'):
        return jsonify({"code": 400, "msg": "标题和内容不能为空"}), 400

    post = {
        "id": next_id,
        "title": data['title'],
        "content": data['content'],
        "author": session['username'],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "likes": 0,
        "liked_by": [], # 记录点赞用户，防止重复点赞
        "comments": []  # 记录评论

    }
    posts_db[next_id] = post
    next_id += 1 #手动自增
    return jsonify({"code": 200, "msg": "日志发布成功", "data": post}), 201


#获取博客列表
@app.route('/api/posts', methods=['GET'])
@login_required
def list_posts():
    sorted_posts = sorted(posts_db.values(), key=lambda x: x['id'], reverse=True)
    return jsonify({"code": 200, "data": sorted_posts})


#获取单篇博客详情
@app.route('/api/posts/<int:post_id>', methods=['GET'])
@login_required
def get_post(post_id):
    if post_id not in posts_db:
        return jsonify({"code": 404, "msg": "博客不存在"}), 404
    return jsonify({"code": 200, "data": posts_db[post_id]})


#点赞博客
@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    #判断博客是否存在 post_id
    if post_id not in posts_db:
        return jsonify({"code": 404, "msg": "博客不存在"}), 404   
    
    #判断用户是否已点赞
    post = posts_db[post_id]
    current_user = session['username']
    if current_user in post['liked_by']:
        return jsonify({"code": 400, "msg": "您已经点赞过该博客了", "likes": post['likes']}), 400   

    #增加点赞数
    post['likes'] += 1
    post['liked_by'].append(current_user)
    return jsonify({"code": 200, "msg": "点赞成功", "likes": post['likes']})

#发表评论
@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
def comment_post(post_id):
    if post_id not in posts_db:
        return jsonify({"code": 404, "msg": "博客不存在"}), 404

    data = request.get_json()
    if not data.get('content'):
        return jsonify({"code": 400, "msg": "评论内容不能为空"}), 400

    comment = {
        "author": session['username'],
        "content": data['content'],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    posts_db[post_id]['comments'].append(comment)
    return jsonify({"code": 200, "msg": "评论成功", "data": comment})



#测试入口
if __name__ == '__main__':
    app.run(debug=True, port=5004)