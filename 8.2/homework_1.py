# 学生代码框架提示
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

# 1. 生成数据
X = torch.randn(1000, 2)
# TODO: 构造真实的 Y
# 设定真实的权重和偏置
true_weights = torch.tensor([[2.0], [-3.0]])
true_bias = 5.0
# 构造真实的 Y 值，并加入少量噪声
Y = X @ true_weights + true_bias + 0.1 * torch.randn(1000, 1)


# 2. 数据加载
# TODO: 构建 Dataset 和 DataLoader
dataset = TensorDataset(X, Y)
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

# 3. 构建模型
class LinearRegression(nn.Module):
  def __init__(self):
      super().__init__()
      # TODO: 定义一个线性层 nn.Linear
      self.linear = nn.Linear(2, 1)

  def forward(self, x):
      # TODO: 实现前向传播
      # return: 返回模型的预测值
      outputs = self.linear(x)# 线性层输出
      return outputs

model = LinearRegression()

# 4. 训练配置与循环
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
criterion = nn.MSELoss()

for epoch in range(20):
    # TODO: 编写完整的训练过程
    model.train()
    epoch_loss = 0
    for batch_X, batch_y in dataloader:
        outputs = model(batch_X)
        loss = criterion(outputs, batch_y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()
    
    # 每10个epoch打印一次
    if (epoch + 1) % 10 == 0:
        avg_loss = epoch_loss / len(dataloader)
        print(f"Epoch [{epoch+1}/{20}], Loss: {avg_loss:.4f}")
   

    

# 检查学习到的参数
print(model.state_dict())