# 🎤 10-Minute Presentation Script — "Prompt Cost Lab"

> Target: 8 minutes talk + 2 minutes Q&A. Delivered slightly slower than casual conversation. Practice out loud 3× on video.

---

## Slide 1 — Hook (0:00 → 0:40)

> "Quick show of hands — how many of you have looked at your OpenAI or Anthropic bill this month and thought *'wait, this can't be right'*?
>
> Yeah. Same.
>
> Last month, a team I know was spending forty-seven thousand dollars on GPT-4. In two days of optimization work, we brought it down to **six thousand**. Same model. Same product. Same users.
>
> Today I want to show you the five techniques we used — and I've built a small app so you can try each one live. The link is going into the chat right now."

*(share URL in chat)*

---

## Slide 2 — Why costs explode (0:40 → 1:30)

> "Here's the problem: **LLM cost is a silent leak.** Three things kill your bill:
>
> One — you send the same big system prompt on every call, and pay full price every time.
> Two — you use your strongest model for questions your cheapest one could answer.
> Three — you let the model ramble because nobody set `max_tokens`.
>
> None of these show up in code review. They only show up on the invoice.
>
> The good news: **all five fixes I'll show you are one-day work.** No model change, no vendor switch."

---

## Slide 3 — The 5 techniques *(one line each)* (1:30 → 2:00)

> "Here they are. Prompt caching. Model routing. Semantic cache. Context trimming. Output control. I'll demo each one live now."

*(switch to the app — sidebar visible, all toggles OFF)*

---

## Demo 1 — Prompt caching (2:00 → 3:00)

*(pick a preloaded example with a long system prompt, click Run — toggles all off)*

> "Baseline call. Look at the cost — the system prompt alone is 300 tokens, and we pay full price for it on every single call, even though it never changes.
>
> Now watch this. **Toggle prompt caching on. Re-run.**
>
> Boom. Same output — but on Anthropic, cached input is **90% cheaper**. On OpenAI, 50%. If you're a support bot handling 100,000 tickets a month with the same system prompt, this one toggle saves you thousands. Zero code change beyond adding a `cache_control` marker."

---

## Demo 2 — Model routing (3:00 → 4:00)

*(pick "Short factual Q" — "What's the capital of France?")*

> "Second technique. Right now we're using GPT-4o for *'What's the capital of France?'*. That's like taking a Ferrari to buy milk.
>
> **Toggle Model Routing on. Re-run.**
>
> See the badge? It auto-classified this as a simple prompt and routed to GPT-4o-mini — sixteen times cheaper. For complex prompts, it still uses the strong model. A tiny classifier at the front of your pipeline captures most of the savings people chase from fine-tuning — with none of the effort."

---

## Demo 3 — Semantic cache (4:00 → 5:00)

*(pick "Repetitive support ticket" — "How do I reset my Acme Cloud password?" — run, then paraphrase and re-run)*

> "Third one. In production, users ask *the same question ten different ways*.
>
> First call — normal cost.
>
> Now I'll rephrase — with **semantic cache toggled on** — *"Can you help me reset my Acme Cloud password?"*
>
> **Cost: zero. Latency: 40 milliseconds.** The cache matched at 87% similarity and returned the previous answer. In a support product, 30 to 70% of traffic hits this cache. It's the single biggest lever most teams haven't pulled."

---

## Demo 4 — Context trimming (5:00 → 5:45)

*(pick "Long analysis" example — toggle Context Trimming)*

> "Fourth. Long chat threads bloat input tokens fast. A 20-turn conversation can be 8,000 tokens of history — most of it irrelevant.
>
> **Trim on. Re-run.**
>
> We keep the last 500 tokens and drop the rest. In production you'd swap the drop for a summary — same idea. Watch the input tokens fall off a cliff."

---

## Demo 5 — Output control (5:45 → 6:15)

*(any prompt, toggle Output Control)*

> "Fifth, the simplest of all. **Toggle Output Control.**
>
> Cap `max_tokens` at 150. That's it. No more three-paragraph answers when you asked for a yes/no. Combine it with JSON mode and structured outputs and your output cost — which is 3–5× your input cost — drops sharply."

---

## Slide 4 — All five together (6:15 → 7:15)

*(toggle ALL FIVE on — same prompt from Demo 1 — re-run)*

> "Now let's stack them. All five techniques on. Same prompt. Same model family.
>
> Ninety-two percent savings.
>
> And here" *(scroll to projection)* — "at 100,000 calls a month, this is what your invoice looks like. That's a headcount. That's runway."

---

## Slide 5 — Takeaways (7:15 → 8:00)

> "Three things to try at your desk tomorrow.
>
> **One** — turn on prompt caching. It's usually 3 lines of code. Do it today.
> **Two** — audit *which* model each call uses. You'll find at least one place where a cheaper model works fine.
> **Three** — put a `max_tokens` cap on every endpoint. Rambling responses are 100% waste.
>
> The app is at [YOUR-URL]. Code is on GitHub. Steal it, fork it, ship it.
>
> Happy to take questions."

---

## Anticipated questions + short answers

**Q: How accurate is semantic caching? Won't it return wrong answers?**
> "It only fires above 85% similarity, and you tune that threshold. For FAQs and support it's very safe. For math or code — turn it off."

**Q: Does prompt caching work for everyone?**
> "Anthropic and OpenAI both support it now. Different pricing — Anthropic gives 90% off cached input; OpenAI gives 50%. Both charge a small write premium the first time, so it pays back after ~2 calls."

**Q: What about fine-tuning instead?**
> "Fine-tuning wins if you have thousands of consistent examples *and* your prompt is huge. For most teams, these five techniques get you 80% of the savings for 5% of the effort. Do these first."

**Q: How do I know which technique to try first?**
> "Prompt caching. Highest ROI, lowest risk, works even if nothing else changes."

---

## Delivery tips

- **Pace:** slower than you think. Silence is your friend after a big number.
- **Big numbers:** always say the dollar figure. "$47,000 to $6,000" hits harder than "87% reduction."
- **Eye contact:** during each demo, look up at the audience while the model call runs. Don't stare at the screen.
- **If a demo fails:** don't panic. Say *"live demos, everyone's favorite"* — refresh, keep going. Have a screenshot fallback on slide.
- **Time check:** at slide 4 you should be at 6:15. If you're at 7:00, skip Demo 4's second toggle. If you're at 5:30, expand the "monthly savings" moment.
