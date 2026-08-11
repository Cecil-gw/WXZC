import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

local_model_path = "./bge-small-zh-v1.5"

def run_rag_qa(query, persist_directory="./chroma_db"):
    if not os.path.exists(persist_directory):
        print(f"❌ 找不到向量数据库目录 '{persist_directory}'，请先运行 2_vector_builder.py。")
        return

    print("▶ 正在加载嵌入模型...")
    embeddings = HuggingFaceEmbeddings(
        model_name=local_model_path,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    print("▶ 正在加载本地向量数据库...")
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )

    llm = ChatOpenAI(model=model_name, temperature=0, api_key=api_key, base_url=base_url)

    system_prompt = (
        "你是星讯科技有限公司的内部智能人事/行政助手。\n"
        "请严格基于以下提供的公司内部文档内容回答用户问题。\n"
        "如果你在文档中找不到答案，请直接说“根据提供的文档，我无法回答该问题”，绝不能凭空编造信息。\n\n"
        "【参考文档内容】\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    def format_docs(docs):
        return "\n".join(doc.page_content for doc in docs)

    # ==============================
    # ✅ 修复：只检索一次，给打印 + 给LLM用
    # ==============================
    docs = retriever.invoke(query)
    print(docs)
    
    # 打印分块
    print("\n" + "="*60)
    print(f"📄 检索到的分块数量：{len(docs)}")
    print("="*60)
    for i, doc in enumerate(docs):
        print(f"\n--- 分块 {i+1} ---")
        print(f"内容：{doc.page_content}")
    print("\n" + "="*60 + "\n")

    # ==============================
    # ✅ 修复：链里直接使用上面检索好的 docs（不再二次检索）
    # ==============================
    rag_chain = (
        {"context": lambda x: format_docs(docs), "input": lambda x: x["input"]}
        | prompt
        | llm
        | StrOutputParser()
    )

    print(f"\n================ 问答测试 ================")
    print(f"👤 用户提问: {query}")
    print("🤖 正在检索知识库并生成答案，请稍候...\n")

    answer = rag_chain.invoke({"input": query})

    print("💡 回答:")
    print(answer)
    print("\n==========================================")

if __name__ == "__main__":
    test_query = "节日和生日福利有什么？"
    run_rag_qa(test_query)