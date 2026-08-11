import os
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.retrievers import BM25Retriever
from dotenv import load_dotenv

load_dotenv(r"D:\wx26.7.14\8.11\.env",override=True)

# ===================== 配置 =====================
api_key = os.getenv("API_KEY")
base_url = os.getenv("BA,SE_URL")
model_name = os.getenv("MODEL_NAME")

#调试
print(f"[DEBUG] api_key: {api_key[:10]}***")
print(f"[DEBUG] base_url: {base_url}")
print(f"[DEBUG] model_name: {model_name}")
