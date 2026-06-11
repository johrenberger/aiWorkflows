"""Tests for component_test_candidates filtering (Bug #34 fix)."""
from test_factory.orchestrator import TestFactoryOrchestrator


def test_component_candidate_is_controller():
    item = {"path": "core/broadleaf-framework-web/src/main/java/com/example/MyController.java", "language": "java"}
    assert TestFactoryOrchestrator._is_component_candidate(item) is True


def test_component_candidate_is_web_layer():
    item = {"path": "core/broadleaf-framework/src/main/java/com/example/web/FilterImpl.java", "language": "java"}
    assert TestFactoryOrchestrator._is_component_candidate(item) is True


def test_component_candidate_is_js_ui():
    item = {"path": "admin/broadleaf-open-admin-platform/src/main/resources/open_admin_style/js/admin/components/filterbuilder.js", "language": "javascript"}
    assert TestFactoryOrchestrator._is_component_candidate(item) is True


def test_domain_entity_is_not_component():
    """Bug #34: domain entities / DTOs / service impls (not web layer) should
    not be flagged as component test candidates. The previous filter
    used risk_score >= 50, which made every queue item pass."""
    item = {"path": "core/broadleaf-framework/src/main/java/com/example/catalog/domain/Product.java", "language": "java", "risk_score": 999.0}
    assert TestFactoryOrchestrator._is_component_candidate(item) is False
