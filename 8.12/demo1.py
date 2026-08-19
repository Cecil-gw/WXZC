import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# .env 和 demo1.py 在同一个目录
env_path = Path(__file__).resolve().parent / ".env"

print(".env 路径：", env_path)
print(".env 是否存在：", env_path.exists())

load_dotenv(env_path)

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")

print("API Key 是否读取成功：", bool(api_key))
print("API Key 长度：", len(api_key) if api_key else 0)
print("Base URL：", base_url)

if not api_key:
    raise RuntimeError("没有读取到 OPENAI_API_KEY")

if not base_url:
    raise RuntimeError("没有读取到 OPENAI_BASE_URL")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

response = client.chat.completions.create(
    model="MiniMax-M2.5",
    messages=[
        {
            "role": "user",
            "content": "你好，请介绍一下你自己"
        }
    ]
)

print("模型回复：")
print(response.choices[0].message.content)