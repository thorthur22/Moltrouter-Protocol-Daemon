from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


VerificationLevel = Literal[
    "self_asserted",
    "registry_attested",
    "third_party_indexed",
    "third_party_audited",
]

RegistryEntryKind = Literal["provider", "indexed"]


class TrustInfo(BaseModel):
    score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    proofs: List[str] = Field(default_factory=list)
    level: Optional[VerificationLevel] = None


class RegistryEntry(BaseModel):
    id: str

    # Stable identity used to merge indexed/provider records.
    canonical_id: Optional[str] = None

    kind: Optional[RegistryEntryKind] = None

    name: str
    description: Optional[str] = None

    repo: Optional[str] = None

    # Required for kind=provider; optional for kind=indexed.
    manifest_url: Optional[str] = None

    capabilities: List[str] = Field(default_factory=list)
    policies: List[str] = Field(default_factory=list)
    proofs: List[str] = Field(default_factory=list)

    trust: Optional[TrustInfo] = None

    metadata: dict[str, Any] = Field(default_factory=dict)


class RegistryQueryResponse(BaseModel):
    mrp_version: str = "0.1"
    next_page: Optional[str] = None
    results: List[RegistryEntry] = Field(default_factory=list)
