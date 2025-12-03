import os
import tornado.ioloop
import tornado.web

class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("新项目已运行")

class HealthHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("ok")

def make_app(port=9000):
    return tornado.web.Application(
        [
            (r"/", RootHandler),
            (r"/health", HealthHandler),
        ],
        debug=True,
    )

if __name__ == "__main__":
    port = int(os.environ.get("NEW_PORT", "9000"))
    app = make_app(port=port)
    app.listen(port)
    print(f"New Project HTTP running at http://localhost:{port}/")
    tornado.ioloop.IOLoop.current().start()
