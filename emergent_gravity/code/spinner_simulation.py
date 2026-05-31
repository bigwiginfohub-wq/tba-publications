"""
Spinner Dynamo Simulation
Models a three-lobe rotor harvesting energy from a gravity gradient.
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# Parameters
I = 0.1  # Moment of inertia (kg·m^2)
initial_spin_rate = 10.0  # rad/s
gradient_strength = 1e-6  # N/m per kg (simulated)
harvesting_efficiency = 0.5  # 0–1
k_harvest = 0.01  # Harvesting coefficient
k_loss = 0.001  # Friction/drag coefficient
k_mag = 0.01  # Magnetic field coupling (induced)
B_target = 1e-5  # Target magnetic field strength (Tesla) for Cf = 1

def spinner_dynamics(t, y):
    """
    y[0] = spin_rate (rad/s)
    y[1] = harvested_energy (J)
    """
    spin_rate = y[0]
    
    # Torque from gravity gradient harvesting
    torque_harvest = k_harvest * harvesting_efficiency * gradient_strength
    
    # Torque loss (friction, drag)
    torque_loss = k_loss * spin_rate
    
    # Net torque
    net_torque = torque_harvest - torque_loss
    
    # Angular acceleration
    alpha = net_torque / I
    
    # Power harvested
    power_harvest = torque_harvest * spin_rate
    
    # Harvested energy accumulation
    dE_dt = power_harvest
    
    # Magnetic field (induced)
    B = k_mag * spin_rate
    
    # Coherence (Cf)
    Cf = min(B / B_target, 1.0)
    
    return [alpha, dE_dt, B, Cf]

def simulate(duration=100, dt=0.01):
    t_span = (0, duration)
    t_eval = np.arange(0, duration, dt)
    y0 = [initial_spin_rate, 0.0]
    
    # Wrap dynamics to include B and Cf in output
    def full_dynamics(t, y):
        alpha, dE_dt, B, Cf = spinner_dynamics(t, y)
        return [alpha, dE_dt]
    
    sol = solve_ivp(full_dynamics, t_span, y0, t_eval=t_eval, method='RK45')
    
    # Compute B and Cf from spin_rate
    spin_rate = sol.y[0]
    B = k_mag * spin_rate
    Cf = np.minimum(B / B_target, 1.0)
    
    return sol.t, spin_rate, sol.y[1], B, Cf

# Run simulation
t, spin_rate, energy, B, Cf = simulate(duration=200)

# Plotting
fig, axes = plt.subplots(4, 1, figsize=(10, 12))

axes[0].plot(t, spin_rate)
axes[0].set_ylabel('Spin Rate (rad/s)')
axes[0].set_title('Spinner Dynamo Simulation')
axes[0].grid(True)

axes[1].plot(t, energy)
axes[1].set_ylabel('Harvested Energy (J)')
axes[1].grid(True)

axes[2].plot(t, B)
axes[2].set_ylabel('Magnetic Field (T)')
axes[2].grid(True)

axes[3].plot(t, Cf)
axes[3].set_ylabel('Coherence (Cf)')
axes[3].set_xlabel('Time (s)')
axes[3].set_ylim(0, 1.1)
axes[3].grid(True)

plt.tight_layout()
plt.savefig('spinner_simulation.png')
plt.show()

print("Simulation complete. Plot saved as spinner_simulation.png")