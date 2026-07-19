from __future__ import annotations

import logging
from random import Random
from typing import TYPE_CHECKING

from utils import DIAGONAL, EncodedQubit, random_bases, random_bits, validate_basis, validate_bit


if TYPE_CHECKING:
    from qiskit import QuantumCircuit


logger = logging.getLogger(__name__)


def generate_bits(count: int, rng: Random) -> list[int]:
    """Generate Alice's random classical bit sequence."""
    bits = random_bits(count, rng)
    logger.info("Alice generated %s random bits.", len(bits))
    return bits


def choose_bases(count: int, rng: Random) -> list[str]:
    """Choose Alice's random preparation bases."""
    bases = random_bases(count, rng)
    logger.info("Alice selected %s preparation bases.", len(bases))
    return bases


def prepare_signal(bit: int, basis: str) -> EncodedQubit:
    """Prepare one encoded BB84 signal from a bit and basis."""
    validate_bit(bit)
    validate_basis(basis)
    return EncodedQubit(bit=bit, basis=basis)


def prepare_signals(bits: list[int], bases: list[str]) -> list[EncodedQubit]:
    """Prepare all of Alice's encoded BB84 signals."""
    if len(bits) != len(bases):
        raise ValueError("Alice must have one basis for every bit.")
    return [prepare_signal(bit, basis) for bit, basis in zip(bits, bases)]


def build_preparation_circuit(bit: int, basis: str) -> "QuantumCircuit":
    """Build a one-qubit Qiskit circuit showing Alice's preparation step."""
    validate_bit(bit)
    validate_basis(basis)

    try:
        from qiskit import QuantumCircuit
    except Exception as exc:
        raise RuntimeError("Qiskit is required for circuit visualization.") from exc

    circuit = QuantumCircuit(1, 1)
    if bit == 1:
        circuit.x(0)
    if basis == DIAGONAL:
        circuit.h(0)
    circuit.measure(0, 0)
    return circuit
