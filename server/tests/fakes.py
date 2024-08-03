"""A stand-in for the OpenAI client so tests never need a real API key."""

import hashlib
import json
import math
import re
from types import SimpleNamespace

import httpx
import openai


def chat_response(content: str | None, prompt_tokens=120, completion_tokens=30):
    return SimpleNamespace(
        model="gpt-4o-mini-test",
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
    )


def stream_chunks(pieces: list[str], prompt_tokens=200, completion_tokens=40, fail_after=None):
    """Chunks shaped like a streamed chat completion; the last one carries usage."""

    def chunks():
        for index, piece in enumerate(pieces):
            if fail_after is not None and index == fail_after:
                raise openai.APIConnectionError(
                    request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
                )
            yield SimpleNamespace(
                model="gpt-4o-mini-test",
                usage=None,
                choices=[SimpleNamespace(delta=SimpleNamespace(content=piece))],
            )
        yield SimpleNamespace(
            model="gpt-4o-mini-test",
            usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
            choices=[],
        )

    return chunks()


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


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


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "for",
    "how",
    "i",
    "is",
    "it",
    "my",
    "of",
    "the",
    "to",
}


def fake_embedding(text: str, dimensions: int = 1536) -> list[float]:
    """Bag-of-words vector: texts that share words end up close together."""
    vector = [0.0] * dimensions
    for word in re.findall(r"[a-z]+", text.lower()):
        if word not in STOP_WORDS:
            vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % dimensions] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


class FakeOpenAI:
    def __init__(self):
        self.chat_responses: list = []
        self.chat_calls: list[dict] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create_chat))
        self.embedding_calls: list[dict] = []
        self.embedding_error: Exception | None = None
        self.embeddings = SimpleNamespace(create=self._create_embeddings)

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

    def _create_embeddings(self, *, model, input, dimensions):
        self.embedding_calls.append({"model": model, "input": input, "dimensions": dimensions})
        if self.embedding_error:
            raise self.embedding_error
        return SimpleNamespace(
            model="text-embedding-3-small-test",
            data=[
                SimpleNamespace(index=index, embedding=fake_embedding(text, dimensions))
                for index, text in enumerate(input)
            ],
            usage=SimpleNamespace(prompt_tokens=sum(len(text.split()) for text in input)),
        )
