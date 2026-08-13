# 🎬 Slide Deck Outline (7 slides, minimal text)

Use Google Slides or PowerPoint. Dark background, one big idea per slide.

---

**Slide 1 — Title**
> Prompt Cost Lab
> Cutting LLM cost by 90% without changing models
> *[Your name] · [Date]*

---

**Slide 2 — The hook**
> ONE BIG NUMBER (centered, huge):
> **$47,000 → $6,000**
> *Same model. Same product. Same users.*

---

**Slide 3 — Why costs explode**
> Three silent leaks:
> - Reused system prompts, full price every call
> - Ferrari model for milk-run queries
> - No `max_tokens` cap → the model rambles

---

**Slide 4 — The 5 techniques**
> 1. Prompt caching
> 2. Model routing
> 3. Semantic cache
> 4. Context trimming
> 5. Output control
> *(Live demo coming up)*

---

**Slide 5 — LIVE DEMO placeholder**
> "Let's see it work →"
> *(alt-tab to Streamlit app; toggle each technique)*

---

**Slide 6 — Combined result**
> Screenshot of app with all 5 toggles on
> Big text below: **92% savings**
> "At 100k calls/mo = $X saved. That's a headcount."

---

**Slide 7 — Do these tomorrow**
> 1. Turn on prompt caching (3 lines)
> 2. Audit which model each call uses
> 3. Set `max_tokens` on every endpoint
>
> App: [your-url].streamlit.app
> Code: github.com/[you]/prompt-cost-lab
