"""Files attached to the Allure report of the tests that check the API specification."""

from pathlib import Path

import pytest

import allure

SWAGGER_SCREENSHOT = Path(__file__).parent / "attachments" / "swagger-eds-api.png"


@pytest.fixture
def swagger_screenshot():
    """Attach the Swagger UI of the EDS API (screenshot taken 2026-11-10) to the test report."""
    allure.attach.file(
        str(SWAGGER_SCREENSHOT),
        name="Swagger UI of the EDS API (2026-11-10)",
        attachment_type=allure.attachment_type.PNG,
    )
