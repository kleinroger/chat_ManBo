import json
import tornado.httpclient
import tornado.ioloop

async def handle(self, text, broadcast, APP_CONFIG):
    if "@新闻" not in text:
        return False
    try:
        broadcast(self.room, {
            "type": "system",
            "room": self.room,
            "text": "@新闻 正在查询热点...",
            "ts": tornado.ioloop.IOLoop.current().time(),
        })
        client = tornado.httpclient.AsyncHTTPClient()
        url = "https://v2.xxapi.cn/api/bilibilihot"
        req = tornado.httpclient.HTTPRequest(
            url=url,
            method="GET",
            headers={"User-Agent": "xiaoxiaoapi/1.0.0"},
            request_timeout=5,
        )
        resp = await client.fetch(req, raise_error=False)
        if resp.code != 200:
            tip = {
                "type": "system",
                "room": self.room,
                "text": f"@新闻 接口暂不可用：HTTP {resp.code}",
                "ts": tornado.ioloop.IOLoop.current().time(),
            }
            broadcast(self.room, tip)
            return True
        data = json.loads(resp.body.decode("utf-8", errors="ignore"))
        if not isinstance(data, dict) or int(data.get("code", 0)) != 200 or not isinstance(data.get("data"), list):
            tip = {
                "type": "system",
                "room": self.room,
                "text": f"@新闻 返回数据异常",
                "ts": tornado.ioloop.IOLoop.current().time(),
            }
            broadcast(self.room, tip)
            return True
        items = [str(x) for x in data.get("data", [])][:20]
        news_msg = {
            "type": "news",
            "room": self.room,
            "user": self.username,
            "data": {
                "source": "bilibili",
                "items": items
            },
            "ts": tornado.ioloop.IOLoop.current().time(),
        }
        broadcast(self.room, news_msg)
        return True
    except Exception as e:
        tip = {
            "type": "system",
            "room": self.room,
            "text": f"@新闻 请求失败：{str(e)[:120]}",
            "ts": tornado.ioloop.IOLoop.current().time(),
        }
        broadcast(self.room, tip)
        return True
