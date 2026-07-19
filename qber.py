from __future__ import annotations

import logging

from config import QBER_THRESHOLD
from utils import validate_key_pair, validate_probability


logger = logging.getLogger(__name__)


def count_key_errors(alice_key: list[int], bob_key: list[int], allow_empty: bool = False) -> int:
    """Count mismatched bits between Alice's and Bob's sifted keys."""
    if not allow_empty:
        validate_key_pair(alice_key, bob_key)
    elif len(alice_key) != len(bob_key):
        raise ValueError("Alice and Bob sifted keys must have the same length.")
    return sum(1 for alice_bit, bob_bit in zip(alice_key, bob_key) if alice_bit != bob_bit)


def calculate_qber(alice_key: list[int], bob_key: list[int], allow_empty: bool = False) -> float:
    """Calculate the quantum bit error rate for two sifted keys."""
    if not alice_key:
        if not allow_empty:
            raise ValueError("Sifted keys are empty; QBER cannot be calculated.")
        logger.info("QBER calculation skipped because the sifted key is empty.")
        return 0.0
    errors = count_key_errors(alice_key, bob_key, allow_empty=allow_empty)
    qber = errors / len(alice_key)
    logger.info("QBER calculation found %s errors across %s sifted bits.", errors, len(alice_key))
    return qber


def security_status(qber: float, threshold: float = QBER_THRESHOLD) -> str:
    """Return a human-readable security decision for a QBER value."""
    validate_probability(qber, "QBER")
    validate_probability(threshold, "QBER threshold")
    if qber == 0:
        return "No errors detected in the sifted key."
    if qber <= threshold:
        return "Low error rate. The key looks acceptable for this simulation."
    return "High error rate. Eve or channel noise may be present."
