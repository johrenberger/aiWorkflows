from __future__ import annotations

from copy import deepcopy

from mutationctl.models import LLMClassificationRequest


class FakeLLMClient:
    def __init__(self, configured_response: dict) -> None:
        self._configured_response = deepcopy(configured_response)

    def classify(self, request: LLMClassificationRequest) -> dict:
        del request
        return deepcopy(self._configured_response)
