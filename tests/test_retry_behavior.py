import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests

from client.dataset_api import DatasetApi
from client.eds_client import EDSApiClient
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "Retry behavior")

# Unlike requests_mock, a real local HTTP server sends the requests through the
# client's own HTTPAdapter/Retry, so the retry behavior itself is exercised.


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


@pytest.fixture
def scripted_server():
    servers = []

    def start(*statuses):
        server = ScriptedServer(list(statuses))
        servers.append(server)
        return server

    yield start
    for server in servers:
        server.close()


def api_for(server, max_retries=2):
    client = EDSApiClient(base_url=server.url, max_retries=max_retries, backoff_factor=0)
    return DatasetApi(client, "CO2Emis")


@pytest.mark.parametrize("failing_statuses", [(503, 503), (429,)])
def test_givenTransientFailuresWithinRetryBudget_whenGettingDataset_thenFinalSuccessIsReturned(scripted_server, failing_statuses):
    # arrange
    server = scripted_server(*failing_statuses, 200)

    # act
    response = api_for(server).get()

    # assert
    assert response.status_code == 200
    assert server.request_count == len(failing_statuses) + 1


def test_givenPersistentServerError_whenGettingDataset_thenRetriesStopAfterMaxRetries(scripted_server):
    # arrange
    server = scripted_server(503)

    # act / assert
    with pytest.raises(requests.exceptions.RetryError):
        api_for(server, max_retries=2).get()
    assert server.request_count == 3


@pytest.mark.parametrize("status", [400, 404])
def test_givenClientError_whenGettingDataset_thenItIsNotRetried(scripted_server, status):
    # arrange
    server = scripted_server(status)

    # act
    response = api_for(server).get()

    # assert
    assert response.status_code == status
    assert server.request_count == 1


def test_givenZeroMaxRetries_whenServerFails_thenNoRetryIsMade(scripted_server):
    # arrange
    server = scripted_server(503)

    # act / assert
    with pytest.raises(requests.exceptions.RetryError):
        api_for(server, max_retries=0).get()
    assert server.request_count == 1
