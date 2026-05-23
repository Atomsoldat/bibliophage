"""Embedding model loader and device resolution.

Owns the HuggingFace embeddings singleton and the logic that picks an
inference device (cpu / cuda / xpu / mps) based on configuration and
available hardware.
"""

from __future__ import annotations

import logging
import re

import torch
from langchain_huggingface import HuggingFaceEmbeddings

from config import get_settings

logger = logging.getLogger(__name__)

_embeddings_model: HuggingFaceEmbeddings | None = None


def _resolve_embedding_device(override: str) -> str:
    if re.fullmatch(r"cpu|cuda(:\d+)?|mps|xpu", override):
        logger.info(f"Embedding device selected via override: {override}")
        return override

    if override != "":
        errormsg = f"Unexpected value for embedding device: {override}"
        raise ValueError(errormsg)

    # cuda covers both NVIDIA and AMD (ROCm PyTorch exposes torch.cuda API)
    if torch.cuda.is_available():
        logger.info("Embedding device detected automatically: cuda")
        return "cuda"
    # Intel
    elif torch.xpu.is_available():
        logger.info("Embedding device detected automatically: xpu")
        return "xpu"
    # this is apparently what the Macintosh people use
    elif torch.backends.mps.is_available():
        logger.info("Embedding device detected automatically: mps")
        return "mps"
    else:
        logger.info("Embedding device auto detection failed, falling back to cpu")
        return "cpu"


def get_embeddings_model() -> HuggingFaceEmbeddings:
    """Get the embeddings model singleton."""
    global _embeddings_model
    if _embeddings_model is None:
        settings = get_settings()
        model_name = settings.embedding.embedding_model_name
        device = _resolve_embedding_device(settings.embedding.embedding_device)
        logger.info(f"Loading embeddings model: {model_name} on device: {device}")
        _embeddings_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info(f"Embeddings model loaded: {model_name}")
    return _embeddings_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embedding vectors for a batch of texts.

    Returns one vector per input text, in the same order.
    """
    model = get_embeddings_model()
    logger.info(f"Generating embeddings for {len(texts)} texts")
    return model.embed_documents(texts)
