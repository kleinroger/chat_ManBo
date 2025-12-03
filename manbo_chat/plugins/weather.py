import json
import os
import tornado.httpclient
import tornado.ioloop

async def handle(self, text, broadcast, APP_CONFIG):
    if "@天气" not in text:
        return False
    try:
        city = text.split("@天气", 1)[1].strip()
        if not city:
            tip = {
                "type": "system",
                "room": self.room,
                "text": "@天气 用法：@天气 城市名（例如：@天气 蓬莱）",
                "ts": tornado.ioloop.IOLoop.current().time(),
            }
            broadcast(self.room, tip)
            return True
        from urllib.parse import urlencode
        client = tornado.httpclient.AsyncHTTPClient()
        cfg = APP_CONFIG.get("weather") if isinstance(APP_CONFIG, dict) else None
        base = (os.environ.get("XXAPI_URL") or (cfg.get("api_url") if isinstance(cfg, dict) else None) or "https://v2.xxapi.cn/api/weatherDetails")
        params = {"city": city}
        api_key = (os.environ.get("XXAPI_KEY") or (cfg.get("api_key") if isinstance(cfg, dict) else None))
        if api_key:
            params["key"] = api_key
        url = f"{base}?{urlencode(params)}"
        req = tornado.httpclient.HTTPRequest(
            url=url,
            method="GET",
            headers={"User-Agent": "xiaoxiaoapi/1.0.0"},
            request_timeout=10,
        )
        resp = await client.fetch(req, raise_error=False)
        if resp.code != 200:
            tip = {
                "type": "system",
                "room": self.room,
                "text": f"@天气 接口暂不可用：HTTP {resp.code}",
                "ts": tornado.ioloop.IOLoop.current().time(),
            }
            broadcast(self.room, tip)
            return True
        raw = json.loads(resp.body.decode("utf-8", errors="ignore"))
        code = int(raw.get("code", -1)) if isinstance(raw, dict) else -1
        if code == -8:
            tip = {
                "type": "system",
                "room": self.room,
                "text": "@天气 接口不可用：请携带 Key",
                "ts": tornado.ioloop.IOLoop.current().time(),
            }
            broadcast(self.room, tip)
            return True
        ok_codes = {1, 200, 0}
        if not isinstance(raw, dict) or int(raw.get("code", -1)) not in ok_codes:
            tip = {
                "type": "system",
                "room": self.room,
                "text": f"@天气 查询失败：{raw.get('msg','未知错误') if isinstance(raw, dict) else '响应异常'}",
                "ts": tornado.ioloop.IOLoop.current().time(),
            }
            broadcast(self.room, tip)
            return True
        payload = raw.get("data")
        if not isinstance(payload, dict):
            tip = {
                "type": "system",
                "room": self.room,
                "text": "@天气 返回数据格式异常",
                "ts": tornado.ioloop.IOLoop.current().time(),
            }
            broadcast(self.room, tip)
            return True
        city_name = payload.get("city") or payload.get("area") or payload.get("address") or city
        first = None
        try:
            arr = payload.get("data")
            if isinstance(arr, list) and arr:
                first = arr[0]
        except Exception:
            first = None
        cond = (first or {}).get("weather") or payload.get("weather") or payload.get("type") or ""
        temp = (first or {}).get("temperature") or payload.get("temperature") or payload.get("wendu") or ""
        wind = (first or {}).get("wind") or payload.get("wind") or payload.get("fengxiang") or ""
        aqi = (first or {}).get("air_quality") or payload.get("air_quality") or payload.get("aqi") or ""
        high = payload.get("tempmax") or payload.get("temphigh") or payload.get("high") or ""
        low = payload.get("tempmin") or payload.get("templow") or payload.get("low") or ""
        humidity = payload.get("humidity") or payload.get("shidu") or ""
        tips = payload.get("tips") or payload.get("ps") or payload.get("ganmao") or ""
        update_time = payload.get("update_time") or payload.get("time") or payload.get("reporttime") or ""
        weather_msg = {
            "type": "weather",
            "room": self.room,
            "user": self.username,
            "data": {
                "city": city_name,
                "cond": cond,
                "temp": temp,
                "high": high,
                "low": low,
                "humidity": humidity,
                "wind": wind,
                "aqi": aqi,
                "tips": tips,
                "update_time": update_time
            },
            "ts": tornado.ioloop.IOLoop.current().time(),
        }
        broadcast(self.room, weather_msg)
        return True
    except Exception as e:
        tip = {
            "type": "system",
            "room": self.room,
            "text": f"@天气 请求失败：{str(e)[:120]}",
            "ts": tornado.ioloop.IOLoop.current().time(),
        }
        broadcast(self.room, tip)
        return True
