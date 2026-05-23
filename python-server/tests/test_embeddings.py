"""Unit tests for embeddings.py (device resolution).

We do not actually load a HuggingFace model in tests — only the device
resolution helper is exercised. torch.* availability checks are patched
so the test does not depend on the host's actual hardware.
"""

import pytest

import embeddings as embeddings_module
from embeddings import _resolve_embedding_device, embed_texts


@pytest.mark.unit
@pytest.mark.parametrize(
    "override",
    ["cpu", "cuda", "cuda:0", "cuda:7", "mps", "xpu"],
)
def test_override_is_returned_verbatim(override):
    assert _resolve_embedding_device(override) == override


@pytest.mark.unit
def test_invalid_nonempty_override_raises():
    with pytest.raises(ValueError, match="Unexpected value for embedding device"):
        _resolve_embedding_device("gpu")


@pytest.mark.unit
def test_auto_detect_falls_back_to_cpu(monkeypatch):
    import torch

    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(torch.xpu, "is_available", lambda: False)
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)

    assert _resolve_embedding_device("") == "cpu"


@pytest.mark.unit
def test_auto_detect_picks_cuda_first(monkeypatch):
    import torch

    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.xpu, "is_available", lambda: True)
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: True)

    assert _resolve_embedding_device("") == "cuda"


@pytest.mark.unit
def test_auto_detect_picks_xpu_when_only_xpu(monkeypatch):
    import torch

    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(torch.xpu, "is_available", lambda: True)
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False)

    assert _resolve_embedding_device("") == "xpu"


@pytest.mark.unit
def test_auto_detect_picks_mps_when_only_mps(monkeypatch):
    import torch

    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(torch.xpu, "is_available", lambda: False)
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: True)

    assert _resolve_embedding_device("") == "mps"


# ── embed_texts ─────────────────────────────────────────────────────────


class _FakeModel:
    """Minimal stand-in for HuggingFaceEmbeddings used in embed_texts tests."""

    def __init__(self):
        self.calls: list[list[str]] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[float(len(t)), float(i)] for i, t in enumerate(texts)]


@pytest.mark.unit
def test_embed_texts_delegates_to_singleton_model(monkeypatch):
    fake = _FakeModel()
    monkeypatch.setattr(embeddings_module, "get_embeddings_model", lambda: fake)

    result = embed_texts(["alpha", "bravo", "ch"])

    assert fake.calls == [["alpha", "bravo", "ch"]]
    assert result == [[5.0, 0.0], [5.0, 1.0], [2.0, 2.0]]


@pytest.mark.unit
def test_embed_texts_empty_input(monkeypatch):
    fake = _FakeModel()
    monkeypatch.setattr(embeddings_module, "get_embeddings_model", lambda: fake)

    assert embed_texts([]) == []
    assert fake.calls == [[]]
