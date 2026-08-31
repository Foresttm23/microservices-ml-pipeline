import pytest
from ml_worker.utils.gemini import (
    extract_text_from_gemini_response,
    extract_tokens_from_gemini_response,
)


def test_extract_text_success():
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Hello, world!"}
                    ]
                }
            }
        ]
    }
    assert extract_text_from_gemini_response(payload) == "Hello, world!"


def test_extract_text_missing_candidates():
    assert extract_text_from_gemini_response({}) is None
    assert extract_text_from_gemini_response({"candidates": []}) is None


def test_extract_text_missing_content_or_parts():
    assert extract_text_from_gemini_response({"candidates": [{}]}) is None
    assert extract_text_from_gemini_response({"candidates": [{"content": {}}]}) is None
    assert extract_text_from_gemini_response({"candidates": [{"content": {"parts": []}}]}) is None
    assert extract_text_from_gemini_response({"candidates": [{"content": {"parts": [{}]}}]}) is None


def test_extract_tokens_total_count():
    payload = {
        "usageMetadata": {
            "totalTokenCount": 42,
            "promptTokenCount": 10,
            "candidatesTokenCount": 32,
        }
    }
    assert extract_tokens_from_gemini_response(payload) == 42


def test_extract_tokens_calculated_from_prompt_and_candidates():
    payload = {
        "usageMetadata": {
            "promptTokenCount": 15,
            "candidatesTokenCount": 25,
        }
    }
    assert extract_tokens_from_gemini_response(payload) == 40


def test_extract_tokens_missing_metadata():
    assert extract_tokens_from_gemini_response({}) is None
    assert extract_tokens_from_gemini_response({"usageMetadata": {}}) is None


def test_extract_tokens_invalid_value():
    assert extract_tokens_from_gemini_response({"usageMetadata": {"totalTokenCount": "invalid"}}) is None
