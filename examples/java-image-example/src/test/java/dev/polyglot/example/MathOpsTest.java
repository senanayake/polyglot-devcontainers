package dev.polyglot.example;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class MathOpsTest {
  @Test
  void addsTwoNumbers() {
    assertEquals(5, MathOps.add(2, 3));
  }
}
