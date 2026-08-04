import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

# ===================== 1. 生成模拟数据集 =====================
# 输入特征：1000条样本，2维特征
X = torch.randn(1000, 2)
# 真实模型参数
true_weights = torch.tensor([[2.0], [-3.0]])
true_bias = 5.0
# 构造标签，叠加高斯噪声模拟真实数据
Y = X @ true_weights + true_bias + 0.1 * torch.randn(1000, 1)

# ===================== 2. 构建数据集与迭代器 =====================
dataset = TensorDataset(X, Y)
# 分批加载数据，开启随机打乱
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

# ===================== 3. 定义线性回归模型 =====================
class LinearRegression(nn.Module):
    def __init__(self):
        super().__init__()
        # 输入2维特征，输出1维预测值
        self.linear = nn.Linear(2, 1)

    def forward(self, x):
        # 前向传播，返回预测结果
        outputs = self.linear(x)
        return outputs

# 实例化模型
model = LinearRegression()

# ===================== 4. 优化器、损失函数配置 =====================
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
# 均方误差损失，回归任务标准损失
criterion = nn.MSELoss()

# ===================== 5. 模型训练循环 =====================
for epoch in range(20):
    model.train()
    epoch_loss = 0

    # 遍历所有批次数据
    for batch_X, batch_y in dataloader:
        # 前向计算预测值
        outputs = model(batch_X)
        # 计算损失
        loss = criterion(outputs, batch_y)

        # 梯度清零、反向传播、参数更新
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    # 每10轮输出平均损失
    if (epoch + 1) % 10 == 0:
        avg_loss = epoch_loss / len(dataloader)
        print(f"Epoch [{epoch+1}/{20}], Loss: {avg_loss:.4f}")

# 输出训练完成后的权重与偏置，对比真实参数
print("训练得到模型参数：")
print(model.state_dict())