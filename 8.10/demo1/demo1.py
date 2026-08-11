from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 5条待测试文本
sentences = [
    "Java开发工程师要求3年以上经验",
    "Python岗位要求熟悉Django框架",
    "公司节日福利包括购物卡和电影票",
    "员工享受带薪年假和五险一金",
    "Java高级工程师需精通JVM调优"
]

# 加载本地bge‑large‑zh模型，修改为你本机实际路径
model = SentenceTransformer(r"D:\wx26.7.14\bge-large-zh")

# 批量文本向量化
embeddings = model.encode(sentences)

# ==========任务1：输出向量维度、前5个向量数值==========
print("=====任务1 向量信息=====")
for idx, vec in enumerate(embeddings):
    print(f"\n句子{idx+1}：{sentences[idx]}")
    print(f"向量维度：{vec.shape[0]}")
    print(f"向量前5个值：{np.round(vec[:5],4)}")

# ==========任务2：5×5余弦相似度矩阵，寻找最相似句子对==========
sim_matrix = cosine_similarity(embeddings)
print("\n=====任务2 5×5余弦相似度矩阵====")
print(np.round(sim_matrix, 4))

max_score = -1.0
best_i = 0
best_j = 0
n = len(sentences)
for i in range(n):
    for j in range(i + 1, n):
        score = sim_matrix[i][j]
        if score > max_score:
            max_score = score
            best_i = i
            best_j = j

print(f"\n最相似句子对，相似度={round(max_score,4)}")
print(f"【{best_i+1}】{sentences[best_i]}")
print(f"【{best_j+1}】{sentences[best_j]}")

# ==========任务3：实战问答，返回Top2相似句子==========
query = "Java岗位有什么要求？"
query_emb = model.encode([query])
scores = cosine_similarity(query_emb, embeddings)[0]

rank_result = sorted(zip(scores, sentences), key=lambda x:x[0], reverse=True)
top2 = rank_result[:2]

print("\n=====任务3 Top2相似结果====")
print(f"用户提问：{query}")
for sim, text in top2:
    print(f"相似度:{round(sim,4)} → {text}")