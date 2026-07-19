"""Unit tests for the BB84 simulator."""

from __future__ import annotations

import unittest

import alice
import bob
from qber import calculate_qber, count_key_errors
from utils import EncodedQubit, make_rng, random_bases, random_bits, sift_keys


class TestBB84Core(unittest.TestCase):
    """Test the core BB84 protocol helpers."""

    def test_bit_generation(self) -> None:
        """Alice bit generation should return only binary values."""
        bits = random_bits(16, make_rng(1))

        self.assertEqual(len(bits), 16)
        self.assertTrue(all(bit in (0, 1) for bit in bits))

    def test_basis_generation(self) -> None:
        """Basis generation should return only BB84 bases."""
        bases = random_bases(16, make_rng(2))

        self.assertEqual(len(bases), 16)
        self.assertTrue(all(basis in ("Z", "X") for basis in bases))

    def test_encoding(self) -> None:
        """Alice should encode a bit and basis into an encoded qubit."""
        signal = alice.prepare_signal(1, "X")

        self.assertEqual(signal.bit, 1)
        self.assertEqual(signal.basis, "X")

    def test_invalid_encoding_rejected(self) -> None:
        """Alice should reject invalid bits or bases."""
        with self.assertRaises(ValueError):
            alice.prepare_signal(2, "Z")
        with self.assertRaises(ValueError):
            alice.prepare_signal(1, "Y")

    def test_measurement_same_basis(self) -> None:
        """Bob should recover the original bit when bases match."""
        signal = EncodedQubit(bit=1, basis="Z")
        measured_bit = bob.measure_signal(signal, "Z", make_rng(3))

        self.assertEqual(measured_bit, 1)

    def test_invalid_measurement_rejected(self) -> None:
        """Bob should reject invalid measurement bases."""
        signal = EncodedQubit(bit=1, basis="Z")

        with self.assertRaises(ValueError):
            bob.measure_signal(signal, "Y", make_rng(4))

    def test_key_sifting(self) -> None:
        """Only matching bases should survive key sifting."""
        positions, alice_key, bob_key = sift_keys(
            alice_bits=[1, 0, 1, 1],
            bob_bits=[1, 1, 1, 0],
            alice_bases=["Z", "X", "Z", "X"],
            bob_bases=["Z", "Z", "Z", "X"],
        )

        self.assertEqual(positions, [0, 2, 3])
        self.assertEqual(alice_key, [1, 1, 1])
        self.assertEqual(bob_key, [1, 1, 0])

    def test_qber_calculation(self) -> None:
        """QBER should equal errors divided by sifted key length."""
        alice_key = [1, 1, 0, 0]
        bob_key = [1, 0, 0, 1]

        self.assertEqual(count_key_errors(alice_key, bob_key), 2)
        self.assertEqual(calculate_qber(alice_key, bob_key), 0.5)

    def test_empty_qber_rejected(self) -> None:
        """QBER calculation should reject empty sifted keys by default."""
        with self.assertRaises(ValueError):
            calculate_qber([], [])


if __name__ == "__main__":
    unittest.main()

