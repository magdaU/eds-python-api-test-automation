BODY_PREVIEW_CHARS = 200


def describe_response(response):
    """Status, URL and the start of the body: what a failing assertion on a response shows."""
    return (
        f"status {response.status_code} from {response.url}: {response.text[:BODY_PREVIEW_CHARS]}"
    )


def assert_bad_request_mentioning(response, word):
    """The API rejected the request (400) and its message names what was wrong."""
    assert response.status_code == 400, describe_response(response)
    assert word in response.text.lower(), describe_response(response)


def assert_bad_request_naming_parameter(response, parameter):
    """The API rejected the request (400) and lists `parameter` among its errors."""
    assert response.status_code == 400, describe_response(response)
    assert parameter in response.json()["errors"], describe_response(response)


def assert_no_records(response):
    """The API answered successfully, with an empty page."""
    assert response.status_code == 200, describe_response(response)
    assert response.json()["records"] == [], describe_response(response)
