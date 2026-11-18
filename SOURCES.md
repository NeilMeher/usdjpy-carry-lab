# Sources and data dictionary

Downloaded through FRED on 2026-11-18. Frozen output uses the nonmissing slice dated 2003-10-01 to 2024-12-31. The digest is computed from sorted ISO observation dates and values formatted to eight decimals. Source-hashes.json pins those observations while ignoring new rows outside the period. This is a retrieved historical extract, with no real-time-vintage claim.

| Series | Fields and coverage relevant to the study | Use and access |
|---|---|---|
| DEXJPUS | Yen per USD, New York noon buying rate, weekdays with observations | Fed H.10, public-domain series with citation requested. [FRED](https://fred.stlouisfed.org/series/DEXJPUS) |
| DFF | Effective federal funds rate, percent per year on daily dates | USD interest proxy, H.15, public-domain series with citation requested. [FRED](https://fred.stlouisfed.org/series/DFF) |
| IRSTCI01JPM156N | Monthly Japanese call/interbank short rate, percent per year | Yen proxy, OECD via FRED, copyrighted with citation required. Keep raw data local. [FRED](https://fred.stlouisfed.org/series/IRSTCI01JPM156N) |

Missing H.10 entries are excluded; calendar accrual runs between available observed rates. The lagged DFF lookup takes the latest available observation no later than two calendar days before the start. The Japanese rate uses the month two months before the start. This buffer is a conservative proxy for publication lag and uses revised data. Source observations do not measure executable funding or retail margin. The scenario grid uses fixed USD notional, illustrative bilateral transaction and funding costs, and liquidation at sampled prices.

The simulator input is log spot change, accrued USD rate, accrued yen rate and years elapsed. The output CSV contains generator/length, funding cost in annual basis points, leverage, path count, drawdown and closeout quantiles, breach fraction and Monte Carlo sampling error. Values are fractions unless the unit says otherwise. The public CSV aggregates simulation output and never lists raw series observations.
