# Results

The study used 4,514 calibration intervals ending in 2004–2021 and 750 out-of-sample intervals ending in 2022–2024. The 21-interval historical test uses 35 disjoint paths, with 15 trailing intervals unused. The August stress replay is entirely outside calibration.

| 15×, annual spread 50 bp | P95 drawdown / initial margin | P05 closeout return | Breach fraction | MC standard error |
|---|---:|---:|---:|---:|
| Gaussian, 4,000 paths | 73.30% | −65.70% | 11.95% | 0.51 pp |
| Five-interval blocks, 4,000 paths | 76.75% | −67.02% | 11.75% | 0.51 pp |
| 2022–24 replay, 35 paths | 77.68% | −64.79% | 5/35 | — |

Two- and ten-interval FX blocks gave 11.08% and 11.68% breach rates at those settings. With five-interval blocks, the 0- and 150-bp cost assumptions gave 11.43% and 12.38%. Path generators share sampled interest-rate and accrual schedules; bootstrap blocks preserve short FX dependence. The Monte Carlo errors describe simulation sampling conditional on each fitted generator. Model assumptions and sampling-window differences contribute additional uncertainty.

## August replay and hand check

Using JPY per USD, the Aug. 2–5 observation moved from 146.98 to 143.95. Over three calendar days, receive 5.33% × 3/365 in USD per dollar notional. Repaying the yen position costs (146.98/143.95) × [1 + (0.077% + 0.50%) × 3/365] in dollars. Subtract that from 1 plus the USD accrual. This is the FX loss plus net interest, a yen interest conversion interaction, and the funding spread cost. Trade entry and closing each cost one additional basis point when executed.

Across Aug. 1–5 the separate daily rolls accrued $0.0576 of net interest per $100 notional against a $4.2004 FX loss before funding spread and execution. The 8× mark survived the stress replay and recovered to a −14.21% closing return by Aug. 7. The 15× position liquidated earlier and did not participate in that recovery. The 25× modeled closeout was below zero equity because the next noon mark can gap past the liquidation threshold. Intraday fills, stop execution, market impact and deposit constraints are outside this stylized scenario.

The replay does not infer that any observed trade used this leverage or funding. The BIS report provides market context for the August episode. [BIS](https://www.bis.org/publications/qr-202409/carry-off-carry-on)
