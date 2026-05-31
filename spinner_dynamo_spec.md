
# Spinner Dynamo: A Reaction Wheel with Gravity-Gradient Energy Harvesting (μ-scale)

**Author:** The Bridge Architect, with Morpheus (HuAi)  
**License:** CC0 1.0  
**Date:** 2026-05-31  
**Version:** 2.0 (Physics-Corrected)

---

## Abstract

The spinner dynamo is a variable-inertia rotor that serves as a **reaction wheel** for spacecraft attitude control, with a secondary capability to harvest **micro-scale energy** from the gravity gradient. The available energy per orbit is on the order of **millijoules** — sufficient for sensor power, not for propulsion. This document presents the corrected physics, the analytic upper bound, and a revised simulation approach.

---

## 1. Corrected Physics

### 1.1 Gravity-Gradient Torque

For a spacecraft in a circular orbit, the gravity-gradient torque is:

```
τ_gg = (3μ / r³) * (I_z - I_y) * sin(2θ)
```

Where:

| Symbol | Meaning | Typical LEO value |
|--------|---------|-------------------|
| μ = GM | Earth's gravitational parameter | 3.986 × 10¹⁴ m³/s² |
| r | Orbital radius | 6.771 × 10⁶ m |
| r³ | | 3.104 × 10²⁰ m³ |
| 3μ/r³ | Gradient coefficient | ~3.85 × 10⁻⁶ s⁻² |
| I_z - I_y | Difference in principal moments | Variable (10–10,000 kg·m²) |

The torque is **conservative**:

```
∮ τ_gg dθ = 0
```

No net energy can be extracted from a passive rotor.

### 1.2 Energy Available (Upper Bound)

The maximum change in potential energy from one orientation to another is:

```
ΔU_max = (3μ / 2r³) * (ΔI_max - ΔI_min)
```

| ΔI (kg·m²) | ΔU_max (J) | Practical significance |
|------------|------------|------------------------|
| 10 | 1.93 × 10⁻⁴ | 190 μJ — negligible |
| 100 | 1.93 × 10⁻³ | 1.9 mJ — very small |
| 1,000 | 1.93 × 10⁻² | 19 mJ — small |
| 10,000 | 1.93 × 10⁻¹ | 0.19 J — still small |

The available energy per cycle is **millijoules**, not joules or kilojoules.

### 1.3 Actuator Energy Cost

To change ΔI (e.g., deploy wings, move masses), actuator work is required. Even with optimistic estimates:

| ΔI change | Mass moved | Distance | Actuator energy (min) | Available energy | Ratio |
|-----------|------------|----------|----------------------|------------------|-------|
| 400 kg·m² | 100 kg | 2 m | ~20 J | 0.002–0.02 J | 0.0001–0.001 |

Actuator costs exceed available energy by **3–4 orders of magnitude**. Net energy extraction is not feasible.

---

## 2. What the Spinner Actually Does

| Function | Feasibility | Energy scale |
|----------|-------------|--------------|
| **Reaction wheel (attitude control)** | ✅ Proven | N/A |
| **Gravity-gradient stabilization** | ✅ Proven | N/A |
| **Micro-energy harvesting for sensors** | 🟡 Possible | Nanowatts to microwatts |
| **Propulsion or primary power** | ❌ Not feasible | Millijoules vs. kilojoules needed |

The spinner is a **reaction wheel** — not a power plant.

---

## 3. Revised Simulation Approach

The simulation now models:

- Correct gravity-gradient torque: `τ_gg = k * ΔI * sin(2θ)`
- Orbital energy conservation: `dE_orbit/dt = -power_harvest`
- Active inertia modulation (for control, not net energy extraction)
- Gyroscopic stability metric: `S = L / τ_disturbance`

### 3.1 Key Equations

```python
# Gravity-gradient torque (corrected)
tau_gg = 3 * mu / r**3 * delta_I * np.sin(2 * phi)

# Rotor dynamics
I_rotor * d(omega)/dt = tau_control + tau_gen + tau_friction

# Craft dynamics (reaction wheel)
I_craft * d(omega_craft)/dt = -tau_control + tau_gg

# Orbital energy conservation
dE_orbit/dt = -power_harvest

# Available energy per cycle (upper bound)
delta_U_max = (3 * mu / (2 * r**3)) * (delta_I_max - delta_I_min)
```

### 3.2 Simulation Outputs

| Output | What it shows |
|--------|---------------|
| Rotor spin rate | Should remain near resonance if control is active |
| Craft orientation | Should track target with small error |
| Harvested energy | Increases over time (from orbital decay) |
| Altitude | Slowly decays (micro-scale) |
| Gyroscopic stability | High when rotor spins fast |

---

## 4. Experimental Testability

The most direct test is **not in orbit** — it is on a **lab bench** with a torsion balance.

| Experiment | Measured quantity | Expected result |
|------------|-------------------|-----------------|
| Rotating mass with variable inertia | Net torque over a cycle | Should integrate to zero for passive rotor |
| Active inertia modulation (actuated) | Net torque over a cycle | May be non-zero, but actuator energy must be accounted |

If the net work exceeds actuator energy, a discovery has been made. If not, the spinner remains a reaction wheel.

---

## 5. Conclusion

The spinner dynamo is a **reaction wheel** with a secondary, micro-scale energy harvesting capability. The gravity-gradient torque is conservative; net energy extraction requires active inertia modulation, but actuator costs exceed available energy by orders of magnitude. The device is useful for attitude control and stabilization, not for propulsion or primary power.

**The hum is real — but it is faint. You cannot power a spacecraft with a whisper. But you can use it to stay aligned.**

---

## 6. References

- Corrected gravity-gradient torque: `τ_gg = 3μ/r³ * ΔI * sin(2θ)`
- Analytic upper bound: `ΔU_max = (3μ/2r³) * ΔI_max`
- Reaction wheel theory: standard spacecraft dynamics
- Coherence transport roadmap: `coherence_transport_roadmap.md`

— The Bridge Architect, for HuAi
```

---
