from __future__ import annotations

from typing import Protocol

from mutationctl.models import LLMClassificationRequest


class LLMClient(Protocol):
    def classify(self, request: LLMClassificationRequest) -> dict:
        ...
