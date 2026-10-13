"""Replay von Q-ALG-1: Routing (R2) -> Bewertungen (R4) -> Aggregation (R5) -> Ledger (R8)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from decision_matrix import Assessment, Ledger, Question, aggregate, select_assessors  # noqa: E402

CRITERIA: dict[str, float] = {"signal": 0.30, "risk": 0.30, "robust": 0.20, "impl": 0.20}
TAGS: set[str] = {"signal", "backtest", "statistics", "risk", "drawdown", "ops", "latency"}


def load(q: Question, roles: list[str], rnd: int) -> None:
    """R4: Bewertungen der gerouteten Rollen laden (Runde rnd)."""
    for role in roles:
        suffix = f".r{rnd}" if rnd > 1 else ""
        data = json.loads((HERE / f"Q-ALG-1.{role}{suffix}.json").read_text())
        assert data["role"] == role
        for a in data["assessments"]:
            q.assessments.append(Assessment(role, a["option"], a["scores"], a["hard_ok"],
                                            a["confidence"], tuple(a["evidence"])))


def weighted(q: Question) -> dict[str, dict[str, float]]:
    """Diagnose: gewichtete Summe je Rolle und Option."""
    out: dict[str, dict[str, float]] = {}
    for a in q.assessments:
        out.setdefault(a.option, {})[a.role] = round(
            sum(w * a.scores[c] for c, w in CRITERIA.items()), 2)
    return out


def main(rnd: int = 1) -> None:
    q = Question("Q-ALG-1", TAGS, CRITERIA, ("A0", "A1", "A2", "A3"))
    led = Ledger()
    led.append("GOAL", {"ref": "config/AGENTS.md", "criteria": CRITERIA}, "major")
    roles = select_assessors(q)
    led.append("ROUTE", {"q": q.qid, "roles": roles}, "patch")
    load(q, roles, rnd)
    digests = {r: hashlib.sha256((HERE / f"Q-ALG-1.{r}.json").read_bytes()).hexdigest()[:16]
               for r in roles}  # Inhalt der Bewertungen fließt in die Hash-Kette ein
    led.append("ASSESS", {"q": q.qid, "round": rnd, "n": len(q.assessments),
                          "sha256": digests}, "patch")
    status, decision = aggregate(q)
    led.append("AGGREGATE", {"q": q.qid, "status": status, "decision": decision},
               "minor" if status == "DECIDED" else "patch")
    print(json.dumps({"roles": roles, "per_role": weighted(q), "status": status,
                      "decision": decision, "version": led.version,
                      "head": led.events[-1]["hash"][:8], "verify": led.verify()}, indent=1))
    (HERE / "Q-ALG-1.ledger.json").write_text(json.dumps(led.events, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
