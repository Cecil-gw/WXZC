import requests, os
from dotenv import load_dotenv
load_dotenv()
url = os.getenv("BASE_URL") + "/chat/completions"
headers = {"Authorization": f"Bearer {os.getenv('API_KEY')}", "Content-Type": "application/json"}
data = {"model": "doubao-seed-2.0-code", "messages": [{"role":"user","content":"hi"}]}
print(requests.post(url, headers=headers, json=data).json())