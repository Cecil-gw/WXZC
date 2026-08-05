from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv(r"D:\wx26.7.14\8.5\langchain\.env", override=True)

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

print(f"API_KEY: {api_key[:10]}...")  
print(f"BASE_URL: {base_url}")
print(f"MODEL_NAME: {model_name}")

llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
    temperature=0.7,
)


def call_llm(title,descs,feature):
  prompt=PromptTemplate(
    input_variables=["title","descs","feature"],
    template="""
    根据以下标题和描述，生成一个产品介绍：
    标题：{title}
    描述：{descs}
    特点：{feature}
    """,
  )
  final_prompt = prompt.format(title=title, descs=descs, feature=feature)
  print(f"Final Prompt: {final_prompt}")
  resp = llm.invoke(final_prompt)
  return resp.content

def call_llm2(title, descs, feature):
    # 把三个变量拼接成question文本
    question = f"主题：{title}，产品描述：{descs}，产品特点：{feature}"
    
    # 构建聊天消息模板
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "这里写system角色"),
            ("human", "{question}"),
            ("ai", "这里写ai的参考样例"),
            ("human", "生成一句slogan")
        ]
    )
    
    # 填充变量
    messages = chat_prompt.format_messages(question=question)
    # 调用模型
    res = llm.invoke(messages)
    return res.content

if __name__ == "__main__":
  out = call_llm("冰可乐","解暑饮料","气泡充足")
  print(out)
  out = call_llm2("冰可乐","解暑饮料","气泡充足")
  print(out)

  # ... (前面加载环境变量和初始化 llm 的代码保持不变) ...

def create_chat_chain():
    """创建一个带有记忆功能的对话链"""
    
    # 1. 定义提示模板，使用 MessagesPlaceholder 来插入历史消息
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的文案助手，擅长创作引人注目的产品slogan。"),
        MessagesPlaceholder(variable_name="history"),  # 历史消息会插入在这里
        ("human", "{input}")  # 用户最新的输入
    ])
    
    # 2. 创建基础的 LCEL 链
    chain = prompt | llm
    
    # 3. 用 RunnableWithMessageHistory 包装链，赋予其记忆功能
    chain_with_history = RunnableWithMessageHistory(
        runnable=chain,
        # 这个函数根据 session_id 返回对应的历史存储对象
        get_message_history=lambda session_id: ChatMessageHistory(),
        input_messages_key="input",          # 指定输入变量中哪个是用户的新消息
        history_messages_key="history"       # 指定提示模板中哪个变量存放历史消息
    )
    
    return chain_with_history

# 创建一个带记忆的链实例
    chat_chain = create_chat_chain()

    # 模拟多轮对话
    session_id = "user_123"  # 用于区分不同用户或会话

    # 第一轮对话
    response1 = chat_chain.invoke(
        {"input": "主题：冰可乐，产品描述：解暑饮料，产品特点：气泡充足"},
        config={"configurable": {"session_id": session_id}}
    )
    print("第一轮回复:", response1.content)

    # 第二轮对话，模型会记住第一轮的内容
    response2 = chat_chain.invoke(
        {"input": "基于刚才的产品，再想一句更酷的英文slogan"},
        config={"configurable": {"session_id": session_id}}
    )
    print("第二轮回复:", response2.content)