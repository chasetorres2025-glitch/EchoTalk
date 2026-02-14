from app import create_app, websocket_app
from config import get_config
import sys

sys.stdout = sys.stderr

config = get_config()
app = create_app()

class WSGIHandler:
    """
    自定义WSGI处理器，同时处理HTTP和WebSocket请求
    """
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        
        if path.startswith('/ws/'):
            ws = environ.get('wsgi.websocket')
            if ws:
                print(f"[WS] WebSocket请求: {path}", file=sys.stderr, flush=True)
                
                if path.startswith('/ws/realtime/'):
                    parts = path.split('/')
                    if len(parts) >= 5:
                        session_id = parts[3]
                        open_id = parts[4]
                        print(f"[WS] session_id={session_id}, open_id={open_id}", file=sys.stderr, flush=True)
                        
                        from app.routes.realtime import handle_websocket
                        with self.app.app_context():
                            handle_websocket(ws, session_id, open_id)
                        return []
        
        return self.app(environ, start_response)

if __name__ == '__main__':
    print(f"Starting EchoTalk Server...", flush=True)
    print(f"Environment: {'development' if config.DEBUG else 'production'}", flush=True)
    print(f"Host: {config.HOST}", flush=True)
    print(f"Port: {config.PORT}", flush=True)
    print(f"MySQL: {config.MYSQL_HOST}:{config.MYSQL_PORT}/{config.MYSQL_DB}", flush=True)
    print(f"MongoDB: {config.MONGO_HOST}:{config.MONGO_PORT}/{config.MONGO_DB}", flush=True)

    from gevent.pywsgi import WSGIServer
    from geventwebsocket.handler import WebSocketHandler
    
    handler = WSGIHandler(app)
    
    server = WSGIServer(
        (config.HOST, config.PORT),
        handler,
        handler_class=WebSocketHandler,
        log=sys.stdout
    )
    print(f"WebSocket server running on ws://{config.HOST}:{config.PORT}", flush=True)
    server.serve_forever()
