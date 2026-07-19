"""Core BB84 protocol engine.

This module holds the simulation logic itself, independent of any interface.
Both the command-line tool (main.py) and the Streamlit app (app.py) import
run_bb84_protocol from here, so the protocol has exactly one home.
"""
from __future__ import annotations

import logging

import alice
import bob
import eve
from config import DEFAULT_EVE_ENABLED, DEFAULT_INTERCEPT_RATE, DEFAULT_QUBIT_COUNT
from qber import calculate_qber
from utils import SimulationResult, make_rng, sift_keys
from utils import validate_probability, validate_qubit_count


logger = logging.getLogger(__name__)


def run_bb84_protocol(
    qubit_count: int = DEFAULT_QUBIT_COUNT,
    eve_enabled: bool = DEFAULT_EVE_ENABLED,
    intercept_rate: float = DEFAULT_INTERCEPT_RATE,
    seed: int | None = None,
) -> SimulationResult:
    """Run the BB84 protocol and return all simulation data."""
    validate_qubit_count(qubit_count)
    validate_probability(intercept_rate, "Intercept rate")

    rng = make_rng(seed)

    alice_bits = alice.generate_bits(qubit_count, rng)
    alice_bases = alice.choose_bases(qubit_count, rng)
    signals = alice.prepare_signals(alice_bits, alice_bases)

    if eve_enabled:
        transmitted_signals, eve_observations = eve.intercept_signals(
            signals,
            rng,
            intercept_rate=intercept_rate,
        )
    else:
        transmitted_signals = signals
        eve_observations = eve.empty_observations(qubit_count)

    bob_bases = bob.choose_bases(qubit_count, rng)
    bob_bits = bob.measure_signals(transmitted_signals, bob_bases, rng)

    sifted_positions, alice_key, bob_key = sift_keys(
        alice_bits,
        bob_bits,
        alice_bases,
        bob_bases,
    )
    qber = calculate_qber(alice_key, bob_key, allow_empty=True)
    logger.info("BB84 run completed with %.2f%% QBER.", qber * 100)

    return SimulationResult(
        alice_bits=alice_bits,
        alice_bases=alice_bases,
        bob_bases=bob_bases,
        bob_bits=bob_bits,
        sifted_positions=sifted_positions,
        alice_key=alice_key,
        bob_key=bob_key,
        qber=qber,
        eve_enabled=eve_enabled,
        eve_observations=eve_observations,
        intercept_rate=intercept_rate,
    )
