"""Auto-Optimize page — user pastes a prompt, LLM rewrites it to use fewer tokens."""
from __future__ import annotations
import streamlit as st

from providers import call
from optimizations import count_tokens
from pricing import PRICING, cost

st.set_page_config(page_title="Auto-Optimize", layout="wide")

if "api_keys" not in st.session_state:
    st.session_state.api_keys = {"openai": "", "anthropic": "", "google": "", "groq": ""}
if "optimized" not in st.session_state:
    st.session_state.optimized = None

st.title("Auto-Optimize a Prompt")
st.write(
    "Paste any prompt. Click Optimize. A small model rewrites it to use fewer tokens "
    "while keeping the same intent. See how much your production prompt would cost before and after."
)

with st.sidebar:
    st.header("Setup")

    target_model = st.selectbox(
        "Target model (the model you would actually run in production)",
        list(PRICING.keys()),
        index=list(PRICING.keys()).index("gpt-4o"),
    )
    p = PRICING[target_model]
    st.caption(f"Input: ${p['in']} per million tokens. Output: ${p['out']} per million tokens.")

    monthly_calls = st.number_input("Calls per month (for savings projection)",
                                    1_000, 10_000_000, 100_000, step=10_000)

    st.divider()
    with st.expander("API keys (session only)", expanded=True):
        st.session_state.api_keys["groq"]   = st.text_input(
            "Groq key (free at console.groq.com)",
            type="password", value=st.session_state.api_keys["groq"],
        )
        st.session_state.api_keys["openai"] = st.text_input(
            "OpenAI key (used only if no Groq key)",
            type="password", value=st.session_state.api_keys["openai"],
        )
        st.caption("Groq is free. Add either key to run the optimizer. Without a key, the optimizer will not run.")


DEFAULT_PROMPT = (
    "Hey there! I was wondering if you could kindly help me out by writing a short "
    "and friendly-sounding email to my team letting them know that our weekly team "
    "meeting has been moved from Tuesday at 3pm to Wednesday at 4pm this week only. "
    "Please make it professional but warm, and add a little apology for the "
    "last-minute change. Thanks so much for your help!"
)

original = st.text_area("Your prompt", value=DEFAULT_PROMPT, height=180, key="original_prompt")

original_tokens = count_tokens(original)
original_cost   = cost(target_model, original_tokens, 300)

col1, col2 = st.columns(2)
col1.metric("Original tokens (input)", original_tokens)
col2.metric(f"Cost per call on {target_model}", f"${original_cost:.5f}",
            help="Assumes about 300 output tokens per response.")

run = st.button("Optimize this prompt", type="primary", use_container_width=True)


META_PROMPT = (
    "You are a prompt compression expert. Rewrite the following prompt to use the "
    "minimum possible tokens while preserving the user's intent.\n\n"
    "Rules:\n"
    "- Keep the same task or question exactly\n"
    "- Remove redundant phrasing, greetings, apologies, and filler words\n"
    "- Use imperative voice where possible\n"
    "- Do NOT add explanations, commentary, or quotation marks\n"
    "- Output ONLY the rewritten prompt on a single answer, nothing else\n\n"
    "Original prompt:\n"
)


def pick_optimizer() -> str | None:
    if st.session_state.api_keys["groq"]:
        return "llama-3.1-70b-versatile"
    if st.session_state.api_keys["openai"]:
        return "gpt-4o-mini"
    return None


if run:
    opt_model = pick_optimizer()
    if opt_model is None:
        st.error("Add a Groq key (free) or an OpenAI key in the sidebar, then click Optimize again.")
    else:
        with st.spinner(f"Rewriting with {opt_model}..."):
            resp = call(
                model=opt_model,
                prompt=META_PROMPT + original,
                system="You compress prompts.",
                max_tokens=500,
                keys=st.session_state.api_keys,
            )
        st.session_state.optimized = {
            "text": resp.text.strip().strip('"').strip("'"),
            "optimizer_model": opt_model,
            "mocked": resp.mocked,
        }


if st.session_state.optimized:
    o = st.session_state.optimized
    optimized_text   = o["text"]
    optimized_tokens = count_tokens(optimized_text)
    optimized_cost   = cost(target_model, optimized_tokens, 300)

    st.divider()
    st.subheader("Optimized prompt")

    if o["mocked"]:
        st.warning("Optimizer returned a mock response. Add a real API key in the sidebar to see actual compression.")
    st.caption(f"Rewritten by {o['optimizer_model']}")
    st.text_area("Rewritten prompt", value=optimized_text, height=140, disabled=True, label_visibility="collapsed")

    saved_tokens   = original_tokens - optimized_tokens
    saved_cost     = original_cost - optimized_cost
    saved_pct      = (saved_cost / original_cost * 100) if original_cost > 0 else 0
    monthly_saving = saved_cost * monthly_calls

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Optimized tokens", optimized_tokens, f"{-saved_tokens:+}",
              delta_color="inverse")
    c2.metric("Optimized cost per call", f"${optimized_cost:.5f}")
    c3.metric("Savings per call", f"${saved_cost:.5f}", f"-{saved_pct:.1f}%")
    c4.metric(f"Monthly savings ({monthly_calls:,} calls)", f"${monthly_saving:,.2f}")

    st.divider()
    st.subheader("Side by side")
    left, right = st.columns(2)
    with left:
        st.markdown("**Original**")
        st.code(original, language="text")
        st.caption(f"{original_tokens} tokens")
    with right:
        st.markdown("**Optimized**")
        st.code(optimized_text, language="text")
        st.caption(f"{optimized_tokens} tokens")

else:
    st.info("Enter a prompt above and click Optimize.")
