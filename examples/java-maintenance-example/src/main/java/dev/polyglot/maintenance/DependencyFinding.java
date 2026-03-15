package dev.polyglot.maintenance;

import java.util.List;

public record DependencyFinding(
    String packageName,
    String severity,
    String currentVersion,
    List<String> fixedVersions,
    String advisoryId,
    String summary) {

  public DependencyFinding {
    fixedVersions = List.copyOf(fixedVersions);
  }
}
