"""调试：捕获完整错误堆栈。"""
import traceback, sys

from app import create_app

app = create_app()

with app.test_client() as c:
    # 登录
    print("=== 登录 ===")
    r = c.post('/api/v1/auth/login', json={'username':'admin','password':'admin123'})
    print(r.status_code, r.get_json())

    # 提取 token
    data = r.get_json()
    token = data['data']['access_token']
    h = {'Authorization': f'Bearer {token}'}

    # 依次测试每个 API
    tests = [
        ('GET', '/api/v1/auth/me', None),
        ('GET', '/api/v1/data/customers', None),
        ('GET', '/api/v1/data/statistics', None),
        ('GET', '/api/v1/data/quality', None),
        ('GET', '/api/v1/data/visualization/gender', None),
        ('GET', '/api/v1/model/experiments', None),
        ('GET', '/api/v1/model/best', None),
        ('GET', '/api/v1/logs', None),
        ('GET', '/api/v1/email/targets', None),
        ('GET', '/api/v1/email/prompt', None),
        ('GET', '/api/v1/email/records', None),
    ]

    for method, path, body in tests:
        print(f"\n=== {method} {path} ===")
        try:
            if method == 'GET':
                r = c.get(path, headers=h)
            print(f"Status: {r.status_code}")
            resp = r.get_json()
            print(f"Code: {resp.get('code')}, Msg: {resp.get('message')}")
            if resp.get('code') != 0:
                print(f"  -> 非0返回")
        except Exception as e:
            print(f"ERROR: {e}")
            traceback.print_exc()
    
    # 测试静态文件
    print("\n=== 静态文件 ===")
    for f in ['/', '/static/index.html', '/favicon.ico']:
        r = c.get(f)
        print(f"{f} -> {r.status_code}")