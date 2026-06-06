# Phase 11 — Error Handling, Logging, Observability

## Error Handling
- **Global handler:** <middleware / filter / interceptor + path>
- **Custom error classes:** <list>
- **Retry patterns:** <library / hand-rolled>

## Logging
- **Library:** <pino / winston / log4j / slf4j / structlog / etc.>
- **Format:** <json / text>
- **Log level config:** <env / file>

## Monitoring / Telemetry
- **Sentry:** <yes/no, DSN env>
- **Datadog:** <yes/no>
- **OpenTelemetry:** <yes/no, exporter>
- **Metrics:** <prometheus / statsd / none>

## Alerting Hooks
- <pagerduty / slack / opsgenie integration>
