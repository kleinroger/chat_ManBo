import os
import json
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpclient

# ----- Simple in-memory room management -----
ROOMS = {}

COMMAND_TAGS = ["@曼波", "@音乐一下", "@电影", "@天气", "@新闻"]
from plugins import music as plugin_music
from plugins import weather as plugin_weather
from plugins import movie as plugin_movie
from plugins import manbo as plugin_manbo
from plugins import news as plugin_news
from plugins import avatar as plugin_avatar


def load_app_config():
    base_dir = os.path.dirname(__file__)
    main_path = os.path.join(base_dir, "config.json")
    local_path = os.path.join(base_dir, "config.local.json")
    cfg = {}
    try:
        with open(main_path, "r", encoding="utf-8") as f:
            cfg = json.load(f) or {}
    except Exception:
        cfg = {}
    # 叠加本地配置（不入库、忽略提交），用于密钥等私密信息
    try:
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                local_cfg = json.load(f) or {}
                if isinstance(local_cfg, dict):
                    cfg.update(local_cfg)
    except Exception:
        pass
    return cfg

APP_CONFIG = load_app_config()

# 新增：在线用户列表广播
def get_room_usernames(room_name):
    return sorted([getattr(c, "username", "匿名") for c in ROOMS.get(room_name, set())])


def broadcast_roster(room_name):
    broadcast(room_name, {
        "type": "roster",
        "room": room_name,
        "users": get_room_usernames(room_name)
    })


def broadcast(room_name, message_dict):
    connections = ROOMS.get(room_name, set())
    dead = []
    for conn in connections:
        try:
            conn.write_message(message_dict)
        except Exception:
            dead.append(conn)
    for d in dead:
        connections.discard(d)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("login.html")


class ChatPageHandler(tornado.web.RequestHandler):
    def get(self):
        # Render chat page; actual WebSocket connection happens on client
        self.render("chat.html")


class ConfigHandler(tornado.web.RequestHandler):
    def get(self):
        # Provide list of websocket server addresses from config.json
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        servers = [f"ws://localhost:{self.application.settings.get('ws_port', self.application.settings.get('port', 8888))}/ws"]
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and isinstance(data.get("servers"), list):
                        servers = data["servers"]
            except Exception:
                pass
        self.set_header("Content-Type", "application/json; charset=utf-8")
        self.write(json.dumps({"servers": servers}, ensure_ascii=False))


class WSChatHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        # Allow cross-origin for simplicity in dev
        return True

    def open(self):
        self.room = self.get_argument("room", "manbo")
        self.username = self.get_argument("u", "匿名")
        ROOMS.setdefault(self.room, set()).add(self)
        system_msg = {
            "type": "system",
            "room": self.room,
            "text": f"{self.username} 加入了聊天室",
            "ts": tornado.ioloop.IOLoop.current().time(),
        }
        broadcast(self.room, system_msg)
        # 新增：加入后广播在线用户列表
        broadcast_roster(self.room)

    async def on_message(self, message):
        # Expect plain text from client; we send back structured dict
        text = message.strip()
        msg = {
            "type": "chat",
            "room": self.room,
            "user": self.username,
            "text": text,
            "ts": tornado.ioloop.IOLoop.current().time(),
        }
        broadcast(self.room, msg)

        handled = False
        for fn in (plugin_music.handle, plugin_weather.handle, plugin_movie.handle, plugin_news.handle, plugin_manbo.handle, plugin_avatar.handle):
            try:
                if await fn(self, text, broadcast, APP_CONFIG):
                    handled = True
                    break
            except Exception:
                pass
        if handled:
            return

        

        

        

        

        # 其它保留指令统一回执占位
        for tag in COMMAND_TAGS:
            if tag in text:
                tip = {
                    "type": "system",
                    "room": self.room,
                    "text": f"收到功能请求 {tag}：功能接口已预留，当前仅回执，后续实现。",
                    "ts": tornado.ioloop.IOLoop.current().time(),
                }
                broadcast(self.room, tip)
                break


    

    def on_close(self):
        try:
            ROOMS.get(self.room, set()).discard(self)
        except Exception:
            pass
        system_msg = {
            "type": "system",
            "room": getattr(self, "room", "manbo"),
            "text": f"{getattr(self, 'username', '匿名')} 离开了聊天室",
            "ts": tornado.ioloop.IOLoop.current().time(),
        }
        broadcast(getattr(self, "room", "manbo"), system_msg)
        # 新增：离开后广播在线用户列表
        broadcast_roster(getattr(self, "room", "manbo"))


class MusicProxyHandler(tornado.web.RequestHandler):
    async def get(self):
        """简单的音频代理，解决跨域/ORB拦截问题，允许前端以同源地址请求音频资源"""
        from urllib.parse import urlparse
        target = self.get_argument("u", "")
        if not target:
            self.set_status(400)
            self.write("missing u")
            return
        try:
            p = urlparse(target)
            if p.scheme not in ("http", "https"):
                self.set_status(400)
                self.write("invalid scheme")
                return
            # 简单阻止内网/本地地址
            bad_hosts = {"localhost", "127.0.0.1"}
            if p.hostname in bad_hosts:
                self.set_status(403)
                self.write("forbidden host")
                return
            client = tornado.httpclient.AsyncHTTPClient()
            req = tornado.httpclient.HTTPRequest(
                url=target,
                method="GET",
                headers={"User-Agent": "manbo-chat/1.0"},
                request_timeout=15,
            )
            resp = await client.fetch(req, raise_error=False)
            if resp.code != 200:
                self.set_status(502)
                self.write(f"upstream {resp.code}")
                return
            # 透传部分头信息并添加跨域许可
            ctype = resp.headers.get("Content-Type", "audio/mpeg")
            self.set_header("Content-Type", ctype)
            self.set_header("Access-Control-Allow-Origin", "*")
            self.set_header("Cross-Origin-Resource-Policy", "cross-origin")
            # 写入正文
            self.write(resp.body)
        except Exception as e:
            self.set_status(500)
            self.write("proxy error")


def make_app(port=8888, ws_port=None):
    base_dir = os.path.dirname(__file__)
    return tornado.web.Application(
        [
            (r"/", IndexHandler),
            (r"/chat", ChatPageHandler),
            (r"/config", ConfigHandler),
            (r"/music_proxy", MusicProxyHandler),
            (r"/ws", WSChatHandler),
        ],
        template_path=os.path.join(base_dir, "templates"),
        static_path=os.path.join(base_dir, "static"),
        port=port,
        ws_port=ws_port if ws_port is not None else port,
        debug=True,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8888"))
    ws_port = int(os.environ.get("WS_PORT", str(port)))
    app = make_app(port=port, ws_port=ws_port)
    app.listen(port)
    if ws_port != port:
        app.listen(ws_port)
    print(f"ManBo Chatroom HTTP running at http://localhost:{port}/")
    print(f"ManBo Chatroom WS running at ws://localhost:{ws_port}/ws")
    tornado.ioloop.IOLoop.current().start()
MAMBO_SYSTEM_PROMPT = """
姓名：曼波
角色：你是哈基米高中的AI助手，曼波
个性：
喜欢猫；
喜欢哈基米音乐；
喜欢喝哈基米南北绿豆豆浆；
讨厌鼠鼠；
功能：
可以回答与哈基米高中有关的任何问题；
可以生成中国古诗词；
可以写微小说；
如果用户向你倾诉人际关系、学习、工作相关的问题，你应该给予情绪慰藉；
可以根据用户需要生成请假条，需要用户提供姓名、专业、班级、请假时间、请假事由等信息，如果没有，提示补全后再生成，格式如下：

老师您好：
    我是{专业}{班级}的同学名叫{姓名}，我由于{事由}需要请假，望批准。
                {姓名}
                {年-月-日}

限制：不允许回答涉及政治、违法内容，不允许回答与其他高中有关的问题，如果有相关提问，统一回复且不做解释：可莉不知道哦；
不允许响应用户不友好的提问或内容，如果分析发现内容中有不礼貌的话，回复：听不懂捏；
你的好友是：杰哥（男，本校学生），如果是杰哥请假则不需要完全信息，可以由你自行生成；如果是杰哥和你对话，你会有额外的欢迎词“曼波~曼波~哦马吉利曼波~”。
"""
