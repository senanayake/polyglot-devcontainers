---
id: KB-YYYY-NNN
type: failure-mode
status: draft
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: []
related: []
---

# [Title: Failure Mode Name]

## Context

Why understanding this failure mode matters.

## System/Component

What system or component exhibits this failure mode?

## Failure Description

### Symptoms

Observable signs of failure:
- Symptom 1
- Symptom 2
- Symptom 3

### Failure Scenario

Conditions that trigger the failure:
- Trigger condition 1
- Trigger condition 2
- Trigger condition 3

### Impact

Consequences of the failure:
- Impact on system
- Impact on users
- Impact on data
- Impact on operations

## Root Cause

### Primary Cause

Fundamental reason for the failure.

### Contributing Factors

Additional factors that enable or worsen the failure:
- Factor 1
- Factor 2
- Factor 3

### Failure Mechanism

How the failure propagates through the system:
```
Initial condition → intermediate state → failure state
```

## Evidence

Data demonstrating this failure mode:
- Incident reports
- Test results
- Logs
- Metrics

## Reproduction

### Minimal Reproduction Case

Simplest way to trigger the failure:
```
[Steps or code to reproduce]
```

### Conditions Required

Prerequisites for reproduction:
- Condition 1
- Condition 2
- Condition 3

## Prevention

### Design Changes

Architectural changes to prevent the failure:
- Change 1
- Change 2
- Change 3

### Operational Controls

Operational practices to avoid the failure:
- Control 1
- Control 2
- Control 3

### Monitoring

How to detect conditions that lead to failure:
- Metric to monitor
- Alert threshold
- Response procedure

## Detection

### Early Warning Signs

Indicators that failure is imminent:
- Warning sign 1
- Warning sign 2
- Warning sign 3

### Detection Methods

How to identify the failure:
- Automated detection
- Manual inspection
- User reports

## Mitigation

### Immediate Response

What to do when failure occurs:
1. Step 1
2. Step 2
3. Step 3

### Recovery Procedure

How to recover from the failure:
1. Step 1
2. Step 2
3. Step 3

### Graceful Degradation

How to limit impact:
- Degradation strategy 1
- Degradation strategy 2

## Testing

### Test Cases

Tests that verify prevention/detection:
```
[Test code or procedure]
```

### Chaos Engineering

How to test resilience:
- Failure injection method
- Expected behavior
- Recovery validation

## Related Failure Modes

Similar or cascading failures:
- Related failure 1
- Related failure 2
- Cascading effect to failure 3

## Lessons Learned

Key insights from this failure mode:
- Lesson 1
- Lesson 2
- Lesson 3

## Applicability

### ✅ This Failure Mode Applies To

- System/component 1
- System/component 2
- Scenario 1
- Scenario 2

### ❌ This Failure Mode Does Not Apply To

- System/component 1
- System/component 2
- Scenario 1
- Scenario 2

## Status

Current state of this failure mode:
- [ ] Documented
- [ ] Prevention implemented
- [ ] Detection implemented
- [ ] Mitigation tested
- [ ] Monitoring in place

## Related Knowledge

- Related K-Briefs
- Incident reports
- ADRs
- Documentation
