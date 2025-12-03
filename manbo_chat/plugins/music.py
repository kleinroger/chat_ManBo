import json
import os
import tornado.httpclient
import tornado.ioloop

async def handle(self, text, broadcast, APP_CONFIG):
    if "@音乐一下" not in text:
        return False
    try:
        from urllib.parse import urlencode
        client = tornado.httpclient.AsyncHTTPClient()
        base = "https://api.qqsuu.cn/api/dm-randmusic"
        params = {"format": "json"}
        api_key = os.environ.get("QQSUU_API_KEY")
        if api_key:
            params["key"] = api_key
        url = f"{base}?{urlencode(params)}"
        req = tornado.httpclient.HTTPRequest(
            url=url,
            method="GET",
            headers={"User-Agent": "manbo-chat/1.0"},
            request_timeout=8,
        )
        resp = await client.fetch(req, raise_error=False)
        if resp.code != 200:
            tip = {
                "type": "system",
                "room": self.room,
                "text": f"@音乐一下 接口暂不可用：HTTP {resp.code}",
                "ts": tornado.ioloop.IOLoop.current().time(),
            }
            broadcast(self.room, tip)
            return True
        data = json.loads(resp.body.decode("utf-8", errors="ignore"))
        if isinstance(data, dict) and int(data.get("code", 0)) == 1 and isinstance(data.get("data"), dict):
            d = data["data"]
            music_msg = {
                "type": "music",
                "room": self.room,
                "user": self.username,
                "data": {
                    "name": d.get("name") or "未知歌曲",
                    "url": d.get("url") or "",
                    "singer": d.get("singer") or "",
                    "image": d.get("picurl") or d.get("image") or "",
                },
                "ts": tornado.ioloop.IOLoop.current().time(),
            }
            broadcast(self.room, music_msg)
        else:
            tip = {
                "type": "system",
                "room": self.room,
                "text": f"@音乐一下 接口暂不可用：{data.get('msg', '未知错误')}",
                "ts": tornado.ioloop.IOLoop.current().time(),
            }
            broadcast(self.room, tip)
        return True
    except Exception as e:
        tip = {
            "type": "system",
            "room": self.room,
            "text": f"@音乐一下 请求失败：{str(e)[:120]}",
            "ts": tornado.ioloop.IOLoop.current().time(),
        }
        broadcast(self.room, tip)
        return True
