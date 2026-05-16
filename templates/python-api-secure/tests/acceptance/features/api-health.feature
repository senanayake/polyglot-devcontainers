Feature: API health endpoints
  The starter should demonstrate a small but traceable executable specification.

  @acceptance
  Scenario: health endpoint reports readiness
    Given an API test client
    When the health endpoint is requested
    Then the response status code is 200
    And the response payload contains the status "healthy"
