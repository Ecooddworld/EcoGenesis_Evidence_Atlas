from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import hashlib
import os
from typing import Any, Iterator

from app.barcode.schemas import SequenceRecord
from app.barcode.scientific_gates import (
    ATTESTATION_KEY_ID_ENV,
    ATTESTATION_SECRET_ENV,
    attest_reference_completeness,
)


# Public by design: this key can authenticate only explicitly labelled synthetic
# regression output generated inside this process. It is not a production trust
# secret and must never be configured on a deployed API.
SYNTHETIC_FIXTURE_SECRET = "PUBLIC-NONTRUST-SYNTHETIC-REGRESSION-KEY-ONLY"
SYNTHETIC_FIXTURE_KEY_ID = "synthetic-regression-fixture-not-external-trust"
SYNTHETIC_AUDIT_SHA256 = hashlib.sha256(
    b"EcoGenesis synthetic regression evidence bundle; no external reference audit"
).hexdigest()


@contextmanager
def synthetic_fixture_attestation_environment() -> Iterator[None]:
    previous_secret = os.environ.get(ATTESTATION_SECRET_ENV)
    previous_key_id = os.environ.get(ATTESTATION_KEY_ID_ENV)
    os.environ[ATTESTATION_SECRET_ENV] = SYNTHETIC_FIXTURE_SECRET
    os.environ[ATTESTATION_KEY_ID_ENV] = SYNTHETIC_FIXTURE_KEY_ID
    try:
        yield
    finally:
        _restore_environment(ATTESTATION_SECRET_ENV, previous_secret)
        _restore_environment(ATTESTATION_KEY_ID_ENV, previous_key_id)


def attest_synthetic_regression_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sign synthetic evidence only so offline regression can exercise pass paths.

    Callers must keep :func:`synthetic_fixture_attestation_environment` active
    while compiling so verification uses the same explicitly non-production key.
    """

    signed = []
    for source in records:
        payload = deepcopy(source)
        evidence = payload.get("reference_completeness")
        if evidence is None:
            signed.append(payload)
            continue
        evidence.update(
            {
                "status": "audited_sufficient",
                "audit_source": (
                    "synthetic repeated-fixture regression only; public test key; "
                    "not independent reference validation"
                ),
                "audit_sha256": SYNTHETIC_AUDIT_SHA256,
                "notes": (
                    "This public-key fixture attestation exercises deterministic code paths only and "
                    "cannot support scientific release."
                ),
            }
        )
        model = SequenceRecord(**payload)
        candidate_species = len(
            {hit.taxon for hit in model.hits if str(hit.rank).strip().lower() == "species"}
        )
        evidence["attestation"] = attest_reference_completeness(
            model,
            candidate_species_in_hits=candidate_species,
        )
        signed.append(payload)
    return signed


def _restore_environment(name: str, previous: str | None) -> None:
    if previous is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = previous
