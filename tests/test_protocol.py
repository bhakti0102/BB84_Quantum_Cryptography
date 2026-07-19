"""End-to-end protocol and security tests for the BB84 simulator.

These complement the unit tests in test_bb84.py. Where test_bb84.py checks the
individual helpers, this file runs the FULL protocol via run_bb84_protocol and
asserts the properties that make BB84 meaningful:

  * an honest, noiseless channel produces perfectly matching keys, and
  * an eavesdropper (Eve) is exposed by a jump in the error rate (QBER).

Run from the project root with:
    python -m unittest discover
"""
from __future__ import annotations

import unittest

from config import MAX_QUBIT_COUNT, QBER_THRESHOLD
from main import run_bb84_protocol
from qber import security_status
from utils import validate_probability, validate_qubit_count


class TestReproducibility(unittest.TestCase):
    def test_same_seed_gives_identical_run(self):
        # A fixed seed must make the whole simulation repeatable - this is what
        # lets you demo the same result twice in a viva.
        a = run_bb84_protocol(qubit_count=64, eve_enabled=False, seed=7)
        b = run_bb84_protocol(qubit_count=64, eve_enabled=False, seed=7)
        self.assertEqual(a.alice_bits, b.alice_bits)
        self.assertEqual(a.bob_bits, b.bob_bits)
        self.assertEqual(a.qber, b.qber)


class TestHonestChannelInvariant(unittest.TestCase):
    def test_no_eve_means_no_errors(self):
        # THE core BB84 invariant. With no eavesdropper and no channel noise,
        # every sifted bit must agree. Tested across many seeds so a single
        # lucky run can't hide a bug.
        for seed in range(25):
            result = run_bb84_protocol(qubit_count=64, eve_enabled=False, seed=seed)
            self.assertEqual(result.error_count, 0)
            self.assertEqual(result.qber, 0.0)
            self.assertEqual(result.alice_key, result.bob_key)

    def test_about_half_the_bits_survive_sifting(self):
        # Alice and Bob choose bases independently, so roughly half should match
        # and survive sifting. (Uses the maximum allowed qubit count.)
        result = run_bb84_protocol(qubit_count=MAX_QUBIT_COUNT, eve_enabled=False, seed=1)
        ratio = result.sifted_count / result.total_qubits
        self.assertTrue(0.43 < ratio < 0.57, f"Expected ~0.5, got {ratio:.3f}")


class TestEveSecurityProperty(unittest.TestCase):
    def test_full_intercept_raises_qber_to_about_25_percent(self):
        # Eve measuring every qubit in a random basis introduces ~25% error.
        # This statistical fingerprint is exactly what makes eavesdropping
        # detectable - the entire security argument of BB84 in one assertion.
        result = run_bb84_protocol(
            qubit_count=MAX_QUBIT_COUNT, eve_enabled=True, intercept_rate=1.0, seed=3
        )
        self.assertTrue(
            0.20 < result.qber < 0.30,
            f"Expected QBER near 0.25, got {result.qber:.3f}",
        )

    def test_eve_is_flagged_by_security_status(self):
        # A full-intercept attack must push QBER above the alarm threshold and
        # trigger the "High error rate" warning.
        result = run_bb84_protocol(
            qubit_count=MAX_QUBIT_COUNT, eve_enabled=True, intercept_rate=1.0, seed=5
        )
        self.assertGreater(result.qber, QBER_THRESHOLD)
        self.assertIn("High", security_status(result.qber))


class TestInputValidation(unittest.TestCase):
    def test_qubit_count_bounds(self):
        # 0 is too small, a bool is not a real count, and MAX+1 is over the ceiling.
        for bad in (0, True, MAX_QUBIT_COUNT + 1):
            with self.assertRaises(ValueError):
                validate_qubit_count(bad)

    def test_probability_bounds(self):
        for bad in (-0.1, 1.1, True):
            with self.assertRaises(ValueError):
                validate_probability(bad, "intercept rate")

    def test_security_status_messages(self):
        self.assertIn("No errors", security_status(0.0))
        self.assertIn("acceptable", security_status(QBER_THRESHOLD - 0.01))
        self.assertIn("High", security_status(QBER_THRESHOLD + 0.2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
