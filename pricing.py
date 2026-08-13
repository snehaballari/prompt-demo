"""Per-1M-token pricing (USD). Rough public rates — update as needed."""

PRICING = {
    # OpenAI
    "gpt-4o":          {"in": 2.50, "out": 10.00, "cached_in": 1.25, "provider": "openai"},
    "gpt-4o-mini":     {"in": 0.15, "out": 0.60,  "cached_in": 0.075, "provider": "openai"},
    # Anthropic
    "claude-sonnet-4-6": {"in": 3.00, "out": 15.00, "cached_in": 0.30, "provider": "anthropic"},
    "claude-haiku-4-5":  {"in": 0.80, "out": 4.00,  "cached_in": 0.08, "provider": "anthropic"},
    # Google
    "gemini-1.5-flash": {"in": 0.075, "out": 0.30, "cached_in": 0.019, "provider": "google"},
    # Groq (free tier — nominal pricing for math)
    "llama-3.1-70b-versatile": {"in": 0.59, "out": 0.79, "cached_in": 0.59, "provider": "groq"},
}

MODEL_TIERS = {
    "openai":    {"cheap": "gpt-4o-mini",     "strong": "gpt-4o"},
    "anthropic": {"cheap": "claude-haiku-4-5", "strong": "claude-sonnet-4-6"},
    "google":    {"cheap": "gemini-1.5-flash", "strong": "gemini-1.5-flash"},
    "groq":      {"cheap": "llama-3.1-70b-versatile", "strong": "llama-3.1-70b-versatile"},
}


def cost(model: str, in_tok: int, out_tok: int, cached_in_tok: int = 0) -> float:
    p = PRICING[model]
    fresh_in = max(in_tok - cached_in_tok, 0)
    return (
        fresh_in       * p["in"]        / 1_000_000
        + cached_in_tok * p["cached_in"] / 1_000_000
        + out_tok      * p["out"]       / 1_000_000
    )
