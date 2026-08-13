"""Prompt Cost Lab — compare two versions of a prompt side-by-side."""
from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go

from pricing import PRICING, cost
from optimizations import count_tokens
from providers import call

st.set_page_config(page_title="Prompt Cost Lab", layout="wide")

# ---------- Session state ----------
if "api_keys" not in st.session_state:
    st.session_state.api_keys = {"openai": "", "anthropic": "", "google": "", "groq": ""}
if "result_a" not in st.session_state:
    st.session_state.result_a = None
if "result_b" not in st.session_state:
    st.session_state.result_b = None

# ---------- Header ----------
st.title("Prompt Cost Lab")
st.write(
    "Write a prompt on the left. Write a more efficient version on the right. "
    "Run both. See exactly how many tokens each used and what it cost."
)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Setup")

    model = st.selectbox("Model", list(PRICING.keys()), index=list(PRICING.keys()).index("gpt-4o"))
    p = PRICING[model]
    st.caption(
        f"Input: ${p['in']} per million tokens  \n"
        f"Output: ${p['out']} per million tokens  \n"
        f"Cached input: ${p['cached_in']} per million tokens"
    )

    st.divider()
    with st.expander("API keys (session only, never stored)"):
        st.session_state.api_keys["openai"]    = st.text_input("OpenAI key",    type="password", value=st.session_state.api_keys["openai"])
        st.session_state.api_keys["anthropic"] = st.text_input("Anthropic key", type="password", value=st.session_state.api_keys["anthropic"])
        st.session_state.api_keys["google"]    = st.text_input("Google key",    type="password", value=st.session_state.api_keys["google"])
        st.session_state.api_keys["groq"]      = st.text_input("Groq key (free at console.groq.com)", type="password", value=st.session_state.api_keys["groq"])
        st.caption("No key? The app will use a mock response. Cost math still works.")

    st.divider()
    st.header("Assumptions")
    monthly_calls = st.number_input("Calls per month (for savings projection)", 1_000, 10_000_000, 100_000, step=10_000)


# ---------- Example bank ----------
EXAMPLES = {
    "-- pick a before/after example --": None,
    "1. Bloated system prompt (caching)": {
        "sys_a": ("You are a helpful customer-support assistant for Acme Cloud. Always be friendly. "
                  "Never invent SKUs. Cite documentation pages when possible. Follow the style guide: "
                  "friendly, plain English, no jargon. " * 6),
        "user_a": "How do I reset my Acme Cloud password?",
        "sys_b": "Acme Cloud support assistant. Cite docs. No made-up SKUs.",
        "user_b": "How do I reset my Acme Cloud password?",
        "note": "Trim the system prompt. Same intent, 90% fewer tokens.",
    },
    "2. Wrong model for the job (routing)": {
        "sys_a": "You are a helpful assistant.",
        "user_a": "What is the capital of France?",
        "sys_b": "You are a helpful assistant.",
        "user_b": "What is the capital of France?",
        "note": "The prompt is fine — but a factual one-liner does not need the flagship model. Switch the sidebar model to a cheaper one (e.g. gpt-4o-mini or claude-haiku-4-5) for Version B.",
    },
    "3. Rambling instructions (output control)": {
        "sys_a": "You are a helpful assistant. Give thorough, detailed answers.",
        "user_a": "Explain what HTTPS is.",
        "sys_b": "You are a helpful assistant. Answer in one short sentence.",
        "user_b": "Explain what HTTPS is in one sentence.",
        "note": "Cut output length in both the system prompt and the user prompt.",
    },
    "4. Stuffed context (trimming)": {
        "sys_a": "You are a helpful assistant. Use the following context.",
        "user_a": ("CONTEXT:\n" + ("Acme was founded in 2005. It has 500 employees. HQ in Austin. " * 40)
                   + "\n\nQUESTION: When was Acme founded?"),
        "sys_b": "You are a helpful assistant.",
        "user_b": "Acme was founded in 2005. When was Acme founded?",
        "note": "Keep only the sentence relevant to the question. Massive input savings.",
    },
    "5. Free-text where JSON works (structured output)": {
        "sys_a": "You are a helpful assistant.",
        "user_a": "Tell me the pros and cons of remote work.",
        "sys_b": "You are a helpful assistant. Respond in JSON with keys 'pros' (list of 3 strings) and 'cons' (list of 3 strings). No prose.",
        "user_b": "Pros and cons of remote work.",
        "note": "Structured output caps verbosity and makes the response cheaper and easier to use.",
    },
}


# ---------- Load example ----------
st.divider()
picked = st.selectbox("Load a before/after example", list(EXAMPLES.keys()))
if picked and EXAMPLES[picked]:
    ex = EXAMPLES[picked]
    st.session_state.sys_a  = ex["sys_a"]
    st.session_state.user_a = ex["user_a"]
    st.session_state.sys_b  = ex["sys_b"]
    st.session_state.user_b = ex["user_b"]
    st.session_state.note   = ex["note"]

if "sys_a" not in st.session_state:
    st.session_state.sys_a = "You are a helpful assistant."
    st.session_state.user_a = "Write two paragraphs about the history of the Eiffel Tower."
    st.session_state.sys_b = "You are a helpful assistant. Be concise."
    st.session_state.user_b = "In 2 short sentences: history of the Eiffel Tower."
    st.session_state.note = ""

if st.session_state.note:
    st.info(st.session_state.note)


# ---------- Two side-by-side prompt panels ----------
col_a, col_b = st.columns(2, gap="large")


def prompt_panel(label: str, key_prefix: str, run_key: str):
    st.subheader(label)
    sys_p = st.text_area("System prompt", key=f"sys_{key_prefix}", height=110)
    usr_p = st.text_area("User prompt",   key=f"user_{key_prefix}", height=140)

    in_tok_estimate = count_tokens(sys_p) + count_tokens(usr_p)
    st.caption(f"Input tokens (estimate): {in_tok_estimate}")

    return st.button(f"Run {label}", key=run_key, type="primary", use_container_width=True), sys_p, usr_p


with col_a:
    run_a, sys_a, user_a = prompt_panel("Version A (baseline)", "a", "run_a")

with col_b:
    run_b, sys_b, user_b = prompt_panel("Version B (optimized)", "b", "run_b")


# ---------- Run handlers ----------
def do_call(sys_p: str, user_p: str) -> dict:
    resp = call(model, user_p, sys_p, max_tokens=1000, keys=st.session_state.api_keys)
    return {
        "text": resp.text,
        "input_tokens": resp.input_tokens,
        "output_tokens": resp.output_tokens,
        "cost": cost(model, resp.input_tokens, resp.output_tokens),
        "mocked": resp.mocked,
        "model": model,
    }


if run_a:
    with st.spinner("Running Version A..."):
        st.session_state.result_a = do_call(sys_a, user_a)

if run_b:
    with st.spinner("Running Version B..."):
        st.session_state.result_b = do_call(sys_b, user_b)


# ---------- Results panels ----------
def result_panel(container, result: dict | None, label: str):
    with container:
        if result is None:
            st.caption(f"Run {label} to see results.")
            return
        m1, m2, m3 = st.columns(3)
        m1.metric("Input tokens",  result["input_tokens"])
        m2.metric("Output tokens", result["output_tokens"])
        m3.metric("Cost per call", f"${result['cost']:.5f}")
        with st.expander("Model response"):
            if result["mocked"]:
                st.warning("Using MOCK response (no API key). Cost math is still real.")
            st.write(result["text"])


st.divider()
res_col_a, res_col_b = st.columns(2, gap="large")
result_panel(res_col_a, st.session_state.result_a, "Version A")
result_panel(res_col_b, st.session_state.result_b, "Version B")


# ---------- Comparison ----------
a, b = st.session_state.result_a, st.session_state.result_b
if a and b:
    st.divider()
    st.subheader("Comparison")

    saved_per_call = a["cost"] - b["cost"]
    saved_pct = (saved_per_call / a["cost"] * 100) if a["cost"] > 0 else 0
    saved_monthly = saved_per_call * monthly_calls

    c1, c2, c3 = st.columns(3)
    c1.metric("Savings per call", f"${saved_per_call:.5f}", f"{saved_pct:.1f}%")
    c2.metric("Input token change",  f"{b['input_tokens'] - a['input_tokens']:+}")
    c3.metric(f"Monthly savings ({monthly_calls:,} calls)", f"${saved_monthly:,.2f}")

    fig = go.Figure(data=[
        go.Bar(name="Version A", x=["Input tokens", "Output tokens", "Cost per call (x1000)"],
               y=[a["input_tokens"], a["output_tokens"], a["cost"] * 1000],
               marker_color="#ef4444"),
        go.Bar(name="Version B", x=["Input tokens", "Output tokens", "Cost per call (x1000)"],
               y=[b["input_tokens"], b["output_tokens"], b["cost"] * 1000],
               marker_color="#22c55e"),
    ])
    fig.update_layout(barmode="group", height=320, margin=dict(l=10, r=10, t=30, b=10),
                      legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig, use_container_width=True)


# ---------- Techniques reference ----------
st.divider()
with st.expander("Five techniques to try (reference)"):
    st.markdown("""
**1. Prompt caching** — Repeated system prompts get a discount when marked cacheable.
Anthropic gives roughly 90% off cached input tokens. OpenAI roughly 50%.
*Try it:* keep your system prompt identical across calls and add the provider's cache marker.

**2. Model routing** — Send simple prompts to a cheaper model in the same family.
gpt-4o-mini is ~16x cheaper than gpt-4o. claude-haiku is ~4x cheaper than claude-sonnet.
*Try it:* switch the sidebar model for Version B and compare.

**3. Prompt compression** — Rewrite verbose instructions in fewer words. Trim redundant style rules.
*Try it:* shorten the system prompt in Version B.

**4. Context trimming** — Do not send the entire chat history or full documents. Send only the relevant slice, or a summary.
*Try it:* delete irrelevant context from the user prompt in Version B.

**5. Output control** — Cap max_tokens and use JSON mode. Output tokens usually cost 3-5x more than input.
*Try it:* tell the model to answer in one short sentence, or in JSON with fixed keys.
""")
