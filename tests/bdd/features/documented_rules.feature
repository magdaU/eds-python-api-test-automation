Feature: Rules from the EDS API guide
  As a tester of the EDS API client
  I want the requests to follow the rules stated in the guide
  So that the API answers the way the guide describes

  Scenario Outline: Without a limit the client sends no limit, so the API default applies
    Given the <dataset> dataset answers with an empty result
    When I get the dataset without a limit
    Then the request carries no limit

    Examples:
      | dataset         |
      | CO2Emis         |
      | DayAheadPrices  |

  Scenario Outline: A limit of zero is sent unchanged
    Given the <dataset> dataset answers with an empty result
    When I get the dataset with limit 0
    Then the request carries only limit "0"

    Examples:
      | dataset         |
      | CO2Emis         |
      | DayAheadPrices  |

  Scenario Outline: A filter with two values is sent as a JSON array
    Given the <dataset> dataset answers with an empty result
    When I get the dataset filtered by price areas "DK1" and "DK2"
    Then the request carries the filter '{"PriceArea":["DK1","DK2"]}'

    Examples:
      | dataset         |
      | CO2Emis         |
      | DayAheadPrices  |
