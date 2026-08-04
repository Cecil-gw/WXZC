#!/usr/bin/env python3
"""保险精准营销系统 - 启动入口。"""

from app import create_app

if __name__ == "__main__":
    app = create_app()
    import logging
    logging.basicConfig(level=logging.DEBUG)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
