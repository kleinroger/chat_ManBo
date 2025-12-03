# ManBo Chat 开发日志（DEVLOG）

用于实时记录后续开发过程的关键事件、帮助信息、提示词等内容。建议团队在每次变更或调试后更新此日志，便于追踪问题与复现操作。

## 使用说明
- 记录格式建议：
  - 日期时间（本地时区）
  - 分类标签：feature/fix/config/deploy/doc/ops/note/idea/tip
  - 模块：backend/frontend/login/chat/config/deploy
  - 事件与操作摘要（包含关键命令、主要修改点、影响面）
  - 关联文件与端口（如 app.py、config.json、HTTP:8888、WS:8899）
  - 验证方式（访问地址、预览链接、日志输出、浏览器控制台）
  - 后续动作或 TODO

- 示例模板：
  - 日期时间：2025-12-03 14:00
  - 标签：feature
  - 模块：backend
  - 事件：新增 WS 独立端口支持（WS_PORT）
  - 修改：app.py 增加 ws_port 设置，主程序读取环境变量 WS_PORT，同时监听两个端口
  - 端口：HTTP 8888；WS 8899
  - 验证：启动日志打印 HTTP/WS 地址；登录页连接成功
  - 文件：app.py
  - TODO：更新 config.json 中的默认 ws 地址为 ws://localhost:8899/ws

## 初始化条目（当前状态）
- 日期时间：2025-12-03
  - 标签：doc
  - 模块：project
  - 事件：新增 README.md（项目概述、启动方法、配置方式、内网穿透建议、开发计划）
  - 文件：README.md

- 日期时间：2025-12-03
  - 标签：config
  - 模块：frontend
  - 事件：精简服务器列表，仅保留两个地址（本地与公网1）
  - 文件：config.json（servers：ws://localhost:8888/ws，ws://1run6ce7oa69.ngrok.xiaomiqiu123.top/ws）

- 日期时间：2025-12-03
  - 标签：feature
  - 模块：frontend/login
  - 事件：登录页下拉显示友好名称（本地服务器/公共服务器1），按协议过滤与主机名去重，优先 wss
  - 文件：static/js/login.js
  - 验证：预览 http://localhost:8887/templates/login.html

- 日期时间：2025-12-03
  - 标签：fix
  - 模块：frontend/chat
  - 事件：在 HTTPS 页面自动将 ws:// 升级为 wss://，并增加 WebSocket 错误提示
  - 文件：static/js/chat.js
  - 说明：避免混合内容导致的连接失败；错误信息更清晰

- 日期时间：2025-12-03
  - 标签：feature
  - 模块：backend
  - 事件：支持 WS 独立端口；读取 WS_PORT 环境变量（默认与 HTTP 共端口）
  - 文件：app.py
  - 端口：HTTP 8888；WS 8899（示例）
  - 启动日志：
    - ManBo Chatroom HTTP running at http://localhost:8888/
    - ManBo Chatroom WS running at ws://localhost:8899/ws

- 日期时间：2025-12-03
  - 标签：ops
  - 模块：runtime
  - 事件：处理端口占用（WinError 10048），释放占用进程后重新启动后端
  - 命令：netstat -ano | findstr :8888；Stop-Process -Id <PID> -Force

- 日期时间：2025-12-03
  - 标签：ui
  - 模块：frontend/chat
  - 事件：移除 🎵 emoji，仅保留 😀 😂 👍；更新小字提示内容
  - 文件：templates/chat.html

## 后续计划与 TODO（建议按需更新）
- 功能指令实现：@曼波/@音乐一下/@电影/@天气/@新闻/@小视频 → 后端路由或第三方 API；系统消息回执优化
- 历史记录与持久化：引入数据库（SQLite/PG），查询接口与前端分页展示
- 用户认证与多房间：登录鉴权（口令→JWT），房间管理与权限控制
- 前端增强：Emoji 面板与富文本、在线用户交互（私聊、@ 提示）、发送状态与重试
- 部署与安全：HTTPS/WSS、证书管理、日志与限流、CORS 策略
- 配置统一化：将 config.json 与环境变量（PORT/WS_PORT）组合为环境配置方案

## 备注
- 在 HTTPS 页面必须使用 wss:// 连接，否则浏览器会阻止混合内容
- 反向代理需透传 WebSocket 头（Upgrade/Connection/Host），否则握手失败
- 变更后建议更新本日志，以便复盘与问题定位