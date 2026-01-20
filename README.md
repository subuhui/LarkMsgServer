# LarkMsgServer

飞书消息发送服务 - 支持多机器人、文本/图片/富文本消息，数据库 SQLCipher 加密。

## 功能特性

- 支持多个飞书机器人配置
- 统一消息发送接口 (自动判断消息类型)
- 支持文本、图片、图文混合消息
- SQLCipher 数据库加密，防止数据泄露
- 提供 HTTP API 和 CLI 两种调用方式
- FastAPI 自带 Swagger 文档

## 快速开始

### 1. 安装依赖

```bash
# 安装 SQLCipher (必须先安装)
# macOS
brew install sqlcipher

# Ubuntu/Debian
sudo apt install libsqlcipher-dev

# CentOS/RHEL
sudo yum install sqlcipher-devel

# 安装 Python 依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件:

```bash
# SQLCipher 数据库加密密钥 (必填，建议32位随机字符串)
LARK_DB_KEY=your-32-char-encryption-key-here

# 服务配置
LARK_SERVER_HOST=0.0.0.0
LARK_SERVER_PORT=234
```

### 3. 初始化数据库

```bash
python -m src.main init
```

### 4. 添加机器人

```bash
python -m src.main bot add \
  --name mybot \
  --app-id cli_xxxxxxxx \
  --app-secret xxxxxxxxxxxxxxxx
```

### 5. 启动服务

```bash
python -m src.main serve
```

服务启动后访问: http://localhost:234/docs 查看 API 文档

## API 使用

### 发送消息

**接口:** `POST /api/send`

**Content-Type:** `multipart/form-data`

**参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| bot_name | string | 是 | 机器人名称 |
| receive_id | string | 是 | 接收者 ID |
| receive_id_type | string | 否 | ID 类型: open_id(默认)/user_id/email |
| title | string | 否 | 消息标题 (富文本时使用) |
| content | string | 否 | 文本内容 |
| image | file | 否 | 图片文件 |

> content 和 image 至少提供一个

**示例:**

```bash
# 发送纯文本
curl -X POST http://localhost:234/api/send \
  -F "bot_name=mybot" \
  -F "receive_id=ou_xxxxxxxx" \
  -F "content=Hello World"

# 发送图片
curl -X POST http://localhost:234/api/send \
  -F "bot_name=mybot" \
  -F "receive_id=ou_xxxxxxxx" \
  -F "image=@./photo.png"

# 发送图文混合 (富文本)
curl -X POST http://localhost:234/api/send \
  -F "bot_name=mybot" \
  -F "receive_id=ou_xxxxxxxx" \
  -F "title=通知标题" \
  -F "content=这是通知内容" \
  -F "image=@./photo.png"
```

### 机器人管理

```bash
# 添加机器人
POST /api/bots
{
  "name": "mybot",
  "app_id": "cli_xxx",
  "app_secret": "xxx"
}

# 列出机器人
GET /api/bots

# 删除机器人
DELETE /api/bots/{id}
```

## CLI 使用

### 服务管理

```bash
# 启动 HTTP 服务
python -m src.main serve

# 指定端口
python -m src.main serve --port 8080

# 初始化数据库
python -m src.main init
```

### 机器人管理

```bash
# 添加机器人
python -m src.main bot add --name mybot --app-id cli_xxx --app-secret xxx

# 列出机器人
python -m src.main bot list

# 删除机器人
python -m src.main bot remove mybot
```

### 发送消息

```bash
# 发送纯文本
python -m src.main send \
  --bot mybot \
  --to ou_xxxxxxxx \
  --content "Hello World"

# 发送图片
python -m src.main send \
  --bot mybot \
  --to ou_xxxxxxxx \
  --image ./photo.png

# 发送图文混合
python -m src.main send \
  --bot mybot \
  --to ou_xxxxxxxx \
  --title "通知" \
  --content "详情内容" \
  --image ./photo.png

# 使用邮箱作为接收者
python -m src.main send \
  --bot mybot \
  --to user@company.com \
  --id-type email \
  --content "Hello"
```

## 接收者 ID 说明

| ID 类型 | 格式示例 | 说明 |
|---------|----------|------|
| open_id | ou_xxxxxxxxx | 用户的 Open ID (默认) |
| user_id | on_xxxxxxxxx | 用户的 User ID |
| email | user@company.com | 用户邮箱 |

**获取 Open ID 方法:**

1. 飞书开放平台 → 应用 → 调试 → 消息 → 发送消息，选择接收者时显示
2. 用户给机器人发消息时，事件回调中包含 `open_id`
3. 调用飞书 API: `POST /contact/v3/users/batch_get_id`

## Linux 部署

### 后台运行 (nohup)

```bash
# 后台启动
nohup python -m src.main serve > /var/log/lark-msg-server.log 2>&1 &

# 查看日志
tail -f /var/log/lark-msg-server.log

# 停止服务
pkill -f "python -m src.main serve"
```

### 使用 Screen

```bash
# 创建 screen 会话
screen -S lark-msg

# 启动服务
python -m src.main serve

# 按 Ctrl+A+D 分离会话

# 重新连接
screen -r lark-msg
```

### Systemd 服务 (推荐)

创建服务文件:

```bash
sudo vim /etc/systemd/system/lark-msg-server.service
```

写入以下内容:

```ini
[Unit]
Description=Lark Message Server
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/LarkMsgServer
Environment="PATH=/opt/LarkMsgServer/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="LARK_DB_KEY=your-32-char-encryption-key-here"
Environment="LARK_SERVER_PORT=234"
ExecStart=/opt/LarkMsgServer/venv/bin/python -m src.main serve
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用服务:

```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start lark-msg-server

# 设置开机启动
sudo systemctl enable lark-msg-server

# 查看状态
sudo systemctl status lark-msg-server

# 查看日志
sudo journalctl -u lark-msg-server -f

# 停止服务
sudo systemctl stop lark-msg-server

# 重启服务
sudo systemctl restart lark-msg-server
```

### 完整部署步骤

```bash
# 1. 上传代码到服务器
scp -r LarkMsgServer root@your-server:/opt/

# 2. 登录服务器
ssh root@your-server

# 3. 安装依赖
cd /opt/LarkMsgServer
apt update && apt install -y python3-venv libsqlcipher-dev

# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. 配置环境变量
cp .env.example .env
vim .env  # 编辑配置

# 6. 初始化数据库
python -m src.main init

# 7. 添加机器人
python -m src.main bot add --name mybot --app-id xxx --app-secret xxx

# 8. 创建 systemd 服务 (参考上面的配置)
sudo vim /etc/systemd/system/lark-msg-server.service

# 9. 启动并设置开机启动
sudo systemctl daemon-reload
sudo systemctl enable --now lark-msg-server

# 10. 验证服务
curl http://localhost:234/health
```

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| LARK_DB_KEY | 是 | - | SQLCipher 数据库加密密钥 |
| LARK_SERVER_HOST | 否 | 0.0.0.0 | HTTP 服务监听地址 |
| LARK_SERVER_PORT | 否 | 234 | HTTP 服务端口 |
| LARK_DB_PATH | 否 | data.db | 数据库文件路径 |
| LARK_API_KEY | 否 | - | API 认证密钥 (可选) |

## 项目结构

```
LarkMsgServer/
├── .env.example          # 环境变量模板
├── requirements.txt      # Python 依赖
├── README.md
└── src/
    ├── __init__.py
    ├── config.py         # 配置管理
    ├── main.py           # 程序入口
    ├── api/
    │   ├── router.py     # FastAPI 路由
    │   └── schemas.py    # Pydantic 模型
    ├── cli/
    │   └── commands.py   # Typer CLI
    ├── db/
    │   ├── database.py   # SQLCipher 连接
    │   └── models.py     # Bot 模型
    └── lark/
        └── client.py     # 飞书 API 客户端
```

## 消息类型判断逻辑

| 条件 | 消息类型 |
|------|----------|
| 只有 content | 纯文本 (text) |
| content + title | 富文本 (post) |
| 只有 image | 图片 (image) |
| image + content (+ title) | 图文混合 (post) |
