from __future__ import annotations

import argparse
import logging

from config import DEFAULT_INTERCEPT_RATE, DEFAULT_PREVIEW_ROWS
from config import DEFAULT_QUBIT_COUNT, DEFAULT_RANDOM_SEED, QBER_THRESHOLD
from protocol import run_bb84_protocol
from qber import security_status
from utils import SimulationResult, bits_to_string
from utils import validate_probability, validate_qubit_count


logger = logging.getLogger(__name__)


def print_report(result: SimulationResult, rows: int = DEFAULT_PREVIEW_ROWS) -> None:
    """Print a readable command-line report for a simulation result."""
    print("BB84 Quantum Key Distribution Simulation")
    print("=" * 42)
    print(f"Qubits sent:       {result.total_qubits}")
    print(f"Eve enabled:       {'yes' if result.eve_enabled else 'no'}")
    if result.eve_enabled:
        print(f"Intercept rate:    {result.intercept_rate:.0%}")
    print(f"Sifted key length: {result.sifted_count}")
    print(f"Errors in key:     {result.error_count}")
    print(f"QBER:              {result.qber_percent:.2f}%")
    print(f"Threshold:         {QBER_THRESHOLD:.0%}")
    print(f"Status:            {security_status(result.qber)}")
    print()
    print(f"Alice key: {bits_to_string(result.alice_key)}")
    print(f"Bob key:   {bits_to_string(result.bob_key)}")
    print()

    preview_count = min(rows, result.total_qubits)
    print(f"First {preview_count} transmitted qubits")
    print("Idx  A_bit  A_basis  Eve  B_basis  B_bit  Kept")
    print("-" * 49)
    sifted = set(result.sifted_positions)
    for index in range(preview_count):
        eve_mark = "Y" if result.eve_observations[index].intercepted else "N"
        kept = "Y" if index in sifted else "N"
        print(
            f"{index + 1:>3}  "
            f"{result.alice_bits[index]:>5}  "
            f"{result.alice_bases[index]:>7}  "
            f"{eve_mark:>3}  "
            f"{result.bob_bases[index]:>7}  "
            f"{result.bob_bits[index]:>5}  "
            f"{kept:>4}"
        )


def qubit_count_arg(value: str) -> int:
    """Parse and validate a qubit count for command-line arguments."""
    try:
        parsed_value = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a valid integer.") from exc
    try:
        validate_qubit_count(parsed_value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return parsed_value


def positive_int(value: str) -> int:
    """Parse a positive integer for command-line arguments."""
    try:
        parsed_value = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a valid integer.") from exc
    if parsed_value < 1:
        raise argparse.ArgumentTypeError("Value must be at least 1.")
    return parsed_value


def probability(value: str) -> float:
    """Parse a probability value for command-line arguments."""
    try:
        parsed_value = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a valid number.") from exc
    try:
        validate_probability(parsed_value, "Value")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return parsed_value


def configure_logging() -> None:
    """Configure simple structured logging for command-line runs."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")


def parse_args() -> argparse.Namespace:
    """Parse command-line inputs for the simulator."""
    parser = argparse.ArgumentParser(description="Run a BB84 quantum key distribution simulation.")
    parser.add_argument("--qubits", type=qubit_count_arg, default=DEFAULT_QUBIT_COUNT, help="Number of qubits Alice sends.")
    parser.add_argument("--eve", action="store_true", help="Enable Eve intercept-resend attack.")
    parser.add_argument(
        "--intercept-rate",
        type=probability,
        default=DEFAULT_INTERCEPT_RATE,
        help="Fraction of signals Eve intercepts when Eve is enabled.",
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_RANDOM_SEED, help="Optional seed for repeatable output.")
    parser.add_argument("--rows", type=positive_int, default=DEFAULT_PREVIEW_ROWS, help="Number of transmission rows to print.")
    return parser.parse_args()


def main() -> None:
    """Run the simulator from the command line."""
    configure_logging()
    args = parse_args()
    result = run_bb84_protocol(
        qubit_count=args.qubits,
        eve_enabled=args.eve,
        intercept_rate=args.intercept_rate,
        seed=args.seed,
    )
    print_report(result, rows=args.rows)


if __name__ == "__main__":
    main()
