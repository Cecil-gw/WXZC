from flask import Flask

app = Flask(__name__)
databases_db = []
introduce=""

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    import front
    import back_env
    
    front.get_main(app, databases_db)
    back_env.register_routes(app, databases_db)    
    print(app.url_map)
    app.run(debug=True,port=5005, use_reloader=False)