from flask import request, jsonify

introduce = "本公司专注企业数字化信息服务，深耕行业多年，坚持以技术赋能业务，以诚信立足市场。公司汇聚专业运营与技术团队，面向客户提供资讯发布、信息公示、公告推送等综合服务。我们秉持务实创新、客户至上的经营理念，持续优化内容管理体系，搭建高效透明的信息传播渠道。未来公司将不断拓展业务边界，完善服务能力，力求为合作伙伴创造长期稳定价值，携手共同发展。"

# 路由注册函数：接收app实例、新闻数据库列表db
def get_main(app, db):
    # 首页接口：简介 + 最新3条新闻
    @app.route('/', methods=['GET'])
    def main_show():
        # 切片取最后3条新闻
        latest_news = db[-3:]
        resp = {
            'code': 200,
            'message': 'success',
            'data': {
                "introduce": introduce,
                "latest_news": latest_news
            }
        }
        return jsonify(resp)

    # 获取全部新闻接口
    @app.route('/api/news', methods=['GET'])
    def news_show():
        # 反转：最新新闻放前面
        news_list = db[::-1]
        resp = {
            'code': 200,
            'message': 'news_success',
            'data': {
                'news': news_list
            }
        }
        return jsonify(resp)

    # 根据id查询单条新闻【推荐正确写法：遍历匹配id】
    @app.route('/api/news/<id>', methods=['GET'])
    def news_detail(id):
        for news in db:
            # 统一转为字符串比较，防止类型不一致
            if str(news.get("id")) == str(id):
                return jsonify({
                    'code': 200,
                    'message': 'news_detail_success',
                    'data': {'news': news}
                })
        # 循环结束没找到，返回404
        return jsonify({"code": 404, "message": "找不到该新闻"}), 404