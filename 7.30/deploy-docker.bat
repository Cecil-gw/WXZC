@echo off
REM 保险精准营销系统 - Docker 一键部署脚本（Windows）
REM 请确保已安装 Docker Desktop

echo ========================================
echo 保险精准营销 AI 系统 - Docker 部署
echo ========================================
echo.

REM 检查 Docker 是否可用
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安装或未启动！
    echo.
    echo 请先下载并安装 Docker Desktop:
    echo   https://www.docker.com/get-started
    echo.
    pause
    exit /b 1
)

echo ✅ Docker 已就绪
docker --version
echo.

REM 准备环境文件
if not exist ".env" (
    echo 📄 正在创建 .env 文件...
    copy .env.docker .env >nul
    echo ⚠️  请记得编辑 .env 中的 JWT_SECRET_KEY 和密码！
)

echo 📦 正在构建并启动容器...
echo.

docker-compose up -d --build

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo ✅ 部署成功！
    echo ========================================
    echo.
    echo 访问地址: http://127.0.0.1:5000
    echo.
    echo 账号: admin
    echo 密码: admin123
    echo.
    echo 查看日志: docker-compose logs -f
    echo 停止服务: docker-compose down
    echo.
) else (
    echo.
    echo ❌ 部署失败，请查看上方错误信息。
    echo.
)

pause
