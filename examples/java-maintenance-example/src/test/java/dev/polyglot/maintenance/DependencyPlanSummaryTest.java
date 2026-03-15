package dev.polyglot.maintenance;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.fasterxml.jackson.core.JsonProcessingException;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class DependencyPlanSummaryTest {
  private static List<DependencyFinding> sampleFindings() {
    return List.of(
        new DependencyFinding(
            "jackson-databind",
            "high",
            "2.17.2",
            List.of("2.18.4"),
            "GHSA-example-jackson",
            "Upgrade the JSON parsing dependency."),
        new DependencyFinding(
            "commons-lang3",
            "medium",
            "3.14.0",
            List.of("3.17.0"),
            "GHSA-example-commons",
            "Upgrade the utility dependency."),
        new DependencyFinding(
            "slf4j-simple",
            "medium",
            "2.0.16",
            List.of("2.0.17"),
            "GHSA-example-slf4j",
            "Refresh the logging dependency."));
  }

  @Test
  void summarizeBySeverityCountsKnownFindings() {
    assertEquals(
        Map.of("critical", 0L, "high", 1L, "medium", 2L, "low", 0L),
        DependencyPlanSummary.summarizeBySeverity(sampleFindings()));
  }

  @Test
  void renderHeadlineUsesOrderedSeverityCounts() {
    assertEquals(
        "java-maintenance-example: high=1, medium=2",
        DependencyPlanSummary.renderHeadline("java-maintenance-example", sampleFindings()));
  }

  @Test
  void collectFixVersionsReturnsDistinctSortedValues() {
    assertEquals(
        List.of("2.0.17", "2.18.4", "3.17.0"),
        DependencyPlanSummary.collectFixVersions(sampleFindings()));
  }

  @Test
  void fromJsonParsesDependencyFindingPayload() throws JsonProcessingException {
    String json =
        """
                {
                  "packageName": "jackson-databind",
                  "severity": "high",
                  "currentVersion": "2.17.2",
                  "fixedVersions": ["2.18.4"],
                  "advisoryId": "GHSA-example-jackson",
                  "summary": "Upgrade the JSON parsing dependency."
                }
                """;

    DependencyFinding finding = DependencyPlanSummary.fromJson(json);

    assertEquals("jackson-databind", finding.packageName());
    assertEquals(List.of("2.18.4"), finding.fixedVersions());
  }
}
