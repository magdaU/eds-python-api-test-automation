import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from client.dataset_api import DatasetApi
from client.eds_client import EDSApiClient


class ScriptedServer:
    """Answers each request with the next scripted status; the last one repeats."""

    def __init__(self, statuses):
        self.statuses = statuses
        self.request_count = 0
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                index = min(outer.request_count, len(outer.statuses) - 1)
                outer.request_count += 1
                body = json.dumps({"records": [], "total": 0}).encode()
                self.send_response(outer.statuses[index])
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def client_for(server, max_retries=2):
    return EDSApiClient(base_url=server.url, max_retries=max_retries, backoff_factor=0)


def api_for(server, max_retries=2):
    return DatasetApi(client_for(server, max_retries), "CO2Emis")
