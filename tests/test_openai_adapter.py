from types import SimpleNamespace

from app.config import LLMConfig
from app.domain.intent import ParsedEngineeringIntent
from app.providers.openai_parser import OpenAIEngineeringParser


def _unknown():
    return {
        "raw_value": None,
        "raw_unit": None,
        "source_text": None,
        "state": "unknown",
        "confidence": 0.0,
    }


class FakeResponses:
    def __init__(self, parsed):
        self.parsed = parsed
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.parsed)


class FakeClient:
    def __init__(self, parsed):
        self.responses = FakeResponses(parsed)


def test_openai_adapter_uses_responses_parse_and_pydantic_model():
    payload = {}
    for name in ParsedEngineeringIntent.model_fields:
        if name in {"qualitative_requirements", "unmapped_phrases"}:
            payload[name] = []
        else:
            payload[name] = _unknown()

    payload["component"] = {
        "raw_value": "bracket",
        "raw_unit": None,
        "source_text": "bracket",
        "state": "confirmed",
        "confidence": 1.0,
    }

    parsed = ParsedEngineeringIntent.model_validate(payload)
    client = FakeClient(parsed)
    config = LLMConfig(
        provider="openai",
        model="gpt-5.6-sol",
        timeout_seconds=30,
        max_retries=1,
    )

    parser = OpenAIEngineeringParser(config=config, client=client)
    result = parser.parse("Create a bracket.")

    assert result == parsed
    call = client.responses.calls[0]
    assert call["model"] == "gpt-5.6-sol"
    assert call["text_format"] is ParsedEngineeringIntent
    assert call["store"] is False
