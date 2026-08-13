"""The 5 cost-optimization techniques."""
from __future__ import annotations
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional
import re
import tiktoken

from pricing import MODEL_TIERS

_ENC = tiktoken.get_encoding("cl100k_base")

_STOP = {
    "a", "an", "the", "i", "my", "me", "do", "does", "did", "how", "is", "it",
    "to", "in", "on", "of", "for", "and", "or", "but", "can", "could", "would",
    "should", "will", "be", "am", "have", "has", "had", "this", "that", "what",
    "which", "who", "when", "where", "why", "you", "your", "we", "our", "so",
    "if", "as", "at", "by", "with", "from", "into", "any", "some",
}


def _content_words(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOP and len(w) > 1}


def similarity(a: str, b: str) -> float:
    """Hybrid similarity: max of char-level ratio and content-word Jaccard."""
    seq = SequenceMatcher(None, a.lower(), b.lower()).ratio()
    wa, wb = _content_words(a), _content_words(b)
    if not wa or not wb:
        return seq
    jaccard = len(wa & wb) / len(wa | wb)
    return max(seq, jaccard)


def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(_ENC.encode(text))


# ---------- 1. Prompt caching ----------
def apply_prompt_cache(system_prompt: str, cache_enabled: bool) -> int:
    """Return the number of input tokens that count as *cached* (discounted)."""
    if not cache_enabled:
        return 0
    return count_tokens(system_prompt)


# ---------- 2. Model routing ----------
COMPLEX_HINTS = ("analyze", "compare", "reason", "step by step", "explain why",
                 "derive", "prove", "code", "debug", "architect", "design")

def route_model(prompt: str, provider: str, routing_enabled: bool, default: str) -> str:
    if not routing_enabled:
        return default
    tier = MODEL_TIERS[provider]
    lower = prompt.lower()
    is_complex = len(prompt) > 400 or any(h in lower for h in COMPLEX_HINTS)
    return tier["strong"] if is_complex else tier["cheap"]


# ---------- 3. Semantic cache ----------
@dataclass
class CacheHit:
    response: str
    similarity: float


class SemanticCache:
    def __init__(self, threshold: float = 0.55):
        self.store: list[tuple[str, str]] = []
        self.threshold = threshold

    def lookup(self, prompt: str) -> Optional[CacheHit]:
        best: Optional[CacheHit] = None
        for cached_prompt, response in self.store:
            sim = similarity(prompt, cached_prompt)
            if sim >= self.threshold and (best is None or sim > best.similarity):
                best = CacheHit(response=response, similarity=sim)
        return best

    def put(self, prompt: str, response: str) -> None:
        self.store.append((prompt, response))

    def clear(self) -> None:
        self.store.clear()


# ---------- 4. Context trimming ----------
def trim_context(text: str, trim_enabled: bool, max_tokens: int = 500) -> tuple[str, int]:
    """Return (possibly trimmed text, tokens saved)."""
    tokens = _ENC.encode(text)
    if not trim_enabled or len(tokens) <= max_tokens:
        return text, 0
    kept = tokens[-max_tokens:]
    saved = len(tokens) - len(kept)
    trimmed = "[...earlier context summarized...] " + _ENC.decode(kept)
    return trimmed, saved


# ---------- 5. Output control ----------
def output_cap(output_control_enabled: bool) -> int:
    """Return max_tokens cap for the response."""
    return 150 if output_control_enabled else 1000
