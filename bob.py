from __future__ import annotations

import logging
from random import Random

from utils import EncodedQubit, measure_encoded_qubit, random_bases


logger = logging.getLogger(__name__)


def choose_bases(count: int, rng: Random) -> list[str]:
    """Choose Bob's random measurement bases."""
    bases = random_bases(count, rng)
    logger.info("Bob selected %s measurement bases.", len(bases))
    return bases


def measure_signal(signal: EncodedQubit, basis: str, rng: Random) -> int:
    """Measure one encoded signal using Bob's chosen basis."""
    return measure_encoded_qubit(signal, basis, rng)


def measure_signals(signals: list[EncodedQubit], bases: list[str], rng: Random) -> list[int]:
    """Measure all signals received by Bob."""
    if len(signals) != len(bases):
        raise ValueError("Bob must have one measurement basis for every signal.")
    measurements = [measure_signal(signal, basis, rng) for signal, basis in zip(signals, bases)]
    logger.info("Bob measured %s received signals.", len(measurements))
    return measurements
