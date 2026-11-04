def assert_bad_request_mentioning(response, word):
    """The API rejected the request (400) and its message names what was wrong."""
    assert response.status_code == 400
    assert word in response.text.lower()


def assert_bad_request_naming_parameter(response, parameter):
    """The API rejected the request (400) and lists `parameter` among its errors."""
    assert response.status_code == 400
    assert parameter in response.json()["errors"]


def assert_no_records(response):
    """The API answered successfully, with an empty page."""
    assert response.status_code == 200
    assert response.json()["records"] == []
