import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _CapturingRequestHandler(BaseHTTPRequestHandler):
    def _handle(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""
        self.server.received.append({"path": self.path, "headers": dict(self.headers), "body": body})
        self.send_response(self.server.response_status)
        self.end_headers()

    do_POST = _handle
    do_GET = _handle

    def log_message(self, *args):
        pass


class LocalAppriseWebhook:
    def __init__(self, response_status=200):
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _CapturingRequestHandler)
        self._server.received = []
        self._server.response_status = response_status
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc_info):
        self._server.shutdown()
        self._server.server_close()

    @property
    def requests(self):
        return self._server.received

    def url(self, path="/hook", scheme="json"):
        host, port = self._server.server_address[:2]
        return f"{scheme}://{host}:{port}{path}"
