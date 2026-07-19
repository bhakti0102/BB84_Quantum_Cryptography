from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from config import PLOT_COLORS, PLOT_FIGSIZE, PLOT_STYLE, QBER_THRESHOLD
from utils import BASIS_LABELS, SimulationResult


def result_to_dataframe(result: SimulationResult) -> pd.DataFrame:
    """Convert a simulation result into a row-by-row transmission table."""
    rows = []
    sifted = set(result.sifted_positions)

    for index in range(result.total_qubits):
        eve_observation = result.eve_observations[index]
        kept = index in sifted
        alice_bit = result.alice_bits[index]
        bob_bit = result.bob_bits[index]

        rows.append(
            {
                "Qubit": index + 1,
                "Alice bit": alice_bit,
                "Alice basis": result.alice_bases[index],
                "Eve basis": eve_observation.basis if eve_observation.intercepted else "-",
                "Eve bit": eve_observation.bit if eve_observation.intercepted else "-",
                "Bob basis": result.bob_bases[index],
                "Bob bit": bob_bit,
                "Kept": "Yes" if kept else "No",
                "Error": "Yes" if kept and alice_bit != bob_bit else "No",
            }
        )

    return pd.DataFrame(rows)


def _prepare_axis(title: str, ylabel: str):
    """Create a consistently styled Matplotlib figure and axis."""
    plt.style.use(PLOT_STYLE)
    fig, ax = plt.subplots(figsize=PLOT_FIGSIZE)
    ax.set_title(title, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    return fig, ax


def _add_bar_labels(ax) -> None:
    """Add value labels above each bar in a bar chart."""
    for container in ax.containers:
        ax.bar_label(container, padding=3, fontsize=9)


def plot_basis_summary(result: SimulationResult):
    """Plot how many transmitted bits were kept or discarded."""
    labels = ["Kept", "Discarded"]
    values = [result.sifted_count, result.discarded_count]

    fig, ax = _prepare_axis("Basis Matching", "Qubits")
    ax.bar(labels, values, color=[PLOT_COLORS["kept"], PLOT_COLORS["discarded"]])
    ax.set_ylim(0, max(values) + 2 if values else 1)
    _add_bar_labels(ax)
    fig.tight_layout()
    return fig


def plot_qber(result: SimulationResult):
    """Plot QBER for the current simulation against the configured threshold."""
    fig, ax = _prepare_axis("Quantum Bit Error Rate", "Percent")
    ax.bar(["QBER"], [result.qber_percent], color=PLOT_COLORS["error"], label="Current QBER")
    threshold_percent = QBER_THRESHOLD * 100
    ax.axhline(
        threshold_percent,
        color=PLOT_COLORS["threshold"],
        linestyle="--",
        linewidth=1.2,
        label=f"{threshold_percent:.0f}% threshold",
    )
    ax.set_ylim(0, max(30, result.qber_percent + 5))
    ax.legend()
    _add_bar_labels(ax)
    fig.tight_layout()
    return fig


def plot_basis_comparison(result: SimulationResult):
    """Plot Alice's preparation bases beside Bob's measurement bases."""
    alice_counts = pd.Series(result.alice_bases).value_counts().reindex(["Z", "X"], fill_value=0)
    bob_counts = pd.Series(result.bob_bases).value_counts().reindex(["Z", "X"], fill_value=0)
    basis_labels = [basis_name("Z"), basis_name("X")]

    fig, ax = _prepare_axis("Alice vs Bob Basis Comparison", "Count")
    x_positions = range(len(basis_labels))
    bar_width = 0.36
    alice_x = [position - bar_width / 2 for position in x_positions]
    bob_x = [position + bar_width / 2 for position in x_positions]

    ax.bar(alice_x, alice_counts, width=bar_width, label="Alice", color=PLOT_COLORS["alice"])
    ax.bar(bob_x, bob_counts, width=bar_width, label="Bob", color=PLOT_COLORS["bob"])
    ax.set_xticks(list(x_positions), basis_labels)
    ax.legend()
    ax.set_ylim(0, max(alice_counts.max(), bob_counts.max()) + 2)
    _add_bar_labels(ax)
    fig.tight_layout()
    return fig


def plot_key_length(result: SimulationResult):
    """Plot key length before and after basis sifting."""
    labels = ["Before sifting", "After sifting"]
    values = [result.total_qubits, result.sifted_count]

    fig, ax = _prepare_axis("Key Length Before and After Sifting", "Bits")
    ax.bar(labels, values, color=[PLOT_COLORS["alice"], PLOT_COLORS["kept"]])
    ax.set_ylim(0, max(values) + 2)
    _add_bar_labels(ax)
    fig.tight_layout()
    return fig


def plot_qber_comparison(no_eve_result: SimulationResult, eve_result: SimulationResult):
    """Compare QBER for simulations with and without Eve."""
    labels = ["No Eve", "With Eve"]
    values = [no_eve_result.qber_percent, eve_result.qber_percent]

    fig, ax = _prepare_axis("QBER Comparison: Eve vs No Eve", "Percent")
    ax.bar(labels, values, color=[PLOT_COLORS["bob"], PLOT_COLORS["eve"]])
    threshold_percent = QBER_THRESHOLD * 100
    ax.axhline(
        threshold_percent,
        color=PLOT_COLORS["threshold"],
        linestyle="--",
        linewidth=1.2,
        label=f"{threshold_percent:.0f}% threshold",
    )
    ax.set_ylim(0, max(30, max(values) + 5))
    ax.legend()
    _add_bar_labels(ax)
    fig.tight_layout()
    return fig


def plot_error_distribution(result: SimulationResult):
    """Plot where errors occurred within the sifted key."""
    fig, ax = _prepare_axis("Error Distribution in Sifted Key", "Error")

    if not result.sifted_positions:
        ax.text(0.5, 0.5, "No sifted key bits", ha="center", va="center", transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        fig.tight_layout()
        return fig

    positions = [position + 1 for position in result.sifted_positions]
    errors = [
        1 if alice_bit != bob_bit else 0
        for alice_bit, bob_bit in zip(result.alice_key, result.bob_key)
    ]

    ax.bar(positions, errors, color=PLOT_COLORS["error"])
    ax.set_xlabel("Original qubit position")
    ax.set_yticks([0, 1], ["Match", "Error"])
    ax.set_ylim(0, 1.2)
    fig.tight_layout()
    return fig


def basis_name(basis: str) -> str:
    """Return a readable name for a BB84 basis."""
    return BASIS_LABELS.get(basis, basis)
