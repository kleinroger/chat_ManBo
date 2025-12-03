# ManBo Chat 聊天室

一个使用 Tornado（Python）实现的简易群聊示例，包含：
- 后端 HTTP 路由与 WebSocket 群聊
- 前端登录页与聊天室页（UI 简洁，支持基础 emoji）
- 可通过 config.json 配置多个 WebSocket 服务器，并在登录页以“本地服务器/公共服务器X”的友好名称展示

## 目录结构
- app.py：后端服务入口（HTTP + WebSocket，支持 WS 独立端口）
- config.json：前端登录页读取的服务器地址列表（ws/wss）
- templates/login.html：登录页
- templates/chat.html：聊天室页
- static/js/login.js：登录页逻辑（读取 /config，渲染下拉）
- static/js/chat.js：聊天室逻辑（WebSocket 连接、消息展示等）
- static/css/：样式

## 关键端口与协议
- HTTP（后端）：默认 8888
  - 访问入口：http://localhost:8888/
  - 路由：`/`（登录页）`/chat`（聊天室页）`/config`（服务器列表）`/ws`（WebSocket 握手路径）
- WS（WebSocket）：默认与 HTTP 共端口 8888；可通过环境变量分离到独立端口
  - 握手地址：ws://localhost:8888/ws（默认）
  - 分离端口示例：将 WS 设为 8899 后，ws://localhost:8899/ws
- 开发静态预览（可选）：8887（python -m http.server）
  - 示例页面：http://localhost:8887/templates/login.html

## 启动步骤（Windows PowerShell）
1) 进入项目目录
```
cd d:\software\Trae\design\manbo_chat
```
2) 激活虚拟环境（如未激活）
```
./venv/Scripts/Activate.ps1
```
3) 安装依赖（如未安装）
```
pip install tornado
```
4) 启动后端（HTTP + WS 共用 8888）
```
./venv/Scripts/python.exe app.py
```
日志示例：
```
ManBo Chatroom HTTP running at http://localhost:8888/
ManBo Chatroom WS running at ws://localhost:8888/ws
```
5) 可选：将 WebSocket 改为独立端口（例如 8899）
```
$env:WS_PORT=8899; ./venv/Scripts/python.exe app.py
```
日志示例：
```
ManBo Chatroom HTTP running at http://localhost:8888/
ManBo Chatroom WS running at ws://localhost:8899/ws
```
6) 可选：启动静态预览（开发测试用）
```
python -m http.server 8887
```
访问：http://localhost:8887/templates/login.html

## 配置方式
- <mcfile name="config.json" path="d:\software\Trae\design\manbo_chat\config.json"></mcfile> 格式示例：
```
{
  "servers": [
    "ws://localhost:8888/ws",
    "ws://你的公网域名或IP:端口/ws"
  ]
}
```
- 登录页（<mcfile name="login.js" path="d:\software\Trae\design\manbo_chat\static\js\login.js"></mcfile>）会读取 `/config` 返回的 `servers` 列表，并：
  - 依据页面协议过滤（HTTPS 仅显示 wss://，HTTP 显示 ws:// 与 wss://）
  - 按主机名去重并优先 wss
  - 将域名转换为友好名称：localhost/127.0.0.1 → 本地服务器，其余依次为 公共服务器1/2…
- 聊天室页（<mcfile name="chat.js" path="d:\software\Trae\design\manbo_chat\static\js\chat.js"></mcfile>）使用 URL 参数中的 `ws` 进行连接，并在 HTTPS 页面上自动将 `ws://` 升级为 `wss://` 以避免混合内容被浏览器阻止

## 后端接口与握手
- <mcfile name="app.py" path="d:\software\Trae\design\manbo_chat\app.py"></mcfile>
  - 路由
    - GET `/`：登录页
    - GET `/chat`：聊天室页
    - GET `/config`：返回 `{ "servers": [ ... ] }`
    - WS `/ws`：WebSocket 握手地址
  - WebSocket 握手参数
    - `room`：房间名（默认 manbo）
    - `u`：昵称（默认 匿名）
  - 消息类型
    - `system`：系统提示（加入/离开、功能回执）
    - `chat`：用户聊天消息
    - `roster`：在线用户列表（加入/离开时广播）

## 内网穿透与反向代理建议
- 对外公开建议统一映射后端端口：
  - HTTP：映射到公网 80 或自定义端口（例如 8888）
  - WS：
    - 与 HTTP 共端口：ws://你的域名:80/ws
    - 独立端口：ws://你的域名:8899/ws（需在启动时设置 WS_PORT）
- 反向代理需正确透传 WebSocket 握手头：`Upgrade: websocket`、`Connection: Upgrade`、`Host` 等，否则握手失败
- 若使用 HTTPS 页面（https://），必须使用 `wss://` 进行 WebSocket 连接，浏览器会阻止 `ws://`（混合内容）

## 常见问题与排查
- 端口被占用（WinError 10048）
  - 使用 `netstat -ano | findstr :端口` 查占用进程，`Stop-Process -Id <PID> -Force` 释放端口
- 混合内容阻止（HTTPS 页面 + ws://）
  - 使用 `wss://` 或在登录页/配置中只提供 wss 地址，确保服务端开启 TLS（HTTPS/WSS）
- 无法连接 WebSocket
  - 检查代理是否支持 WebSocket Upgrade，确认公网穿透地址与端口正确

## 开发计划与关键步骤（指导后续开发）
1) 功能指令实现（@曼波/@音乐一下/@电影/@天气/@新闻/@小视频）
   - 在后端接收包含这些标签的消息时，调用对应服务（可通过 HTTP API/第三方服务）
   - 将结果通过系统消息推送到房间
2) 历史记录与持久化
   - 设计消息存储（SQLite/PostgreSQL/文件）
   - 增加“历史记录查看”入口与分页加载
3) 用户认证与房间管理
   - 登录鉴权（简单口令→JWT）
   - 支持多房间创建/加入、房间权限控制
4) 前端增强
   - Emoji 面板优化、消息富文本展示
   - 在线用户列表交互（私聊入口、@ 提示）
   - 发送状态与重试机制
5) 部署与安全
   - 启用 HTTPS/WSS（证书管理）
   - 生产配置（日志、限流、CORS 策略）

## 维护与扩展
- 新增/修改服务器地址：编辑 <mcfile name="config.json" path="d:\software\Trae\design\manbo_chat\config.json"></mcfile>
- 调整端口：
  - HTTP：设置环境变量 `PORT`
  - WS：设置环境变量 `WS_PORT`（不设置时与 HTTP 共端口）
- 代码入口与静态目录在 <mcfile name="app.py" path="d:\software\Trae\design\manbo_chat\app.py"></mcfile> 中的 `make_app` 设置，模板与静态资源分别位于 `templates/` 与 `static/`

如需我将 config.json 更新为你的最终公网地址或输出一份部署示例（ngrok/caddy/nginx 配置），告诉我具体域名与端口，我会补充示例配置与操作步骤。