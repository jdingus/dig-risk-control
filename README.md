# Call before you dig. Test before you trust.

![Call before you dig. Test before you trust.](assets/round2-811.png)

**Status: in progress.** The data is built and verified. Questions come next, committed before any folder or run.

Can a folder help a model answer actuarial questions (frequency, severity, repeat rate, trend) about
9,958 Indiana dig-damage enforcement cases? That's about 1.9M tokens, too big to paste into one prompt.

- `data/`: the 58 state orders (2021–2025) and the 2025 law, unchanged, plus every parsing and cleaning
  step as a committed script. Start at [data/README.md](data/README.md).
- `assets/`: slides. [round2-actuary.png](assets/round2-actuary.png) shows the question. [round2-problem.png](assets/round2-problem.png)
  is a first draft we dropped: it asked about a single contractor, and a text search answers that.

Round 1, the pilot on the dig law itself, is the separate repo `indiana-dig-law-control`.
