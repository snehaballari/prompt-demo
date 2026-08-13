"""Prompt Cost Lab — live demo of 5 LLM cost-optimization techniques."""
from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from pricing import PRICING, MODEL_TIERS, cost
from optimizations import (
    count_tokens, apply_prompt_cache, route_model,
    SemanticCache, trim_context, output_cap,
)
from providers import call

st.set_page_config(page_title="Prompt Cost Lab", page_icon="💸", layout="wide")

# ---------- Session state ----------
if "cache" not in st.session_state:
    st.session_state.cache = SemanticCache(threshold=0.55)
if "keys" not in st.session_state:
    st.session_state.keys = {"openai": "", "anthropic": "", "google": "", "groq": ""}
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ---------- Header ----------
st.title("💸 Prompt Cost Lab")
st.caption(
    "Same model. Same product. Same users. **Cut LLM cost by 70–95%** "
    "with 5 techniques you can toggle live."
)

# ---------- Sidebar: keys, model, toggles ----------
with st.sidebar:
    st.header("⚙️  Setup")
    with st.expander("🔑 API keys (stored only in this session)", expanded=False):
        st.session_state.keys["openai"]    = st.text_input("OpenAI key",     type="password", value=st.session_state.keys["openai"])
        st.session_state.keys["anthropic"] = st.text_input("Anthropic key",  type="password", value=st.session_state.keys["anthropic"])
        st.session_state.keys["google"]    = st.text_input("Google key",     type="password", value=st.session_state.keys["google"])
        st.session_state.keys["groq"]      = st.text_input("Groq key (free)", type="password", value=st.session_state.keys["groq"])
        st.caption("Leave blank to use mocked responses — cost math still works.")

    model = st.selectbox(
        "Model",
        list(PRICING.keys()),
        index=list(PRICING.keys()).index("gpt-4o"),
    )
    p = PRICING[model]
    st.caption(f"**${p['in']}/M in · ${p['out']}/M out · ${p['cached_in']}/M cached**")

    st.divider()
    st.header("🎛  Optimizations")
    opt_cache   = st.toggle("1️⃣  Prompt caching",   value=False, help="Discount input tokens that come from a repeated system prompt (Anthropic 90%, OpenAI 50%).")
    opt_route   = st.toggle("2️⃣  Model routing",    value=False, help="Auto-classify prompt complexity; route simple prompts to the cheaper model in the same family.")
    opt_semcache= st.toggle("3️⃣  Semantic cache",   value=False, help="Return a cached answer when a new prompt is >85% similar to a previous one.")
    opt_trim    = st.toggle("4️⃣  Context trimming", value=False, help="Trim very long input to the last 500 tokens.")
    opt_output  = st.toggle("5️⃣  Output control",   value=False, help="Cap max_tokens at 150 so the model doesn't ramble.")

    st.divider()
    if st.button("🧹 Clear semantic cache"):
        st.session_state.cache.clear()
        st.success("Cache cleared.")

# ---------- Main area ----------
left, right = st.columns([1, 1])

with left:
    st.subheader("📝 Prompt")
    system = st.text_area(
        "System prompt (often reused → benefits from caching)",
        value=("You are a helpful customer-support assistant for Acme Cloud. "
               "Answer briefly, cite doc pages when possible, and never invent SKUs. "
               "Follow the style guide: friendly, plain English, no jargon. " * 6),
        height=120,
    )
    examples = {
        "— pick an example —": "",
        "Short factual Q":  "What's the capital of France?",
        "Repetitive support ticket": "How do I reset my Acme Cloud password?",
        "Long analysis":    ("Analyze the following architecture and compare the tradeoffs "
                             "of moving from a monolith to microservices step by step, "
                             "considering cost, latency, team topology, and deployability. "
                             "Explain why each factor matters."),
    }
    picked = st.selectbox("Preloaded examples", list(examples.keys()))
    if "prompt_text" not in st.session_state or picked != "— pick an example —":
        st.session_state.prompt_text = examples[picked] or st.session_state.get("prompt_text", "")
    prompt = st.text_area("User prompt", value=st.session_state.prompt_text, height=160, key="prompt_area")

    run = st.button("▶️  Run", type="primary", use_container_width=True)

with right:
    st.subheader("💰 Cost breakdown")
    meter_placeholder = st.empty()
    chart_placeholder = st.empty()
    response_placeholder = st.container()


def compute(prompt: str, system: str, model: str, opts: dict) -> dict:
    """Compute baseline and optimized cost + call the model for the optimized path."""
    provider = PRICING[model]["provider"]

    # --- Baseline: no optimizations ---
    base_in = count_tokens(system) + count_tokens(prompt)
    base_out_cap = 1000
    base_cost = cost(model, base_in, base_out_cap)

    # --- Optimized path ---
    opt_prompt, saved = trim_context(prompt, opts["trim"])
    used_model = route_model(opt_prompt, provider, opts["route"], default=model)
    cached_in = apply_prompt_cache(system, opts["cache"])
    max_out = output_cap(opts["output"])

    # Semantic cache
    cache_hit = None
    if opts["semcache"]:
        cache_hit = st.session_state.cache.lookup(opt_prompt)

    if cache_hit is not None:
        return {
            "baseline_cost": base_cost,
            "optimized_cost": 0.0,
            "baseline_tokens": (base_in, base_out_cap),
            "optimized_tokens": (0, 0),
            "used_model": used_model,
            "cache_hit": cache_hit,
            "response": cache_hit.response,
            "trimmed_saved": saved,
            "mocked": False,
        }

    resp = call(used_model, opt_prompt, system, max_out, st.session_state.keys)
    opt_cost = cost(used_model, resp.input_tokens, resp.output_tokens, cached_in_tok=cached_in)

    if opts["semcache"]:
        st.session_state.cache.put(opt_prompt, resp.text)

    return {
        "baseline_cost": base_cost,
        "optimized_cost": opt_cost,
        "baseline_tokens": (base_in, base_out_cap),
        "optimized_tokens": (resp.input_tokens, resp.output_tokens),
        "used_model": used_model,
        "cache_hit": None,
        "response": resp.text,
        "trimmed_saved": saved,
        "mocked": resp.mocked,
    }


def render(result: dict, opts: dict):
    b, o = result["baseline_cost"], result["optimized_cost"]
    saved_pct = ((b - o) / b * 100) if b > 0 else 0

    with meter_placeholder.container():
        c1, c2, c3 = st.columns(3)
        c1.metric("Baseline",  f"${b:.5f}")
        c2.metric("Optimized", f"${o:.5f}", f"-{saved_pct:.1f}%")
        c3.metric("Monthly savings\n(100k calls)", f"${(b - o) * 100_000:,.0f}")

        badges = []
        if opts["cache"]:    badges.append("🧊 caching")
        if opts["route"]:    badges.append(f"🎯 routed → `{result['used_model']}`")
        if opts["semcache"] and result["cache_hit"]:
            badges.append(f"⚡ cache hit (sim={result['cache_hit'].similarity:.2f})")
        if opts["trim"] and result["trimmed_saved"]:
            badges.append(f"✂️  trimmed {result['trimmed_saved']} tokens")
        if opts["output"]:   badges.append("📏 output capped at 150")
        if badges:
            st.info(" · ".join(badges))

    # Chart
    fig = go.Figure(data=[
        go.Bar(name="Baseline",  x=["Input tok", "Output tok", "Cost ($)"],
               y=[result["baseline_tokens"][0], result["baseline_tokens"][1], b],
               marker_color="#ef4444"),
        go.Bar(name="Optimized", x=["Input tok", "Output tok", "Cost ($)"],
               y=[result["optimized_tokens"][0], result["optimized_tokens"][1], o],
               marker_color="#22c55e"),
    ])
    fig.update_layout(barmode="group", height=280, margin=dict(l=10, r=10, t=30, b=10),
                      legend=dict(orientation="h", y=1.1))
    chart_placeholder.plotly_chart(fig, use_container_width=True)

    with response_placeholder:
        st.subheader("🗨️ Response")
        if result["mocked"]:
            st.warning("Using MOCK response — add an API key in the sidebar to hit a real model.")
        st.write(result["response"])

# ---------- Run ----------
if run and prompt.strip():
    opts = {"cache": opt_cache, "route": opt_route, "semcache": opt_semcache,
            "trim": opt_trim, "output": opt_output}
    with st.spinner("Calling model…"):
        result = compute(prompt, system, model, opts)
    st.session_state.last_result = (result, opts)

if st.session_state.last_result:
    render(*st.session_state.last_result)
else:
    with meter_placeholder.container():
        st.info("👈 Pick a model, toggle optimizations, and hit **Run**.")

# ---------- Bulk simulator ----------
st.divider()
st.subheader("📈 Simulate 100 calls / month projection")
sim_col1, sim_col2 = st.columns([1, 3])
with sim_col1:
    n_calls = st.number_input("Calls / month", 1000, 10_000_000, 100_000, step=10_000)
    if st.button("Run projection"):
        if st.session_state.last_result:
            r, _ = st.session_state.last_result
            df = pd.DataFrame({
                "Scenario": ["Baseline", "Optimized"],
                "Monthly cost ($)": [r["baseline_cost"] * n_calls, r["optimized_cost"] * n_calls],
            })
            with sim_col2:
                st.dataframe(df, hide_index=True, use_container_width=True)
                fig = go.Figure(go.Bar(x=df["Scenario"], y=df["Monthly cost ($)"],
                                       marker_color=["#ef4444", "#22c55e"]))
                fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Run a prompt first.")
