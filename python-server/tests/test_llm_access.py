"""Unit tests for chat/llm_access.py's context-prompt assembly.

`_build_context_prompt` doesn't touch any `LLMClient` instance state, so
these construct a bare instance via `__new__` to skip `__init__` (which
would otherwise need real settings/Ollama config) — pure formatting tests,
no LLM client or network involved. Confirms authority-based sorting and
labeling are gone: documents are presented in supplied order with no
authority label.
"""

import pytest

from chat.llm_access import DocumentContext, LLMClient


def _bare_client() -> LLMClient:
    return LLMClient.__new__(LLMClient)


@pytest.mark.unit
def test_build_context_prompt_preserves_supplied_order():
    client = _bare_client()
    docs = [
        DocumentContext(id="1", name="Zeta Doc", content="zeta content"),
        DocumentContext(id="2", name="Alpha Doc", content="alpha content"),
    ]

    prompt = client._build_context_prompt(docs)  # noqa: SLF001

    assert prompt.index("Zeta Doc") < prompt.index("Alpha Doc")


@pytest.mark.unit
def test_build_context_prompt_has_no_authority_label():
    client = _bare_client()
    docs = [DocumentContext(id="1", name="My Doc", content="some content")]

    prompt = client._build_context_prompt(docs)  # noqa: SLF001

    assert prompt == "--- Source: My Doc ---\nsome content\n"
    for label in (
        "Official Rules",
        "Player Notes",
        "GM Notes",
        "LLM-Generated",
        "Community Content",
        "Official Supplement",
        "Session Log",
    ):
        assert label not in prompt


@pytest.mark.unit
def test_document_context_has_no_authority_or_source_type_fields():
    doc = DocumentContext(id="1", name="Doc", content="content")

    assert not hasattr(doc, "source_type")
    assert not hasattr(doc, "authority_weight")
