# 保险精准营销系统 - Docker 部署说明

## 📦 部署文件

本目录已包含完整的 Docker 部署配置：

| 文件名 | 说明 |
| --- | --- |
| `Dockerfile` | 镜像构建文件，基于 Python 3.12-slim |
| `docker-compose.yml` | 服务编排配置 |
| `.dockerignore` | Docker 构建忽略文件 |
| `.env.docker` | Docker 环境变量模板 |
| `deploy-docker.bat` | Windows 一键部署脚本 |
| `deploy-docker.sh` | macOS/Linux 一键部署脚本 |

## 🚀 快速开始

### 方式一：一键部署脚本（推荐）

```bash
# Windows
deploy-docker.bat

# macOS / Linux
chmod +x deploy-docker.sh
./deploy-docker.sh
```

### 方式二：手动部署

```bash
# 1. 准备环境文件
copy .env.docker .env        # Windows
cp .env.docker .env        # macOS / Linux

# 2. （可选）编辑 .env，修改密钥和密码
# JWT_SECRET_KEY 是必填的，生产环境务必使用强随机字符串

# 3. 构建并启动
docker-compose up -d

# 4. 访问
http://127.0.0.1:5000
```

## 🔐 默认账号

| 用户名 | 密码 |
| --- | --- |
| `admin` | `admin123` |

## 📝 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose stop

# 启动服务
docker-compose start

# 重启服务
docker-compose restart

# 删除容器（数据保留）
docker-compose down

# 重新构建并启动
docker-compose up -d --build

# 进入容器
docker exec -it insurance-ai-app bash
```

## 💾 数据持久化

Docker 容器中的数据已映射到本地目录：

| 容器内路径 | 本地路径 | 说明 |
| --- | --- | --- |
| `/app/data/` | `./data/` | 模型文件和上传数据 |
| `/app/instance/` | `./instance/` | SQLite 数据库 |

删除容器不会丢失数据！

## 📊 健康检查

服务自动运行健康检查，每 30 秒检查一次 `/api/v1/auth/login`。

## ⚙️ 配置说明

### 环境变量

编辑 `.env` 文件修改配置：

```env
# JWT 密钥（生产环境必须修改）
JWT_SECRET_KEY=your-very-strong-secret-key-here

# 管理员密码
DEFAULT_ADMIN_PASSWORD=your-password-here

# 大模型（可选）
LLM_API_KEY=sk-xxx
```

## 🔧 故障排查

### 1. 端口已被占用

修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8080:5000"  # 改为 8080 或其他端口
```

### 2. 依赖安装失败

尝试单独构建：

```bash
docker-compose build --no-cache
```

### 3. 数据文件权限问题（Linux）

```bash
chmod -R 755 data/ instance/
sudo chown -R $USER:$USER data/ instance/
```

### 4. 查看详细日志

```bash
docker-compose logs -f app
```

## 📚 进阶配置

### 使用 MySQL/PostgreSQL（可选）

修改 `.env` 中的 `DATABASE_URL`：

```env
# MySQL
DATABASE_URL=mysql+pymysql://user:password@db:3306/insurance

# PostgreSQL
DATABASE_URL=postgresql://user:password@db:5432/insurance
```

注意：需要相应修改 `docker-compose.yml` 添加数据库服务。

### 生产部署建议

1. **修改 JWT_SECRET_KEY**：使用强随机字符串
2. **修改管理员密码**：不要使用默认密码
3. **配置 HTTPS**：使用反向代理（Nginx/Caddy）
4. **设置资源限制**：在 docker-compose.yml 中添加 resources 配置
5. **备份数据**：定期备份 `data/` 和 `instance/` 目录
