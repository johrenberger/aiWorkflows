---
name: summarizer
artifact_type: agent
purpose: Summarize long documents into structured bullet points for engineering review.
category: analysis
owner: justin
version: "0.2.0"
inputs:
  - name: document
    type: file
outputs:
  format: json
  fields:
    - summary
    - key_points
    - risks
dependencies: []
intended_consumers: []
quality_level: usable
last_reviewed: 2026-06-13
---

# summarizer agent
