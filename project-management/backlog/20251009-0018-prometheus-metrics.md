---
story_id: "0018"
title: "Prometheus metrics endpoint"
created: "2025-10-09"
status: "backlog"
dependencies: ["0003"]
estimated_complexity: "medium"
tags: ["observability", "metrics", "phase2"]
---

# Story 0018: Prometheus metrics endpoint

## Description

Add a Prometheus metrics endpoint to expose connection statistics, tool call counts, error rates, and response time metrics for monitoring and analysis.

## Acceptance Criteria

- [ ] Prometheus client library integrated
- [ ] Metrics endpoint exposed (HTTP endpoint for metrics)
- [ ] Connection count metrics (active, total, failed)
- [ ] Tool call count by tool name
- [ ] Error count by error type
- [ ] Response time histogram (p50, p95, p99)
- [ ] Resource and prompt operation metrics
- [ ] Metrics reset on server restart (ephemeral)
- [ ] Documentation for metrics endpoint
- [ ] Example Prometheus configuration

## Technical Notes

**Metrics to expose:**
```
mcp_test_connections_total{transport="streaming-http"} 15
mcp_test_connections_active{transport="streaming-http"} 1
mcp_test_connections_failed_total 2

mcp_test_tool_calls_total{tool_name="add"} 42
mcp_test_tool_calls_total{tool_name="multiply"} 15

mcp_test_errors_total{error_type="timeout"} 3
mcp_test_errors_total{error_type="not_connected"} 7

mcp_test_response_time_seconds{quantile="0.5"} 0.087
mcp_test_response_time_seconds{quantile="0.95"} 0.145
mcp_test_response_time_seconds{quantile="0.99"} 0.234
```

**Implementation approach:**
- Use prometheus_client library
- Expose metrics on separate HTTP port (default: 9090)
- Configure port via MCP_TEST_METRICS_PORT environment variable
- Metrics are process-level, not persisted

## AI Directives

**IMPORTANT**: As you work through this story, please mark checklist items as complete `[x]` as you finish them. This ensures that if we need to pause and resume work, we have a clear record of progress. Update the `status` field in the frontmatter when moving between stages (in-progress, ready-for-review, done, blocked).

Metrics are optional for Phase 2. Focus on useful operational metrics.
