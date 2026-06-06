# Phase 12 — Security Analysis

> No destructive testing. Read-only analysis.

## Authentication
<mechanism, library, evidence>

## Authorization
<RBAC / ABAC / scopes, evidence>

## Input Validation
<zod / joi / class-validator / etc.>

## Secrets Handling
<env / vault / SOPS, evidence>

## Middleware
- CSRF: <yes/no, lib>
- CORS: <config location>
- CSP: <yes/no>
- Helmet / similar: <yes/no>

## Password / Token Handling
<bcrypt / argon2 / jose, evidence>

## Dependency Risk Indicators
<outdated majors, known CVEs from lockfile check>

## Common Attack Protections
- Rate limiting: <yes/no>
- SQL injection: <parameterized? evidence>
- XSS: <sanitization, evidence>
