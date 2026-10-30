Feature: Resilience when the API misbehaves
  As a tester of the EDS API client
  I want the client to retry only what is worth retrying, and to say what it does
  So that a throttled or failing API neither hangs nor is hammered

  Scenario: The client waits as long as a throttling server asks
    Given an API that answers 429 with "Retry-After: 2" and then 200
    When I get a dataset
    Then the client waited 2 seconds before it retried
    And the response status is 200

  Scenario: The client refuses to wait much longer than it allows
    Given an API that answers 429 with "Retry-After: 300" and then 200
    When I get a dataset
    Then the request fails because the server asked for a longer wait than allowed
    And the client did not wait

  Scenario: The client gives up when the API keeps failing
    Given an API that always answers 503
    When I get a dataset
    Then the request fails with a retry error after 3 attempts

  Scenario Outline: Client errors are not retried
    Given an API that always answers <status>
    When I get a dataset
    Then the response status is <status>
    And the API received 1 request

    Examples:
      | status |
      | 400    |
      | 401    |
      | 404    |
