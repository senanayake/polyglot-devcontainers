package dev.polyglot.maintenance;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import org.apache.commons.lang3.StringUtils;

public final class DependencyPlanSummary {
  private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();
  private static final List<String> SEVERITY_ORDER = List.of("critical", "high", "medium", "low");

  private DependencyPlanSummary() {}

  public static DependencyFinding fromJson(String json) throws JsonProcessingException {
    return OBJECT_MAPPER.readValue(json, DependencyFinding.class);
  }

  public static Map<String, Long> summarizeBySeverity(List<DependencyFinding> findings) {
    Map<String, Long> counts = new LinkedHashMap<>();
    for (String severity : SEVERITY_ORDER) {
      counts.put(
          severity,
          findings.stream().filter(finding -> severity.equals(finding.severity())).count());
    }
    return counts;
  }

  public static String renderHeadline(String projectName, List<DependencyFinding> findings) {
    List<String> parts = new ArrayList<>();
    for (Map.Entry<String, Long> entry : summarizeBySeverity(findings).entrySet()) {
      if (entry.getValue() > 0) {
        parts.add(entry.getKey() + "=" + entry.getValue());
      }
    }
    if (parts.isEmpty()) {
      return projectName + ": no findings";
    }
    return projectName + ": " + StringUtils.join(parts, ", ");
  }

  public static List<String> collectFixVersions(List<DependencyFinding> findings) {
    return findings.stream()
        .flatMap(finding -> finding.fixedVersions().stream())
        .distinct()
        .sorted()
        .collect(Collectors.toList());
  }
}
