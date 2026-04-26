Feature: backend addition helper
  The Python backend keeps a small executable specification for agent-friendly
  behavior discovery.

  @acceptance
  Scenario: add two integers
    Given the backend numbers 2 and 3
    When the backend numbers are added
    Then the backend result is 5
