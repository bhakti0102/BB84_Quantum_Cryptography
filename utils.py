from __future__ import annotations

from dataclasses import dataclass
import logging
from random import Random

from config import MAX_QUBIT_COUNT, MIN_QUBIT_COUNT


logger = logging.getLogger(__name__)

RECTILINEAR = "Z"
DIAGONAL = "X"
BASES = (RECTILINEAR, DIAGONAL)
BASIS_LABELS = {
    RECTILINEAR: "Rectilinear (+)",
    DIAGONAL: "Diagonal (x)",
}


@dataclass
class EncodedQubit:
    bit: int
    basis: str


@dataclass
class EveObservation:
    intercepted: bool
    basis: str | None
    bit: int | None


@dataclass
class SimulationResult:
    alice_bits: list[int]
    alice_bases: list[str]
    bob_bases: list[str]
    bob_bits: list[int]
    sifted_positions: list[int]
    alice_key: list[int]
    bob_key: list[int]
    qber: float
    eve_enabled: bool
    eve_observations: list[EveObservation]
    intercept_rate: float

    @property
    def total_qubits(self) -> int:
        """Return the number of signals Alice sent."""
        return len(self.alice_bits)

    @property
    def sifted_count(self) -> int:
        """Return the number of bits kept after basis comparison."""
        return len(self.sifted_positions)

    @property
    def discarded_count(self) -> int:
        """Return the number of bits discarded after basis comparison."""
        return self.total_qubits - self.sifted_count

    @property
    def error_count(self) -> int:
        """Return the number of mismatched bits in the sifted keys."""
        return sum(1 for a_bit, b_bit in zip(self.alice_key, self.bob_key) if a_bit != b_bit)

    @property
    def qber_percent(self) -> float:
        """Return QBER as a percentage."""
        return self.qber * 100


def make_rng(seed: int | None = None) -> Random:
    """Create a random number generator, optionally with a repeatable seed."""
    return Random(seed)


def validate_qubit_count(count: int) -> None:
    """Validate the number of qubits requested for the simulation."""
    if isinstance(count, bool) or not isinstance(count, int):
        raise ValueError(f"Number of qubits must be an integer, got {count!r}.")
    if count < MIN_QUBIT_COUNT:
        raise ValueError(f"Number of qubits must be at least {MIN_QUBIT_COUNT}.")
    if count > MAX_QUBIT_COUNT:
        raise ValueError(f"Number of qubits must be at most {MAX_QUBIT_COUNT}.")


def validate_bit(bit: int) -> None:
    """Validate that a classical bit is either 0 or 1."""
    if bit not in (0, 1):
        raise ValueError(f"Bit must be 0 or 1, got {bit!r}.")


def validate_basis(basis: str) -> None:
    """Validate a BB84 basis value."""
    if basis not in BASES:
        raise ValueError(f"Basis must be one of {BASES}, got {basis!r}.")


def validate_probability(value: float, name: str) -> None:
    """Validate a probability-like value between 0 and 1 inclusive."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number between 0 and 1, got {value!r}.")
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value!r}.")


def validate_key_pair(alice_key: list[int], bob_key: list[int]) -> None:
    """Validate that two sifted keys can be compared."""
    if len(alice_key) != len(bob_key):
        raise ValueError("Alice and Bob sifted keys must have the same length.")
    if not alice_key:
        raise ValueError("Sifted keys are empty; QBER cannot be calculated.")
    for bit in alice_key + bob_key:
        validate_bit(bit)


def validate_signal(signal: EncodedQubit) -> None:
    """Validate an encoded qubit representation."""
    validate_bit(signal.bit)
    validate_basis(signal.basis)


def random_bits(count: int, rng: Random) -> list[int]:
    """Generate random classical bits for Alice."""
    validate_qubit_count(count)
    return [rng.randint(0, 1) for _ in range(count)]


def random_bases(count: int, rng: Random) -> list[str]:
    """Generate random BB84 bases."""
    validate_qubit_count(count)
    return [rng.choice(BASES) for _ in range(count)]


def measure_encoded_qubit(qubit: EncodedQubit, measurement_basis: str, rng: Random) -> int:
    """Measure an encoded qubit in a chosen basis."""
    validate_signal(qubit)
    validate_basis(measurement_basis)
    if measurement_basis == qubit.basis:
        return qubit.bit
    return rng.randint(0, 1)


def sift_keys(
    alice_bits: list[int],
    bob_bits: list[int],
    alice_bases: list[str],
    bob_bases: list[str],
) -> tuple[list[int], list[int], list[int]]:
    """Keep only positions where Alice and Bob used the same basis."""
    lengths = {len(alice_bits), len(bob_bits), len(alice_bases), len(bob_bases)}
    if len(lengths) != 1:
        raise ValueError("Alice and Bob data must all have the same length.")

    for bit in alice_bits + bob_bits:
        validate_bit(bit)
    for basis in alice_bases + bob_bases:
        validate_basis(basis)

    positions: list[int] = []
    alice_key: list[int] = []
    bob_key: list[int] = []

    for index, (alice_bit, bob_bit, alice_basis, bob_basis) in enumerate(
        zip(alice_bits, bob_bits, alice_bases, bob_bases)
    ):
        if alice_basis == bob_basis:
            positions.append(index)
            alice_key.append(alice_bit)
            bob_key.append(bob_bit)

    logger.info("Key sifting kept %s of %s transmitted bits.", len(positions), len(alice_bits))
    return positions, alice_key, bob_key


def bits_to_string(bits: list[int], empty_text: str = "(empty)") -> str:
    """Convert a list of bits into a compact string."""
    for bit in bits:
        validate_bit(bit)
    if not bits:
        return empty_text
    return "".join(str(bit) for bit in bits)
