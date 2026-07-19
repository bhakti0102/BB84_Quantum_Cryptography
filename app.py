from __future__ import annotations

import streamlit as st

import alice
from config import DEFAULT_EVE_ENABLED, DEFAULT_INTERCEPT_RATE, DEFAULT_QUBIT_COUNT
from config import DEFAULT_RANDOM_SEED, MAX_QUBIT_COUNT, MIN_QUBIT_COUNT
from config import USE_DEFAULT_SEED
from protocol import run_bb84_protocol
from qber import security_status
from utils import bits_to_string
from visualization import plot_basis_comparison, plot_error_distribution, plot_key_length
from visualization import plot_qber_comparison, result_to_dataframe


st.set_page_config(page_title="BB84 QKD Simulator", layout="wide")

st.title("BB84 Quantum Key Distribution Simulator")


def run_and_store_simulation() -> None:
    """Run the simulator from sidebar inputs and store results in session state."""
    try:
        seed_value = int(seed) if use_seed else None
        result = run_bb84_protocol(
            qubit_count=qubit_count,
            eve_enabled=eve_enabled,
            intercept_rate=intercept_rate if eve_enabled else 0.0,
            seed=seed_value,
        )
        no_eve_result = run_bb84_protocol(
            qubit_count=qubit_count,
            eve_enabled=False,
            intercept_rate=0.0,
            seed=seed_value,
        )
        eve_result = run_bb84_protocol(
            qubit_count=qubit_count,
            eve_enabled=True,
            intercept_rate=intercept_rate,
            seed=seed_value,
        )
    except ValueError as error:
        st.session_state["simulation_error"] = str(error)
        return

    st.session_state["simulation_result"] = result
    st.session_state["no_eve_result"] = no_eve_result
    st.session_state["eve_result"] = eve_result
    st.session_state["simulation_error"] = None


with st.sidebar:
    qubit_count = st.slider(
        "Number of bits",
        min_value=MIN_QUBIT_COUNT,
        max_value=MAX_QUBIT_COUNT,
        value=DEFAULT_QUBIT_COUNT,
        step=1,
    )
    eve_enabled = st.checkbox("Enable Eve", value=DEFAULT_EVE_ENABLED)
    intercept_rate = st.slider(
        "Eve intercept rate",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULT_INTERCEPT_RATE,
        step=0.05,
        disabled=not eve_enabled,
    )
    use_seed = st.checkbox("Use repeatable seed", value=USE_DEFAULT_SEED)
    seed = st.number_input(
        "Random seed",
        min_value=0,
        value=DEFAULT_RANDOM_SEED,
        step=1,
        disabled=not use_seed,
    )
    run_clicked = st.button("Run Simulation", type="primary")

if run_clicked or "simulation_result" not in st.session_state:
    run_and_store_simulation()

if st.session_state.get("simulation_error"):
    st.error(st.session_state["simulation_error"])
    st.stop()

result = st.session_state["simulation_result"]
no_eve_result = st.session_state["no_eve_result"]
eve_result = st.session_state["eve_result"]

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Qubits Sent", result.total_qubits)
metric_2.metric("Sifted Key Length", result.sifted_count)
metric_3.metric("Errors", result.error_count)
metric_4.metric("QBER", f"{result.qber_percent:.2f}%")

st.info(security_status(result.qber))

overview_tab, data_tab, graph_tab, circuit_tab = st.tabs(
    ["Overview", "Protocol Data", "Graphs", "Circuit"]
)

with overview_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("Sifted Key")
        st.code(bits_to_string(result.alice_key), language="text")
    with right:
        st.subheader("Final Shared Key")
        shared_key = result.alice_key if result.alice_key == result.bob_key else []
        st.code(bits_to_string(shared_key, empty_text="Keys do not match"), language="text")

    st.subheader("Simulation Summary")
    st.write(
        {
            "Eve enabled": result.eve_enabled,
            "Intercept rate": result.intercept_rate if result.eve_enabled else 0.0,
            "Kept bits": result.sifted_count,
            "Discarded bits": result.discarded_count,
            "QBER": f"{result.qber_percent:.2f}%",
            "Eve detection status": security_status(result.qber),
        }
    )

with data_tab:
    data_left, data_right = st.columns(2)
    data_left.subheader("Alice Bits")
    data_left.code(bits_to_string(result.alice_bits), language="text")
    data_right.subheader("Alice Bases")
    data_right.code(" ".join(result.alice_bases), language="text")

    bob_left, bob_right = st.columns(2)
    bob_left.subheader("Bob Bases")
    bob_left.code(" ".join(result.bob_bases), language="text")
    bob_right.subheader("Bob Measurements")
    bob_right.code(bits_to_string(result.bob_bits), language="text")

    st.subheader("Transmission Log")
    st.dataframe(result_to_dataframe(result), use_container_width=True, hide_index=True)

with graph_tab:
    graph_left, graph_right = st.columns(2)
    with graph_left:
        st.pyplot(plot_basis_comparison(result), clear_figure=True)
        st.pyplot(plot_key_length(result), clear_figure=True)
    with graph_right:
        st.pyplot(plot_qber_comparison(no_eve_result, eve_result), clear_figure=True)
        st.pyplot(plot_error_distribution(result), clear_figure=True)

with circuit_tab:
    st.subheader("Circuit Visualization")
    try:
        first_circuit = alice.build_preparation_circuit(result.alice_bits[0], result.alice_bases[0])
    except RuntimeError as error:
        st.warning(str(error))
    else:
        st.code(str(first_circuit), language="text")
