import os
import tornado.ioloop
import tornado.httpclient
import tornado.escape

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

async def stream_manbo(self, user, prompt, broadcast, APP_CONFIG):
    import uuid, time
    sid = str(uuid.uuid4())
    ts = int(time.time()*1000)
    broadcast(self.room, {"type":"ai_stream","id":sid,"delta":"","ts":ts})
    try:
        from tornado.httpclient import AsyncHTTPClient, HTTPRequest
        client = AsyncHTTPClient()
        cfg = APP_CONFIG.get("ai") if isinstance(APP_CONFIG, dict) else None
        api_key = (os.environ.get('SILICONFLOW_API_KEY','').strip() or (cfg.get('api_key','').strip() if isinstance(cfg, dict) else ''))
        api_url = (os.environ.get('SILICONFLOW_API_URL','').strip() or (cfg.get('api_url','').strip() if isinstance(cfg, dict) else 'https://api.siliconflow.cn/v1/'))
        model = (os.environ.get('SILICONFLOW_MODEL','').strip() or (cfg.get('model_name','').strip() if isinstance(cfg, dict) else 'Qwen/Qwen2.5-7B-Instruct'))
        if not api_key:
            broadcast(self.room, {"type":"ai_stream","id":sid,"delta":"[未配置 SILICONFLOW_API_KEY]","ts":int(time.time()*1000)})
            return
        body = {
            "model": model,
            "messages":[
                {"role":"system","content": MAMBO_SYSTEM_PROMPT},
                {"role":"system","content": f"当前用户昵称为：{user}"},
                {"role":"user","content": prompt}
            ],
            "stream":True,
            "max_tokens":2048,
            "temperature":0.7
        }
        req = HTTPRequest(
            url=f"{api_url.rstrip('/')}/chat/completions",
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":"application/json"
            },
            body=tornado.escape.json_encode(body),
            request_timeout=30
        )
        res = await client.fetch(req, raise_error=False)
        if res.code != 200:
            broadcast(self.room, {"type":"ai_stream","id":sid,"delta":"[后端接口异常，请稍后再试]","ts":int(time.time()*1000)})
        else:
            for line in res.body.decode('utf-8').splitlines():
                line = line.strip()
                if line.startswith('data: '):
                    chunk = line[6:]
                    if chunk == '[DONE]':
                        break
                    try:
                        obj = tornado.escape.json_decode(chunk)
                        delta = obj.get('choices',[{}])[0].get('delta',{}).get('content','')
                        if delta:
                            broadcast(self.room, {"type":"ai_stream","id":sid,"delta":delta,"ts":int(time.time()*1000)})
                    except:
                        pass
    except Exception:
        broadcast(self.room, {"type":"ai_stream","id":sid,"delta":"[后端调用异常，请稍后再试]","ts":int(time.time()*1000)})
    finally:
        broadcast(self.room, {"type":"ai_stream_end","id":sid,"ts":int(time.time()*1000)})

async def handle(self, text, broadcast, APP_CONFIG):
    if "@曼波" not in text:
        return False
    prompt = text.replace("@曼波", "").strip()
    if not prompt:
        tip = {
            "type": "system",
            "room": self.room,
            "text": "@曼波 用法：@曼波 你的问题",
            "ts": tornado.ioloop.IOLoop.current().time(),
        }
        broadcast(self.room, tip)
        return True
    tornado.ioloop.IOLoop.current().spawn_callback(stream_manbo, self, self.username, prompt, broadcast, APP_CONFIG)
    return True
