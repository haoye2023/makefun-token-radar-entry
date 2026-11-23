# Token Launch Radar

[![bounty](https://make.fun/badge/token-radar-01.svg)](https://make.fun/bounty/token-radar-01?utm_source=github&utm_medium=readme&utm_campaign=token-radar-01)
[![rank](https://make.fun/badge/token-radar-01/haoye2023/makefun-token-radar-entry/rank.svg)](https://make.fun/bounty/token-radar-01?utm_source=github&utm_medium=readme&utm_campaign=token-radar-01)
[![reward](https://make.fun/badge/token-radar-01/haoye2023/makefun-token-radar-entry/reward.svg)](https://make.fun/bounty/token-radar-01?utm_source=github&utm_medium=readme&utm_campaign=token-radar-01)

Entry for the make.fun bounty [Build the best token launch radar](https://make.fun/bounty/token-radar-01?utm_source=github&utm_medium=readme&utm_campaign=token-radar-01).

The radar reads a sealed DefiLlama snapshot of 758 protocols, finds the ones
that record no token yet and are not a wrapped, staked, bridged or versioned
product of something else, ranks them by the value their token launch would
have if their record stayed as it is, and hands the reader a concrete farm
plan for each one. All 40 watchlist protocols are on the board, along with
every other eligible pre-token protocol the snapshot carries (198 rows).

## How the model works

Implied value is **TVL × category multiple × momentum × maturity × chain
breadth**, and every input is derived from the snapshot itself — no protocol
name is ever scored by hand:

- **Category multiple** — the median market-cap/TVL ratio of token-bearing
  protocols in the same DefiLlama category, measured on this snapshot
  (categories with fewer than three priced tokens fall back to the global
  median). A pre-token lending market is priced the way the market already
  prices lending markets that have a token.
- **Momentum** — the protocol's 7-day TVL change, clamped to −40%…+60% and
  damped by 0.6 (one week of flow is the noisiest figure in the snapshot).
  Unreported change is neutral.
- **Maturity** — how long the protocol has been tracked with no token
  recorded: the factor rises linearly from 0.75 to 1.25 over four years.
  Longer tokenless at scale means a launch is worth more when it comes.
- **Chain breadth** — +3% per additional chain beyond the first, capped
  at +24%.

Farm plans come from per-category playbooks (DEX, lending, yield, curator,
RWA, derivatives, stablecoin, chain, …) parameterised with each protocol's
own name, main chain and TVL tier, so every plan names concrete actions with
dollar budgets and time commitments.

## The dashboard

`dashboard/` is a static page that renders with no network: a sortable,
filterable board (category, chain, text search, watchlist-only), a detail
view per protocol with its model factor breakdown and farm steps, and a
"How the model works" note with the category multiples measured on the
snapshot. `main.ts` writes its data as `zdata.js` beside the page in the
output.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts --input <path-to-snapshot.json>
```

Requires Node.js 22.18 or later; standard library only. The run writes
`board.json`, `dashboard/` (with `zdata.js`), `screenshots/` and
`dossier.json` into the output directory, and is deterministic: the same
snapshot always produces the same bytes.

## Screenshots

The three screenshots in `screenshots/` are drawn from the real board data
by `scripts/make_screenshots.py` (Python + PIL), in the dashboard's own
palette and layout: the board, the top protocol's detail view, and a
category-filtered view.

## License

MIT — see `LICENSE`.
