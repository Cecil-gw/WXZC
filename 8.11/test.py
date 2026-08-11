import os
from dotenv import load_dotenv
import time

t0 = time.time()
load_dotenv(r"D:\wx26.7.14\8.11\.env",override=True)
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

print(f"[DEBUG] api_key: {api_key[:10]}***")
print(f"[DEBUG] base_url: {base_url}")
print(f"[DEBUG] model_name: {model_name}")
print(f"耗时：{time.time()-t0:.2f} s")