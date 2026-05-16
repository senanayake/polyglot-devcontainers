Feature: addition helper
  A small executable specification keeps the starter understandable to both
  humans and AI agents.

  @acceptance
  Scenario: add two integers
    Given the numbers 2 and 3
    When the numbers are added
    Then the result is 5
