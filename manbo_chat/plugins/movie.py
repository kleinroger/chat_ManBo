import tornado.ioloop

async def handle(self, text, broadcast, APP_CONFIG):
    if "@电影" not in text:
        return False
    import re
    m = re.search(r"@电影\s+\[(https?://[^\]]+)\]", text)
    if not m:
        tip = {
            "type": "system",
            "room": self.room,
            "text": "@电影 用法：@电影 [https://example.com/video.mp4]",
            "ts": tornado.ioloop.IOLoop.current().time(),
        }
        broadcast(self.room, tip)
        return True
    raw_url = m.group(1).strip()
    jx_url = f"https://jx.m3u8.tv/jiexi/?url={raw_url}"
    msg = {
        "type": "movie",
        "room": self.room,
        "user": self.username,
        "data": {"iframe": jx_url, "raw": raw_url},
        "ts": tornado.ioloop.IOLoop.current().time(),
    }
    broadcast(self.room, msg)
    return True
