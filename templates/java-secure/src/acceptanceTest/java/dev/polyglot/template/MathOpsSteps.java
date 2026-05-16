package dev.polyglot.template;

import static org.junit.jupiter.api.Assertions.assertEquals;

import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;

public class MathOpsSteps {
  private int left;
  private int right;
  private int result;

  @Given("the integers {int} and {int}")
  public void theIntegersAnd(int left, int right) {
    this.left = left;
    this.right = right;
  }

  @When("the numbers are added")
  public void theNumbersAreAdded() {
    result = MathOps.add(left, right);
  }

  @Then("the result is {int}")
  public void theResultIs(int expected) {
    assertEquals(expected, result);
  }
}
