import json
import tornado.httpclient
import tornado.ioloop

async def handle(self, text, broadcast, APP_CONFIG):
    if "@随机头像" not in text:
        return False
    try:
        client = tornado.httpclient.AsyncHTTPClient()
        url = "https://v2.xxapi.cn/api/head"
        req = tornado.httpclient.HTTPRequest(
            url=url,
            method="GET",
            headers={"User-Agent": "xiaoxiaoapi/1.0.0"},
            request_timeout=8,
        )
        resp = await client.fetch(req, raise_error=False)
        if resp.code != 200:
            tip = {
                "type": "system",
                "room": self.room,
                "text": "@随机头像 接口暂不可用",
                "ts": tornado.ioloop.IOLoop.current().time(),
            }
            broadcast(self.room, tip)
            return True
        data = json.loads(resp.body.decode("utf-8", errors="ignore"))
        img = data.get("data") if isinstance(data, dict) else None
        if not img:
            tip = {
                "type": "system",
                "room": self.room,
                "text": "@随机头像 返回数据异常",
                "ts": tornado.ioloop.IOLoop.current().time(),
            }
            broadcast(self.room, tip)
            return True
        msg = {
            "type": "avatar",
            "room": self.room,
            "user": self.username,
            "data": {"url": img},
            "ts": tornado.ioloop.IOLoop.current().time(),
        }
        broadcast(self.room, msg)
        return True
    except Exception as e:
        tip = {
            "type": "system",
            "room": self.room,
            "text": "@随机头像 请求失败",
            "ts": tornado.ioloop.IOLoop.current().time(),
        }
        broadcast(self.room, tip)
        return True
