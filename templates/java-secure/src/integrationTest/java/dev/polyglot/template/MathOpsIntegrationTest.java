package dev.polyglot.template;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.List;
import org.junit.jupiter.api.Test;

class MathOpsIntegrationTest {
  @Test
  void addsNumbersAcrossARealCollectionBoundary() {
    int total = List.of(2, 3).stream().reduce(0, MathOps::add);
    assertEquals(5, total);
  }
}
