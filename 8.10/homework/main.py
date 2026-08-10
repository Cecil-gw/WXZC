import os
import json
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv(override=True)

JSON_SAVE_PATH = r"D:\wx26.7.14\8.10\homework\split_result.json"
CHROMA_PERSIST_DIR = r"D:\wx26.7.14\8.10\homework\chroma_huawei"
BGE_MODEL_PATH = r"D:\wx26.7.14\bge-large-zh"
PDF_PATH = r"d:/wx26.7.14/8.10/homework/huawei_report.pdf"


def save_split_docs(docs, save_path):
    data = [{"page_content": d.page_content, "metadata": d.metadata} for d in docs]
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_split_docs(save_path):
    with open(save_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Document(page_content=item["page_content"], metadata=item["metadata"]) for item in data]


def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])


def main():
    print("\n===3.加载本地BGE‑large‑zh embedding===")
    bge_embedding = HuggingFaceBgeEmbeddings(
        model_name=BGE_MODEL_PATH,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    test_vector = bge_embedding.embed_query("测试文本")
    print(f"embedding向量维度：{len(test_vector)}")

    if os.path.exists(JSON_SAVE_PATH):
        print("检测到已存在分块文件，直接读取，跳过PDF解析与分块")
        split_docs = load_split_docs(JSON_SAVE_PATH)
        print(f"读取成功，chunk总数：{len(split_docs)}")
        print("示例chunk:\n", split_docs[0].page_content[:250])
    else:
        print("1.加载PDF")
        loader = PyPDFLoader(PDF_PATH)
        docs = loader.load()
        print(f"PDF一共 {len(docs)} 页")

        print("\n2.文档分块")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=280,
            chunk_overlap=40,
            separators=["\n\n", "\n", "。", "，"]
        )
        split_docs = text_splitter.split_documents(docs)

        # 添加元数据
        for doc in split_docs:
            doc.metadata["source"] = "华为年报"
            doc.metadata["doc_type"] = "财报文档"

        print(f"分块完成，总chunk数量：{len(split_docs)}")
        print("第一个chunk片段:\n", split_docs[0].page_content[:250])

        save_split_docs(split_docs, JSON_SAVE_PATH)
        print(f"分块结果已保存到 {JSON_SAVE_PATH}")

    print("\n4.构建/加载Chroma向量库===")
    if os.path.exists(CHROMA_PERSIST_DIR) and os.listdir(CHROMA_PERSIST_DIR):
        print("检测到已存在Chroma向量库，直接加载，跳过向量化")
        db = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=bge_embedding
        )
    else:
        print("向量库不存在，开始向量化并构建Chroma")
        db = Chroma.from_documents(
            documents=split_docs,
            embedding=bge_embedding,
            persist_directory=CHROMA_PERSIST_DIR
        )
        print(f"向量库构建完成，保存路径：{CHROMA_PERSIST_DIR}")

    print(f"向量库总文档数：{db._collection.count()}")

    print("\n5.简单相似度检索测试===")
    query = "华为的营业收入是多少"
    docs_retrieved = db.similarity_search(query, k=3)
    for idx, doc in enumerate(docs_retrieved):
        print(f"\n---检索结果{idx+1}---")
        print(doc.page_content[:300])

    print("\n6.构建RAG问答链===")
    retriever = db.as_retriever(k=3)

    llm = ChatOpenAI(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BASE_URL"),
        model=os.getenv("MODEL_NAME"),
        temperature=0.1
    )

    rag_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是华为年报问答助手，严格使用下面的上下文回答用户问题。如果上下文没有答案，直接回答‘文档中未找到相关信息’，不要编造。\n上下文：{context}"),
        ("human", "用户问题：{question}")
    ])

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt
        | llm
        | StrOutputParser()
    )

    # 交互循环：输入exit退出
    print("\n=====RAG交互，输入exit退出=====")
    while True:
        user_input = input("请输入问题：")
        if user_input.strip().lower() == "exit":
            break
        res = rag_chain.invoke(user_input)
        print(f"回答：{res}\n")


if __name__ == "__main__":
    main()