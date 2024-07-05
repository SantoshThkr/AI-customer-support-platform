"""A stand-in for the OpenAI client so tests never need a real API key."""

import json
from types import SimpleNamespace

import httpx
import openai


def chat_response(content: str | None, prompt_tokens=120, completion_tokens=30):
    return SimpleNamespace(
        model="gpt-4o-mini-test",
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
    )


def analysis_json(**overrides) -> str:
    data = {
        "category": "ACCOUNT",
        "priority": "HIGH",
        "sentiment": "NEGATIVE",
        "summary": "Customer cannot log in after resetting their password.",
    }
    data.update(overrides)
    return json.dumps(data)


def timeout_error() -> openai.APITimeoutError:
    return openai.APITimeoutError(
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    )


class FakeOpenAI:
    def __init__(self):
        self.chat_responses: list = []
        self.chat_calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create_chat))

    def queue(self, *responses) -> None:
        """Queue chat responses (or exceptions to raise) in the order they will be used."""
        self.chat_responses.extend(responses)

    def _create_chat(self, **params):
        self.chat_calls.append(params)
        if not self.chat_responses:
            raise AssertionError("FakeOpenAI: no chat response queued")
        response = self.chat_responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response
