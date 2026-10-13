"""Referenzimplementierung: versionierte Zustandsmatrix + Fortschreibungsregeln.

Event-Log (append-only, hash-verkettet) = Quelle der Wahrheit.
Matrix = deterministische Projektion (replay) des Logs.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from statistics import median

ROLES: dict[str, set[str]] = {  # Rollenkatalog: Rolle -> Kompetenz-Tags
    "SEC": {"security", "keys", "risk"},
    "OPS": {"ops", "infra", "latency"},
    "FIN": {"risk", "cost", "capital"},
    "ARC": {"infra", "integration", "keys"},
    "LEG": {"compliance", "risk"},
}
ADVERSARIAL = {"SEC", "LEG"}  # mind. 1 Rolle mit Prüf-/Gegenposition


@dataclass(frozen=True)
class Assessment:
    role: str
    option: str
    scores: dict[str, int]          # Kriterium -> 0..3
    hard_ok: bool                   # alle Muss-Kriterien erfüllt
    confidence: float               # 0..1
    evidence: tuple[str, ...]       # Pflicht: >= 1 Referenz


@dataclass
class Question:
    qid: str
    tags: set[str]
    criteria: dict[str, float]      # Kriterium -> Gewicht (Summe 1)
    options: tuple[str, ...]
    deps: tuple[str, ...] = ()
    status: str = "OPEN"            # OPEN|ASSESSING|DECIDED|CONFLICT|ESCALATED|STALE
    decision: str | None = None
    assessments: list[Assessment] = field(default_factory=list)


def select_assessors(q: Question, k: int = 3) -> list[str]:
    """R2: deterministische Auswahl (Tag-Überdeckung, Tie-Break alphabetisch)."""
    ranked = sorted(ROLES, key=lambda r: (-len(ROLES[r] & q.tags), r))
    chosen = ranked[:k]
    if not ADVERSARIAL & set(chosen):  # Invariante: >= 1 adversariale Rolle
        adv = min(ADVERSARIAL, key=lambda r: (-len(ROLES[r] & q.tags), r))
        chosen[-1] = adv
    assert len(set(chosen)) == k
    return chosen


def aggregate(q: Question, delta: float = 0.25, max_spread: int = 1) -> tuple[str, str | None]:
    """R5: Veto (Muss-Kriterien) -> Median je Kriterium -> gewichtete Summe -> Marge."""
    assert all(a.evidence for a in q.assessments), "R4: Bewertung ohne Evidenz ungültig"
    totals: dict[str, float] = {}
    for opt in q.options:
        rows = [a for a in q.assessments if a.option == opt]
        if not rows or not all(a.hard_ok for a in rows):
            continue  # Veto: ein begründetes FAIL schließt Option aus
        for c in q.criteria:
            vals = [a.scores[c] for a in rows]
            if max(vals) - min(vals) > max_spread:
                return "CONFLICT", None
        totals[opt] = sum(w * median(a.scores[c] for a in rows) for c, w in q.criteria.items())
    if not totals:
        return "ESCALATED", None
    best = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    if len(best) > 1 and best[0][1] - best[1][1] < delta:
        return "CONFLICT", None
    return "DECIDED", best[0][0]


def propagate_stale(qs: dict[str, Question], changed: str) -> list[str]:
    """R7: transitive Hülle der Abhängigen -> STALE."""
    stale, frontier = [], [changed]
    while frontier:
        cur = frontier.pop()
        for q in qs.values():
            if cur in q.deps and q.status != "STALE":
                q.status, q.decision = "STALE", None
                stale.append(q.qid)
                frontier.append(q.qid)
    return sorted(stale)


@dataclass
class Ledger:
    """R8: append-only, hash-verkettet; Version = (MAJOR, MINOR, PATCH)."""
    events: list[dict] = field(default_factory=list)
    version: tuple[int, int, int] = (0, 1, 0)

    def append(self, kind: str, payload: dict, bump: str) -> str:
        prev = self.events[-1]["hash"] if self.events else "GENESIS"
        ma, mi, pa = self.version
        self.version = {"major": (ma + 1, 0, 0), "minor": (ma, mi + 1, 0),
                        "patch": (ma, mi, pa + 1)}[bump]
        body = {"kind": kind, "payload": payload, "prev": prev, "v": self.version}
        h = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        self.events.append({**body, "hash": h})
        return h

    def verify(self) -> bool:
        prev = "GENESIS"
        for e in self.events:
            body = {k: e[k] for k in ("kind", "payload", "prev", "v")}
            ok = e["prev"] == prev and e["hash"] == hashlib.sha256(
                json.dumps(body, sort_keys=True).encode()).hexdigest()
            if not ok:
                return False
            prev = e["hash"]
        return True
