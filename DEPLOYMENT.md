# 项目部署指南

本文档介绍如何打包和部署生产排程系统。

---

## 方式一：本地部署（推荐用于开发和测试）

### 1. 环境准备

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行应用

```bash
# 使用快捷脚本
run.bat          # Windows
./run.sh         # Linux/Mac

# 或手动启动
streamlit run ui/app.py
```

### 4. 访问应用

打开浏览器访问：`http://localhost:8501`

---

## 方式二：Docker 容器化部署

### 1. 创建 Dockerfile

项目已包含 `Dockerfile`，内容如下：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. 构建镜像

```bash
docker build -t production-scheduler:latest .
```

### 3. 运行容器

```bash
docker run -p 8501:8501 production-scheduler:latest
```

### 4. 访问应用

打开浏览器访问：`http://localhost:8501`

---

## 方式三：使用 Docker Compose

### 1. 创建 docker-compose.yml

项目已包含 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  scheduler:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
    restart: unless-stopped
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 停止服务

```bash
docker-compose down
```

---

## 方式四：云平台部署

### Streamlit Cloud（最简单）

1. 将代码推送到 GitHub
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 连接 GitHub 仓库
4. 选择 `ui/app.py` 作为主文件
5. 点击部署

**优点**：
- 免费
- 自动部署
- 自动 HTTPS

**限制**：
- 资源有限
- 公开访问

### Heroku

1. 创建 `Procfile`：
```
web: streamlit run ui/app.py --server.port=$PORT --server.address=0.0.0.0
```

2. 创建 `setup.sh`：
```bash
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

3. 部署：
```bash
heroku login
heroku create your-app-name
git push heroku main
```

### AWS EC2

1. 启动 EC2 实例（Ubuntu）
2. 安装依赖：
```bash
sudo apt update
sudo apt install python3-pip python3-venv
```

3. 克隆项目：
```bash
git clone <your-repo>
cd production-scheduling-agent
```

4. 安装并运行：
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run ui/app.py --server.port=8501 --server.address=0.0.0.0
```

5. 配置安全组，开放 8501 端口

### Azure Web App

1. 创建 Web App（Python 3.9）
2. 配置启动命令：
```bash
python -m streamlit run ui/app.py --server.port=8000 --server.address=0.0.0.0
```

3. 部署代码：
```bash
az webapp up --name your-app-name --resource-group your-rg
```

---

## 方式五：打包为可执行文件（Windows）

### 使用 PyInstaller

1. 安装 PyInstaller：
```bash
pip install pyinstaller
```

2. 创建打包脚本 `build.spec`：
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['ui/app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data_layer', 'data_layer'),
        ('business_logic', 'business_logic'),
        ('ui', 'ui'),
        ('docs', 'docs'),
    ],
    hiddenimports=[
        'streamlit',
        'ortools',
        'pandas',
        'plotly',
        'openpyxl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ProductionScheduler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

3. 打包：
```bash
pyinstaller build.spec
```

4. 可执行文件位于 `dist/ProductionScheduler.exe`

**注意**：Streamlit 应用打包为 exe 可能会遇到问题，建议使用 Docker 或云部署。

---

## 方式六：内网部署

### 使用 Nginx 反向代理

1. 安装 Nginx

2. 配置 Nginx（`/etc/nginx/sites-available/scheduler`）：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. 启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/scheduler /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

4. 使用 systemd 管理 Streamlit：

创建 `/etc/systemd/system/scheduler.service`：
```ini
[Unit]
Description=Production Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/production-scheduling-agent
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/streamlit run ui/app.py --server.port=8501
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable scheduler
sudo systemctl start scheduler
```

---

## 配置选项

### Streamlit 配置文件

创建 `.streamlit/config.toml`：

```toml
[server]
port = 8501
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

---

## 性能优化

### 1. 缓存配置

在代码中使用 Streamlit 缓存：
```python
@st.cache_data
def load_data(file):
    return parse_data(file)
```

### 2. 资源限制

在 Docker 中限制资源：
```bash
docker run -p 8501:8501 \
  --memory="2g" \
  --cpus="2" \
  production-scheduler:latest
```

### 3. 并发处理

使用 Gunicorn（不推荐用于 Streamlit，但可用于 API）：
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:server
```

---

## 安全建议

### 1. 添加身份验证

使用 Streamlit-Authenticator：
```python
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(
    credentials,
    'cookie_name',
    'signature_key',
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:
    # 显示应用内容
    pass
```

### 2. HTTPS 配置

使用 Let's Encrypt：
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. 防火墙配置

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 监控和日志

### 1. 应用日志

Streamlit 日志位置：
- Linux: `~/.streamlit/logs/`
- Windows: `%USERPROFILE%\.streamlit\logs\`

### 2. 监控工具

使用 Prometheus + Grafana 监控：
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'streamlit'
    static_configs:
      - targets: ['localhost:8501']
```

---

## 备份和恢复

### 1. 数据备份

```bash
# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# 定期备份（crontab）
0 2 * * * /path/to/backup.sh
```

### 2. 数据库备份（如果使用）

```bash
# PostgreSQL
pg_dump dbname > backup.sql

# MySQL
mysqldump -u user -p dbname > backup.sql
```

---

## 故障排查

### 常见问题

1. **端口被占用**
```bash
# 查找占用端口的进程
netstat -ano | findstr :8501  # Windows
lsof -i :8501                 # Linux/Mac

# 杀死进程
taskkill /PID <pid> /F        # Windows
kill -9 <pid>                 # Linux/Mac
```

2. **依赖安装失败**
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

3. **内存不足**
```bash
# 增加 Docker 内存限制
docker run --memory="4g" ...

# 优化代码，使用缓存
@st.cache_data
```

---

## 更新和维护

### 1. 更新应用

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
sudo systemctl restart scheduler
```

### 2. 版本管理

使用语义化版本：
```
v1.0.0 - 初始版本
v1.1.0 - 添加多目标优化
v1.2.0 - 优化甘特图显示
```

---

## 总结

推荐部署方式：

| 场景 | 推荐方式 | 优点 |
|-----|---------|------|
| 开发测试 | 本地运行 | 简单快速 |
| 小团队内网 | Docker + Nginx | 稳定可靠 |
| 公开演示 | Streamlit Cloud | 免费简单 |
| 生产环境 | AWS/Azure | 可扩展、专业 |
| 离线环境 | Docker | 隔离完整 |

选择合适的部署方式，确保系统稳定运行！
