"""Tests for inference service: normalize_model_output, extract_json_object, _parse_workflow_json."""
import json
import pytest
from fastapi import HTTPException

from app.services.inference import (
    extract_json_object,
    normalize_model_output,
)
from app.services import inference as inference_mod


class TestNormalizeModelOutput:
    def test_empty_returns_empty(self):
        assert inference_mod.normalize_model_output("") == ""
        assert inference_mod.normalize_model_output("   ") == ""

    def test_passthrough_plain_json(self):
        raw = '{"a": 1}'
        assert inference_mod.normalize_model_output(raw) == raw

    def test_strips_fence_with_newline(self):
        raw = "```json\n{\"a\": 1}\n```"
        assert inference_mod.normalize_model_output(raw) == '{"a": 1}'

    def test_strips_fence_no_lang(self):
        raw = "```\n{\"x\": 2}\n```"
        assert inference_mod.normalize_model_output(raw) == '{"x": 2}'


class TestExtractJsonObject:
    def test_simple_object(self):
        text = 'before {"k": "v"} after'
        assert inference_mod.extract_json_object(text) == '{"k": "v"}'

    def test_nested_object(self):
        text = 'x {"a": {"b": 1}} y'
        assert inference_mod.extract_json_object(text) == '{"a": {"b": 1}}'

    def test_no_brace_raises(self):
        with pytest.raises(ValueError, match="No JSON object found"):
            inference_mod.extract_json_object("no braces here")

    def test_ignores_braces_in_strings(self):
        text = '{"msg": "hello {world}"}'
        assert inference_mod.extract_json_object(text) == '{"msg": "hello {world}"}'


class TestParseWorkflowJson:
    def test_valid_raw_json(self):
        obj = {"session_id": "s1", "title": "t", "description": "d", "parameters": [], "steps": [], "risk_level": "low", "time_saved_minutes": 5}
        raw = json.dumps(obj)
        result = inference_mod._parse_workflow_json(raw)
        assert result["session_id"] == "s1"
        assert result["title"] == "t"

    def test_valid_with_fence(self):
        obj = {"session_id": "s2", "title": "T", "description": "D", "parameters": [], "steps": [], "risk_level": "low", "time_saved_minutes": 1}
        raw = "```json\n" + json.dumps(obj) + "\n```"
        result = inference_mod._parse_workflow_json(raw)
        assert result["session_id"] == "s2"

    def test_invalid_raises_502(self):
        with pytest.raises(HTTPException) as exc_info:
            inference_mod._parse_workflow_json("not json at all")
        assert exc_info.value.status_code == 502
