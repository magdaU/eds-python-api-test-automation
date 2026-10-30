import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from client.dataset_api import DatasetApi
from client.eds_client import EDSApiClient, RetryConfig


class ScriptedServer:
    """Answers each request with the next scripted status; the last one repeats.

    `headers` is one dict for every response, or a list with one dict per response (the last one repeats).
    `delay` is how many seconds the server waits before it answers.
    """

    def __init__(self, statuses, headers=None, delay=0):
        self.statuses = statuses
        self.delay = delay
        self.headers = headers or {}
        self.request_count = 0
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                index = min(outer.request_count, len(outer.statuses) - 1)
                outer.request_count += 1
                if outer.delay:
                    time.sleep(outer.delay)
                body = json.dumps({"records": [], "total": 0}).encode()
                self.send_response(outer.statuses[index])
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                headers = outer.headers[min(index, len(outer.headers) - 1)] if isinstance(outer.headers, list) else outer.headers
                for name, value in headers.items():
                    self.send_header(name, value)
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


def client_for(server, max_retries=2, **retry_options):
    retry = RetryConfig(max_retries=max_retries, backoff_factor=0, **retry_options)
    return EDSApiClient(base_url=server.url, retry=retry)


def api_for(server, max_retries=2, **retry_options):
    return DatasetApi(client_for(server, max_retries, **retry_options), "CO2Emis")
