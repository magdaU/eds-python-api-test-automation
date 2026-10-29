Feature: Querying a dataset
  As a tester of the EDS API client
  I want query parameters to reach the API exactly as I give them
  So that the API returns the records I asked for

  Scenario: Asking for a page of records
    Given the CO2Emis dataset answers with an empty result
    When I get the dataset with limit 5 and offset 10
    Then the request carries limit "5" and offset "10"

  Scenario Outline: A sort expression is sent unchanged
    Given the DayAheadPrices dataset answers with an empty result
    When I get the dataset sorted by "<sort>"
    Then the request carries sort "<sort>"

    Examples:
      | sort                             |
      | DayAheadPriceDKK                     |
      | DayAheadPriceDKK desc                |
      | PriceArea asc, DayAheadPriceDKK desc |

  Scenario: Filtering by price area
    Given the DayAheadPrices dataset answers with an empty result
    When I get the dataset filtered by price area "DK1"
    Then the request carries the filter '{"PriceArea":"DK1"}'

  Scenario: A negative limit is refused before anything is sent
    Given the CO2Emis dataset answers with an empty result
    When I get the dataset with limit -1
    Then the client refuses the request and names the limit
    And no request was sent
