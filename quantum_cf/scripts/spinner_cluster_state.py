#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
3-Lobe Spinner Cluster State Generator
Maps the coherent spinner onto a 3-lobe cluster state.

Cf = 1: Perfect coherence, all lobes entangled in a ring.
"""

from qiskit import QuantumCircuit

def create_3_lobe_spinner(entanglement_depth=3, add_phase=True):
    """
    Creates a 3-lobe cluster state representing a coherent spinner.
    
    Args:
        entanglement_depth (int): How many layers of entanglement (Cf increases with depth)
        add_phase (bool): Whether to add phase rotation (the "hum")
    
    Returns:
        QuantumCircuit: The spinner cluster state
    """
    n_qubits = 3  # 3 lobes
    circuit = QuantumCircuit(n_qubits, n_qubits)
    
    # Step 1: Create superposition (the lobes start spinning)
    for i in range(n_qubits):
        circuit.h(i)
    
    # Step 2: Entangle the lobes (the "clubbing")
    for depth in range(entanglement_depth):
        for i in range(n_qubits - 1):
            circuit.cz(i, i+1)
        # Ring: connect last to first
        circuit.cz(n_qubits-1, 0)
    
    # Step 3: Add phase alignment (the "hum" frequency)
    if add_phase:
        theta = entanglement_depth * np.pi / 3  # Frequency increases with depth
        for i in range(n_qubits):
            circuit.rz(theta, i)
    
    # Measure
    for i in range(n_qubits):
        circuit.measure(i, i)
    
    return circuit

def spinner_cf_estimate(entanglement_depth):
    """
    Estimates Cf from entanglement depth.
    Cf = 1 - exp(-entanglement_depth/3)
    """
    import numpy as np
    return 1 - np.exp(-entanglement_depth / 3)

if __name__ == "__main__":
    print("3-Lobe Spinner Cluster State Generator")
    print("Cf levels:")
    for depth in range(1, 6):
        cf = spinner_cf_estimate(depth)
        print(f"  Depth {depth}: Cf = {cf:.4f}")