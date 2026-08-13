"""Unified LLM provider interface. Falls back to a mock if no key is given."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from pricing import PRICING
from optimizations import count_tokens


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    mocked: bool = False


def _mock(prompt: str, system: str, max_tokens: int, model: str) -> LLMResponse:
    """Simulate a response whose length scales with input, so demos show meaningful cost variance."""
    input_tok = count_tokens(system) + count_tokens(prompt)
    # Output roughly 1.2x input, floored at 40, capped at max_tokens
    sim_out = max(40, min(int(input_tok * 1.2) + 20, max_tokens))
    unit = "This is a simulated answer for demoing cost math. "
    reply = "[MOCK — add an API key for a real response] " + (unit * (sim_out // 8 + 1))
    return LLMResponse(
        text=reply,
        input_tokens=input_tok,
        output_tokens=sim_out,
        model=model,
        mocked=True,
    )


def call_openai(prompt, system, model, max_tokens, api_key) -> LLMResponse:
    if not api_key:
        return _mock(prompt, system, max_tokens, model)
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    u = resp.usage
    return LLMResponse(
        text=resp.choices[0].message.content or "",
        input_tokens=u.prompt_tokens,
        output_tokens=u.completion_tokens,
        model=model,
    )


def call_anthropic(prompt, system, model, max_tokens, api_key) -> LLMResponse:
    if not api_key:
        return _mock(prompt, system, max_tokens, model)
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    u = resp.usage
    text = "".join(b.text for b in resp.content if hasattr(b, "text"))
    return LLMResponse(
        text=text,
        input_tokens=u.input_tokens,
        output_tokens=u.output_tokens,
        model=model,
    )


def call_google(prompt, system, model, max_tokens, api_key) -> LLMResponse:
    if not api_key:
        return _mock(prompt, system, max_tokens, model)
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    m = genai.GenerativeModel(model, system_instruction=system)
    resp = m.generate_content(
        prompt,
        generation_config={"max_output_tokens": max_tokens},
    )
    text = resp.text or ""
    return LLMResponse(
        text=text,
        input_tokens=count_tokens(system + prompt),
        output_tokens=count_tokens(text),
        model=model,
    )


def call_groq(prompt, system, model, max_tokens, api_key) -> LLMResponse:
    if not api_key:
        return _mock(prompt, system, max_tokens, model)
    from groq import Groq
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    u = resp.usage
    return LLMResponse(
        text=resp.choices[0].message.content or "",
        input_tokens=u.prompt_tokens,
        output_tokens=u.completion_tokens,
        model=model,
    )


def call(model: str, prompt: str, system: str, max_tokens: int, keys: dict) -> LLMResponse:
    provider = PRICING[model]["provider"]
    fn = {
        "openai":    call_openai,
        "anthropic": call_anthropic,
        "google":    call_google,
        "groq":      call_groq,
    }[provider]
    return fn(prompt, system, model, max_tokens, keys.get(provider))
