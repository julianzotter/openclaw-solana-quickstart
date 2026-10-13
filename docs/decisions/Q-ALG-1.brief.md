# Q-ALG-1 — Bewertungsauftrag (identisch für alle Bewerter)

**Frage:** Welcher Signal-/Handelsalgorithmus soll Entry/Exit in `trading/monitor.js` steuern?
**Ziel G₀ (config/AGENTS.md):** Kapitalerhalt zuerst, Gewinn zweitens; Spot-Long-only über Jupiter (Solana), Positionsgröße ≤ 50 USD, max. 3 Positionen, Daily-Loss-Limit 100 USD, Slippage ≤ 1 %.

## Datenlage (Fakt, Repo)
- DexScreener-Pair-Daten: priceUsd, priceChange m5/h1/h6/h24, volume, txns, liquidity, fdv. **Keine Kerzenhistorie.**
- Eigene Preisreihe entsteht durch Polling alle 30 s (`SCAN_INTERVAL`), OHLCV nur über Zusatz-API (z. B. GeckoTerminal/Birdeye).
- Kosten je Round-Trip realistisch ≈ 0,5–2 % (Slippage + Pool-Fee + Priority-Fee).

## Optionen
- **A0 Status quo:** Filter priceChange h24 > +5 %, vol24h > 50k, Liquidität > 100k, FDV > 100k aus DexScreener-Trending; fix SL −10 %, TP +50 %, Timeout 4 h.
- **A1 Trend-Following / Time-Series-Momentum:** Donchian-Breakout oder EMA-Crossover auf eigener Preisreihe, volatilitätsskalierte Positionsgröße, ATR-Trailing-Stop.
- **A2 Mean-Reversion (kurzfristig):** RSI-/Bollinger-Überverkauft-Entry (long-only), Exit am Mittelwert, enger Stop.
- **A3 ML-Klassifikator:** Gradient Boosting auf Features (Returns m5/h1/h6, Volumen, Txns, Liquidität) → Vorzeichen der nächsten Stunde; Schwellwert-Entry, gleiche Risiko-Exits.

## Kriterien (Score 0–3; 0 = schlecht, 3 = sehr gut)
- **K1 signal (0,30):** empirische Evidenz für positiven Erwartungswert nach Kosten bei Krypto/Altcoins.
- **K2 risk (0,30):** Drawdown-/Tail-Kontrolle, Verträglichkeit mit Kapitalerhalt.
- **K3 robust (0,20):** Overfitting-Risiko, Regimeabhängigkeit, Parameterzahl, Out-of-Sample-Evidenz.
- **K4 impl (0,20):** Umsetzbarkeit mit obiger Datenlage in Node.js, Latenz, Betriebsaufwand.

## Muss-Kriterien (hard_ok = beide erfüllt)
- **M1:** long-only Spot ohne Hebel/Short umsetzbar.
- **M2:** harter Stop-Loss + Positionslimits integrierbar.

## Ausgabeformat (nur JSON, keine weiteren Texte am Ende)
```json
{"role": "<ROLLE>", "assessments": [
  {"option": "A0", "scores": {"signal": 0, "risk": 0, "robust": 0, "impl": 0},
   "hard_ok": true, "confidence": 0.0,
   "evidence": ["arXiv:XXXX.XXXXX | DOI:... | repo-datei:zeile — 1 Satz, was belegt wird"],
   "assumptions": ["..."]}
]}
```
Regeln: je Option ≥ 1 **verifizierbare** Quelle (arXiv-ID, DOI oder Repo-Stelle). Nichts erfinden — nicht verifizierbar ⇒ Quelle weglassen und Konfidenz senken. Scores ganzzahlig.
