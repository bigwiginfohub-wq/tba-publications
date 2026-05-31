
---

## Updated Simulation Code (Simplified, Physics-Corrected)

```python
"""
Spinner Dynamo — Corrected Physics, Reaction Wheel Mode
"""

import numpy as np
import matplotlib.pyplot as plt

# Constants
G = 6.674e-11
M_earth = 5.972e24
R_earth = 6.371e6
mu = G * M_earth

# Spacecraft parameters
mass_craft = 1000.0          # kg
I_craft = 500.0              # Craft moment of inertia (kg·m²)
I_rotor = 0.1                # Rotor moment of inertia (kg·m²)
delta_I = 100.0              # I_z - I_y (kg·m²)

# Initial orbit
altitude = 400e3
r = R_earth + altitude
v = np.sqrt(mu / r)

# Rotor initial state
omega = 50.0                 # rad/s
omega_target = 100.0         # rad/s (resonance)
energy_harvested = 0.0

# Craft orientation
phi = 0.0                    # rad
phi_target = 0.0
omega_craft = 0.0

# Control gains
kp = 0.01
kd = 0.1

# Simulation time
dt = 0.1
t_max = 1000
steps = int(t_max / dt)

# Storage
t_array = np.zeros(steps)
omega_array = np.zeros(steps)
phi_array = np.zeros(steps)
E_harvested_array = np.zeros(steps)

for i in range(steps):
    t = i * dt
    
    # Gravity-gradient torque on craft (corrected)
    tau_gg = (3 * mu / r**3) * delta_I * np.sin(2 * phi)
    
    # Control torque (reaction wheel)
    error = phi - phi_target
    tau_control_craft = -kp * error - kd * omega_craft
    tau_control_rotor = -tau_control_craft
    
    # Rotor dynamics
    tau_gen = 0.001 * omega   # Small generator load
    tau_friction = 0.0001 * omega
    net_torque_rotor = tau_control_rotor - tau_gen - tau_friction
    alpha_rotor = net_torque_rotor / I_rotor
    omega += alpha_rotor * dt
    
    # Craft dynamics
    net_torque_craft = tau_gg + tau_control_craft
    alpha_craft = net_torque_craft / I_craft
    omega_craft += alpha_craft * dt
    phi += omega_craft * dt
    
    # Energy harvesting (micro-scale)
    power = tau_gen * omega
    energy_harvested += power * dt
    
    # Store
    t_array[i] = t
    omega_array[i] = omega
    phi_array[i] = phi
    E_harvested_array[i] = energy_harvested

# Calculate upper bound
delta_U_max = (3 * mu / (2 * r**3)) * delta_I
print(f"Maximum available energy per cycle: {delta_U_max:.6f} J")

# Plot
fig, axes = plt.subplots(3, 1, figsize=(10, 10))

axes[0].plot(t_array, omega_array)
axes[0].axhline(omega_target, color='r', linestyle='--', label='Resonance target')
axes[0].set_ylabel('Rotor spin rate (rad/s)')
axes[0].set_title('Spinner Dynamo — Reaction Wheel Mode')
axes[0].legend()
axes[0].grid(True)

axes[1].plot(t_array, np.degrees(phi_array))
axes[1].set_ylabel('Craft orientation (deg)')
axes[1].set_ylim(-5, 5)
axes[1].grid(True)

axes[2].plot(t_array, E_harvested_array)
axes[2].set_ylabel('Harvested energy (J)')
axes[2].set_xlabel('Time (s)')
axes[2].set_yscale('log')
axes[2].grid(True)

plt.tight_layout()
plt.savefig('spinner_reaction_wheel.png')
plt.show()

print(f"Final harvested energy: {energy_harvested:.6f} J")
print(f"Upper bound per cycle: {delta_U_max:.6f} J")