# ADR-001 — Q-ALG-1: Signal-Algorithmus für `trading/monitor.js`

| Feld | Wert |
|---|---|
| Status | DECIDED (bedingt, Validierungs-Gate offen) |
| Version / Head | 1.1.0 / `32fb5af6` (`Q-ALG-1.ledger.json`, `verify() = true`) |
| Router (R2) | QNT (3 Tag-Treffer) · OPS (2) · RSK (2, adversarial) |
| Replay | `python3 -I docs/decisions/run_q_alg_1.py` |

## Matrix-Zeile
| Q | K | Opt | B1 QNT | B2 OPS | B3 RSK | Ent | St |
|---|---|---|---|---|---|---|---|
| Q-ALG-1 | signal,risk,robust,impl | A0–A3 | A1:2.0:.55 | A1:2.0:.60 | A1:1.5:.55 | **A1** | DECIDED |

## Aggregation (R5: Veto → Median je Kriterium → Σ Gewicht)
| Option | signal (0,3) | risk (0,3) | robust (0,2) | impl (0,2) | Σ | max. Streuung |
|---|---|---|---|---|---|---|
| A0 Status quo | 0 | 1 | 1 | 3 | 1,10 | 1 |
| **A1 Trend/TSMOM + ATR-Trail** | **2** | **2** | **2** | **2** | **2,00** | 1 |
| A2 Mean-Reversion | 0 | 1 | 1 | 2 | 0,90 | 1 |
| A3 ML-Klassifikator | 1 | 1 | 0 | 1 | 0,80 | 1 |

- Veto: keines (alle hard_ok = true). Marge A1 − A0 = 0,90 ≥ δ = 0,25. Streuung ≤ 1 ⇒ kein CONFLICT, keine Delphi-Runde.

## Entscheidung
**A1** — langsames Trend-Following (Donchian-/EMA-Breakout auf 6 h–1 d-Kerzen), volatilitätsskalierte Größe (Cap 50 USD), ATR-Trailing-Stop + fester Hard-Stop.

### Auflagen (aus allen 3 Bewertungen, unabhängig von der Option)
1. Exit-Bug: fixe 6 Decimals (`monitor.js:315`) → Decimals on-chain lesen.
2. `MAX_DAILY_LOSS` wird nie gelesen (`.env.example:30`) → implementieren.
3. `entryPrice` = DexScreener-Preis statt Fill (`monitor.js:225`) → Fill-Preis aus Swap.
4. Universum: liquide/verifizierte Tokens statt Trending-Liste; Token-Sicherheitsfilter (Mint-/Freeze-Authority, LP-Lock).
5. Preis-Ringpuffer persistieren (Warm-up) oder OHLCV-API (GeckoTerminal).

### Validierungs-Gate (vor Live-Betrieb)
- Evidenz für A1 stammt von CEX-Majors/Perps, **nicht** von Solana-DEX-Altcoins; keine Option hat positiven Erwartungswert nach 0,5–2 % Kosten nachgewiesen.
- Pflicht: Walk-forward-Backtest + ≥ 2 Wochen `DRY_RUN=true`; Abbruch, wenn Netto-Erwartungswert ≤ 0.

## Quellen (verifiziert via alphaXiv/Websuche)
- arXiv:2603.24625 Rug Pulls auf Solana · arXiv:2504.07132 SolRPDS · arXiv:2606.08232 Memecoin-Bot Solana
- arXiv:2606.00060 ML-BTC-Trading unter Kosten · arXiv:2608.21888 Mean-Reversion Krypto
- arXiv:2602.11708 Trend-Following + ATR-Trail (Preprint, optimistisch) · arXiv:2607.01550 Ende des kurzfristigen Trend-Following (Futures)
- arXiv:2510.14435 Krypto-Momentum (Querschnitt) · arXiv:2504.18055 Solana-Transaktionsfehler · arXiv:2209.05559 / DOI:10.21314/JCF.2016.322 Backtest-Overfitting
- DOI:10.1093/rfs/hhaa113 Liu & Tsyvinski 2021 · DOI:10.1016/j.finmar.2013.07.001 Kaminski & Lo 2014
- arXiv:2610.10149 nur **teilweise** gestützt (Honeypot-Schemes, BSC/ETH) — in RSK-Bewertung korrigiert (PATCH).
