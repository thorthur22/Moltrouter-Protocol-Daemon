from __future__ import annotations

from mrpd.core.models import RegistryEntry


def score_entry(entry: RegistryEntry, *, capability: str | None, policy: str | None) -> float:
    """Very simple scoring for now.

    Later: incorporate trust, cost, latency, token estimates, etc.
    """

    score = 0.0
    if capability and capability in entry.capabilities:
        score += 5.0
    if policy and policy in entry.policies:
        score += 2.0

    if entry.trust and entry.trust.score is not None:
        score += float(entry.trust.score)

    # small boost if both are present
    if capability and policy and (capability in entry.capabilities) and (policy in entry.policies):
        score += 1.0

    return score
