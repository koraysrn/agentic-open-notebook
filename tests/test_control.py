"""Tests for the Control Layer verification graph (Road_Map Step 8)."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from open_notebook.graphs.control import (
    Claim,
    Contradiction,
    HallucinationCheck,
    VerificationResult,
    contradiction_graph,
    contradiction_node,
    graph,
    hallucination_graph,
    hallucination_node,
    verify_node,
)


def _fake_model(content: str):
    return SimpleNamespace(ainvoke=AsyncMock(return_value=SimpleNamespace(content=content)))


class TestClaimModel:
    def test_valid_claim(self):
        claim = Claim(text="x", label="verified", confidence=0.9)
        assert claim.label == "verified"
        assert claim.evidence_ids == []

    def test_invalid_label_is_rejected(self):
        with pytest.raises(ValueError):
            Claim(text="x", label="wrong")  # type: ignore[arg-type]

    def test_confidence_out_of_range_is_rejected(self):
        with pytest.raises(ValueError):
            Claim(text="x", label="verified", confidence=1.5)


class TestVerifyNode:
    @pytest.mark.asyncio
    async def test_parses_claims_from_model_output(self):
        payload = {
            "claims": [
                {
                    "text": "The sky is blue.",
                    "label": "verified",
                    "evidence_ids": ["source:1"],
                    "confidence": 0.95,
                }
            ]
        }
        model = _fake_model(json.dumps(payload))
        with patch(
            "open_notebook.graphs.control.provision_langchain_model",
            new=AsyncMock(return_value=model),
        ):
            result = await verify_node({"answer": "a", "evidence": []}, {})  # type: ignore[arg-type]

        assert isinstance(result["claims"][0], Claim)
        assert result["claims"][0].label == "verified"
        assert result["claims"][0].evidence_ids == ["source:1"]


class TestControlGraph:
    def test_graph_has_verify_node(self):
        names = set(graph.get_graph().nodes.keys())
        assert {"verify", "__start__", "__end__"} <= names

    def test_verification_result_defaults_to_empty_claims(self):
        assert VerificationResult().claims == []


class TestContradictionModel:
    def test_confidence_out_of_range_is_rejected(self):
        with pytest.raises(ValueError):
            Contradiction(
                statement_a="a", statement_b="b", confidence=2.0
            )


class TestContradictionNode:
    @pytest.mark.asyncio
    async def test_parses_contradictions_from_model_output(self):
        payload = {
            "contradictions": [
                {
                    "statement_a": "X is true.",
                    "evidence_a_ids": ["source:1"],
                    "statement_b": "X is false.",
                    "evidence_b_ids": ["source:2"],
                    "reasoning": "Direct conflict.",
                    "confidence": 0.9,
                }
            ]
        }
        model = _fake_model(json.dumps(payload))
        with patch(
            "open_notebook.graphs.control.provision_langchain_model",
            new=AsyncMock(return_value=model),
        ):
            result = await contradiction_node({"evidence": []}, {})  # type: ignore[arg-type]

        assert isinstance(result["contradictions"][0], Contradiction)
        assert result["contradictions"][0].evidence_a_ids == ["source:1"]


class TestContradictionGraph:
    def test_graph_has_detect_node(self):
        names = set(contradiction_graph.get_graph().nodes.keys())
        assert {"detect", "__start__", "__end__"} <= names


class TestHallucinationNode:
    @pytest.mark.asyncio
    async def test_parses_supported_verdict(self):
        payload = {
            "supported": False,
            "confidence": 0.8,
            "reasoning": "The answer asserts facts not in the evidence.",
        }
        model = _fake_model(json.dumps(payload))
        with patch(
            "open_notebook.graphs.control.provision_langchain_model",
            new=AsyncMock(return_value=model),
        ):
            result = await hallucination_node({"answer": "a", "evidence": []}, {})  # type: ignore[arg-type]

        assert isinstance(result["check"], HallucinationCheck)
        assert result["check"].supported is False


class TestHallucinationGraph:
    def test_graph_has_judge_node(self):
        names = set(hallucination_graph.get_graph().nodes.keys())
        assert {"judge", "__start__", "__end__"} <= names
