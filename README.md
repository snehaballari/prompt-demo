# 💸 Prompt Cost Lab

Interactive demo of **5 LLM cost-optimization techniques**. Toggle each on/off and watch cost drop live.

Built for a 10-minute AI-accelerator talk. Stack: **Streamlit + Python**. Hosting: **Streamlit Community Cloud** (free).

## Techniques demoed

1. **Prompt caching** — reuse discount on repeated system prompts (Anthropic 90% off, OpenAI 50% off).
2. **Model routing** — send simple prompts to a cheaper model in the same family.
3. **Semantic cache** — return a prior answer when a new prompt is ≥85% similar.
4. **Context trimming** — cut runaway history down to the last 500 tokens.
5. **Output control** — cap `max_tokens` so the model doesn't ramble.

Supports **OpenAI, Anthropic, Google Gemini, Groq (free)**. Works with no key at all — mocked responses still power the cost math.

---

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501.

## Deploy to Streamlit Community Cloud (free, ~60 seconds)

1. **Create a GitHub repo** (empty, public or private):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Prompt Cost Lab"
   git branch -M main
   git remote add origin https://github.com/<your-username>/prompt-cost-lab.git
   git push -u origin main
   ```

2. Go to **https://share.streamlit.io** → sign in with GitHub.
3. Click **"New app"** → pick your repo → main file: `app.py` → **Deploy**.
4. You get a public URL like `https://prompt-cost-lab-<you>.streamlit.app`.

Every `git push` auto-redeploys.

## Get a free Groq key

https://console.groq.com — free tier, very fast Llama-3 inference. Perfect for the demo.

## File map

- `app.py` — Streamlit UI
- `optimizations.py` — the 5 techniques
- `providers.py` — OpenAI / Anthropic / Google / Groq unified interface
- `pricing.py` — per-token pricing table
- `.streamlit/config.toml` — dark theme
