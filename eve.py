from __future__ import annotations

import logging
from random import Random

from utils import BASES, EncodedQubit, EveObservation, measure_encoded_qubit
from utils import validate_probability, validate_qubit_count


logger = logging.getLogger(__name__)


def intercept_signals(
    signals: list[EncodedQubit],
    rng: Random,
    intercept_rate: float = 1.0,
) -> tuple[list[EncodedQubit], list[EveObservation]]:
    """Intercept, measure, and resend signals using Eve's random bases."""
    validate_probability(intercept_rate, "Intercept rate")

    resent_signals: list[EncodedQubit] = []
    observations: list[EveObservation] = []

    for signal in signals:
        if rng.random() < intercept_rate:
            eve_basis = rng.choice(BASES)
            eve_bit = measure_encoded_qubit(signal, eve_basis, rng)
            resent_signals.append(EncodedQubit(bit=eve_bit, basis=eve_basis))
            observations.append(EveObservation(intercepted=True, basis=eve_basis, bit=eve_bit))
        else:
            resent_signals.append(signal)
            observations.append(EveObservation(intercepted=False, basis=None, bit=None))

    intercepted_count = sum(observation.intercepted for observation in observations)
    logger.info(
        "Eve intercepted %s of %s signals at %.0f%% intercept rate.",
        intercepted_count,
        len(signals),
        intercept_rate * 100,
    )
    return resent_signals, observations


def empty_observations(count: int) -> list[EveObservation]:
    """Create empty Eve observations when Eve is disabled."""
    validate_qubit_count(count)
    return [EveObservation(intercepted=False, basis=None, bit=None) for _ in range(count)]
