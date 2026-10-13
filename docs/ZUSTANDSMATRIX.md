# Versionierte Zustandsmatrix & Fortschreibungsregeln

Ziel → Entscheidungsfragen → je 3 getrennte Fachbewertungen → prüfbares Systemdesign.
Referenzimplementierung: [`decision_matrix.py`](decision_matrix.py).

## 1. Architektur
- **Quelle der Wahrheit:** append-only Event-Log, hash-verkettet (SHA-256, `prev`-Zeiger).
- **Matrix:** reine Projektion des Logs (Replay ⇒ reproduzierbar). Details (Bewertungen, Evidenz) liegen außerhalb, Matrix hält nur IDs/Kurzcodes ⇒ Größe O(|Q|).
- **Version:** `MAJOR.MINOR.PATCH` — MAJOR = Ziel/Kriterien geändert, MINOR = Entscheidung gesetzt/ersetzt, PATCH = Evidenz/Redaktion ohne Ergebnisänderung.

## 2. Matrix-Schema (eine Zeile je Entscheidungsfrage)
| Spalte | Inhalt | Beispiel |
|---|---|---|
| `Q` | ID | Q1 |
| `K` | Kriterien-IDs (Rückbezug zum Ziel) | K1,K3 |
| `Dep` | vorausgesetzte Q (DAG) | – |
| `Opt` | Optionen | FILE/KMS/MPC |
| `B1..B3` | `Rolle:Option:Score:Konf` | SEC:KMS:2.6:.8 |
| `Ent` | gewählte Option + ADR-ID | KMS (ADR-001) |
| `St` | OPEN · ASSESSING · DECIDED · CONFLICT · ESCALATED · STALE | DECIDED |
| `v` / `h` | Version / Event-Hash (8 Zeichen) | 1.1.0 / 3fa2c9e1 |

## 3. Fortschreibungsregeln
| # | Regel | Prüfkriterium |
|---|---|---|
| R0 | Ziel G₀ einfrieren, in Kriterien K (Gewichte Σ=1, Muss-Kriterien markiert) zerlegen | Hash(G₀) im Genesis-Event |
| R1 | Jede Q referenziert ≥ 1 K; Abhängigkeiten azyklisch | Coverage K→Q = 100 %, DAG-Check |
| R2 | 3 Rollen deterministisch per Tag-Überdeckung wählen; ≥ 2 Disziplinen, ≥ 1 adversariale Rolle (Security/Compliance) | Auswahl replaybar |
| R3 | Bewertungen blind & getrennt (eigener Kontext, nur Q + K + geschlossene Vorentscheidungen) | kein Zugriff auf fremde Voten |
| R4 | Bewertung = Score je K (0–3), Muss-Pass/Fail, Konfidenz, Annahmen, **≥ 1 Evidenz-Ref** | sonst ungültig |
| R5 | Aggregation: Veto bei Muss-Fail → Median je K → gewichtete Summe → Marge ≥ δ und Streuung ≤ 1 ⇒ DECIDED, sonst CONFLICT | deterministisch |
| R6 | CONFLICT: 1 Delphi-Runde (anonymisierte Begründungen), danach ESCALATED an Zielverantwortliche | max. 2 Runden |
| R7 | Änderung an Q oder Annahme ⇒ transitive Abhängige → STALE, nur diese neu bewerten | Propagation im Log |
| R8 | Jede Zustandsänderung = 1 Event + Versionssprung | `verify()` = true |
| R9 | Abschluss: alle Q DECIDED, kein STALE, paarweise Konsistenz, Design-Element → ADR → K → G₀ lückenlos | Traceability 100 % |

## 4. Invarianten (Audit-Checkliste)
- Hash-Kette lückenlos; Replay des Logs ergibt identische Matrix.
- Keine Entscheidung ohne 3 gültige Bewertungen von 3 verschiedenen Rollen.
- Keine DECIDED-Q mit STALE-Vorgänger.
- Jedes Muss-Kriterium in jeder gewählten Option erfüllt.
