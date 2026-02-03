from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from mrpd.core.models import RegistryEntry


@dataclass(frozen=True)
class ScoreResult:
    entry: RegistryEntry
    score: float
    required_matches: int
    trust_score: float
    proofs_count: int
    reasons: tuple[str, ...]
    missing: tuple[str, ...]

    @property
    def satisfied(self) -> bool:
        return len(self.missing) == 0

    def rank_key(self) -> tuple:
        # Deterministic ordering: score, required matches, trust, proofs, name, id.
        return (
            -self.score,
            -self.required_matches,
            -self.trust_score,
            -self.proofs_count,
            (self.entry.name or "").lower(),
            self.entry.id,
        )


def score_entry(entry: RegistryEntry, *, capability: str | None, policy: str | None) -> ScoreResult:
    """Deterministic scoring with explicit tie-breakers.

    Score weights are simple and predictable; ties break by required matches,
    trust score, proof count, then stable name/id ordering.
    """

    score = 0.0
    reasons: list[str] = []
    missing: list[str] = []
    required_matches = 0

    if capability:
        if capability in entry.capabilities:
            score += 50.0
            required_matches += 1
            reasons.append(f"capability match: {capability}")
        else:
            missing.append(f"capability:{capability}")

    if policy:
        if policy in entry.policies:
            score += 20.0
            required_matches += 1
            reasons.append(f"policy match: {policy}")
        else:
            missing.append(f"policy:{policy}")

    trust_score = 0.0
    if entry.trust and entry.trust.score is not None:
        trust_score = float(entry.trust.score)
        score += 10.0 * trust_score
        reasons.append(f"trust score: {trust_score:.2f}")

    proofs_count = len(entry.proofs)
    if proofs_count:
        reasons.append(f"proofs: {proofs_count}")

    if capability and policy and (capability in entry.capabilities) and (policy in entry.policies):
        score += 5.0
        reasons.append("capability+policy bonus")

    return ScoreResult(
        entry=entry,
        score=score,
        required_matches=required_matches,
        trust_score=trust_score,
        proofs_count=proofs_count,
        reasons=tuple(reasons),
        missing=tuple(missing),
    )


def rank_entries(
    entries: Iterable[RegistryEntry], *, capability: str | None, policy: str | None
) -> list[ScoreResult]:
    scored = [score_entry(e, capability=capability, policy=policy) for e in entries]
    return sorted(scored, key=lambda r: r.rank_key())
