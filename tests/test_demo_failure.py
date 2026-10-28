"""DEMO ONLY: a live test that fails on purpose, so the Allure report shows a real entry in Categories and Categories trend.

It asks the API for a dataset that does not exist and wrongly expects success. Remove this file (revert the commit that
added it) as soon as the report has been published and looked at; while it is on `main`, the full run and the nightly
live run are red on purpose.
"""

import pytest

import allure

pytestmark = [pytest.mark.live, allure.epic("Live API")]


@allure.feature("Demo")
def test_givenUnknownDataset_whenGettingIt_thenDemoExpectsSuccessAndFailsOnPurpose(eds_client):
    # act
    response = eds_client.get_dataset("NotARealDataset")

    # assert
    assert response.status_code == 200, "DEMO: this failure is deliberate, to show Categories and Categories trend"
