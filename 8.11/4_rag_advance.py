import os
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from dotenv import load_dotenv

# 填你的.env完整绝对路径
env_path = r"D:\wx26.7.14\8.11\.env"
load_dotenv(dotenv_path=env_path, override=True)

# ===================== 配置 =====================
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

print(f"[DEBUG] api_key: {api_key[:10]}***")
print(f"[DEBUG] base_url: {base_url}")
print(f"[DEBUG] model_name: {model_name}")

# ---------- 混合检索模式选择 ----------
# 可选值: "weighted"（加权融合） 或 "rrf"（倒数排名融合）
HYBRID_MODE = "rrf"          # 当前使用 RRF 融合
# HYBRID_MODE = "weighted"   # 若想切换，请取消这行注释并注释上一行

# 加权融合权重
VECTOR_WEIGHT = 0.6
BM25_WEIGHT = 0.4

# 通用参数
TOP_K = 8                   # 两路粗排各召回条数
FINAL_TOP_K = 5             # 融合后送入精排的候选数
RERANK_TOP_K = 2            # 精排后最终返回给LLM的条数
RRF_K = 60                  # RRF 平滑常数

# 模型与向量库路径
local_embed_path = r"D:\wx26.7.14\bge-large-zh"
local_rerank_path = r"D:\wx26.7.14\bge-reranker-v2-m3"
CHROMA_PERSIST_DIR = r"D:\wx26.7.14\8.10\homework\chroma_huawei"

# ===================== 本地重排序器 =====================
class LocalReranker:
    def __init__(self, model_path):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    def rank(self, query, docs):
        pairs = [[query, doc.page_content] for doc in docs]
        with torch.no_grad():
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512
            )
            scores = self.model(**inputs, return_dict=True).logits.view(-1).float()
            scores = scores.tolist()
        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked]

reranker = LocalReranker(local_rerank_path)

# ===================== 工具函数 =====================
def get_all_docs(vectorstore):
    data = vectorstore.get(include=["documents", "metadatas"])
    return [Document(page_content=d, metadata=m if m else {}) for d, m in zip(data["documents"], data["metadatas"])]

def format_docs(docs):
    return "\n".join(x.page_content for x in docs)

# ===================== 方式一：加权融合 =====================
def weighted_fusion(query, vectorstore):
    all_docs = get_all_docs(vectorstore)

    # BM25 粗排
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = TOP_K
    bm25_docs = bm25_retriever.invoke(query)

    # 向量粗排
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    vector_docs = vector_retriever.invoke(query)

    # 分数加权
    bm25_scores = {d.page_content: (TOP_K - i) * BM25_WEIGHT for i, d in enumerate(bm25_docs)}
    vector_scores = {d.page_content: (TOP_K - i) * VECTOR_WEIGHT for i, d in enumerate(vector_docs)}

    all_docs_dict = {}
    for doc in bm25_docs + vector_docs:
        cnt = doc.page_content
        total = vector_scores.get(cnt, 0) + bm25_scores.get(cnt, 0)
        all_docs_dict[cnt] = (total, doc)

    sorted_docs = sorted(all_docs_dict.values(), key=lambda x: x[0], reverse=True)
    return [doc for score, doc in sorted_docs[:FINAL_TOP_K]]

# ===================== 方式二：RRF 倒数排名融合 =====================
def rrf_fusion(bm25_docs, vector_docs, rrf_k=60):
    bm25_rank_map = {doc.page_content: idx+1 for idx, doc in enumerate(bm25_docs)}
    vector_rank_map = {doc.page_content: idx+1 for idx, doc in enumerate(vector_docs)}

    all_doc_set = {}
    for doc in bm25_docs + vector_docs:
        key = doc.page_content
        if key not in all_doc_set:
            all_doc_set[key] = doc

    doc_rrf_score = {}
    for page_text, doc in all_doc_set.items():
        score = 0.0
        if page_text in bm25_rank_map:
            score += 1.0 / (bm25_rank_map[page_text] + rrf_k)
        if page_text in vector_rank_map:
            score += 1.0 / (vector_rank_map[page_text] + rrf_k)
        doc_rrf_score[page_text] = score

    item_list = [(all_doc_set[text], score) for text, score in doc_rrf_score.items()]
    sorted_items = sorted(item_list, key=lambda x: x[1], reverse=True)
    return [doc for doc, _score in sorted_items]

def rrf_retrieve(query, vectorstore):
    all_docs = get_all_docs(vectorstore)

    # BM25 粗排
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = TOP_K
    bm25_docs = bm25_retriever.invoke(query)

    # 向量粗排
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    vector_docs = vector_retriever.invoke(query)

    # RRF 融合
    fused_all = rrf_fusion(bm25_docs, vector_docs, rrf_k=RRF_K)
    return fused_all[:FINAL_TOP_K]

# ===================== 统一混合检索入口 =====================
def hybrid_retrieve(query, vectorstore, mode="rrf"):
    """
    根据 mode 选择加权融合或 RRF 融合，返回候选文档列表
    """
    if mode == "weighted":
        print("[检索模式] 加权融合")
        return weighted_fusion(query, vectorstore)
    else:  # 默认 rrf
        print("[检索模式] RRF 倒数排名融合")
        return rrf_retrieve(query, vectorstore)

# ===================== RAG 主流程 =====================
def run_rag_qa(query, persist_directory):
    if not os.path.exists(persist_directory):
        print("❌ 请先构建向量数据库")
        return

    embeddings = HuggingFaceEmbeddings(
        model_name=local_embed_path,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

    # 1. 粗排 + 融合（支持两种模式）
    candidates = hybrid_retrieve(query, vectorstore, mode=HYBRID_MODE)

    # 2. Reranker 精排
    final_docs = reranker.rank(query, candidates)[:RERANK_TOP_K]

    print("\n" + "="*60)
    print(f"✅ 混合检索（{HYBRID_MODE}） + 本地Reranker完成，返回 {len(final_docs)} 条")
    print("="*60)
    for i, d in enumerate(final_docs):
        print(f"\n结果 {i+1}：\n{d.page_content}\n")

    # 3. LLM 生成
    llm = ChatOpenAI(model=model_name, temperature=0, api_key=api_key, base_url=base_url)

    system_prompt = (
        "你是华为年报文档问答助手。\n"
        "请严格基于以下提供的文档内容回答用户问题。\n"
        "如果找不到答案，请直接说“根据华为年报文档，未查询到相关信息”，不要编造。\n\n"
        "【参考文档】\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    rag_chain = (
        {"context": lambda x: format_docs(final_docs), "input": lambda x: x["input"]}
        | prompt
        | llm
        | StrOutputParser()
    )

    print("================ 问答 ================")
    print(f"问题：{query}")
    answer = rag_chain.invoke({"input": query})
    print(f"\n回答：\n{answer}")
    print("="*60)

if __name__ == "__main__":
    run_rag_qa("华为的经营业绩怎么样？", persist_directory=CHROMA_PERSIST_DIR)