Feature: Reading news
  As a tester of the EDS API client
  I want the News parameters to be sent exactly as given
  So that the API can tell categories and dates apart

  Scenario Outline: The category is sent with its exact case
    Given the news API answers with an actual item
    When I ask for the actual news of category "<category>"
    Then the request carries only category "<category>"

    Examples:
      | category |
      | HIGH     |
      | INFO     |

  Scenario: The archive without a date sends no date
    Given the news API answers with an empty archive
    When I ask for the archived news without a date
    Then the request carries no parameters
