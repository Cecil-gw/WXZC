import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate

# 加载环境
load_dotenv(override=True)
llm = ChatOpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),
    model=os.getenv("MODEL_NAME"),
    temperature=0.1
)
embedding = OpenAIEmbeddings(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)

PDF_FOLDER = "D:\\wx26.7.14\\8.10\\docs\\pdfs"
CHROMA_DB_PATH = "D:\\wx26.7.14\\8.10\\data\\chroma_db"

def build_vector_db():
    """离线构建：读取全部pdf，切分，存入向量库，只需要执行一次"""
    print("正在加载全部PDF...")
    # 加载文件夹下所有pdf
    loader = PyPDFDirectoryLoader(PDF_FOLDER)
    docs = loader.load()
    print(f"一共读取 {len(docs)} 页pdf")

    # 文档切分
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120
    )
    chunks = text_splitter.split_documents(docs)
    print(f"切分得到 {len(chunks)} 个文本块")

    # 存入Chroma向量库
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        persist_directory=CHROMA_DB_PATH
    )
    print("✅向量库构建完成")
    return db

def get_rag_chain(db):
    prompt = ChatPromptTemplate.from_messages([
        ("system","请严格根据下面文档内容回答用户问题，不知道就直接说不知道，不要编造。文档：{context}"),
        ("human","用户问题：{question}")
    ])
    retriever = db.as_retriever(search_kwargs={"k":3})

    def rag_query(question:str):
        #检索
        docs = retriever.invoke(question)
        context_text = "\n=====\n".join([d.page_content for d in docs])
        res = llm.invoke(prompt.format(context=context_text, question=question))
        return res.content, docs

    return rag_query

if __name__ == "__main__":
    # 如果向量库文件夹不存在，就重新构建；存在直接加载
    if not os.path.exists(CHROMA_DB_PATH):
        db = build_vector_db()
    else:
        print("加载已有向量库")
        db = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embedding)

    rag_func = get_rag_chain(db)

    #交互问答
    while True:
        q = input("\n请输入问题(exit退出):")
        if q.strip() == "exit":
            break
        ans,retrieve_docs = rag_func(q)
        print(f"\n回答：{ans}")
        #打印检索到的片段，方便调试看召回效果
        print("\n---本次检索到的文档片段---")
        for idx,d in enumerate(retrieve_docs):
            print(f"【片段{idx+1}】来源文件:{d.metadata['source']} 页码:{d.metadata['page']}")