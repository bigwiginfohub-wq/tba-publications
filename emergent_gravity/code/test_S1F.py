"""
S1F: External Observer Test — Compare static vs coherent freefall clusters
This is the critical test for emergent gravity
"""

import json
import numpy as np
from emergent_gravity import compute_amplification, RHO_CRITICAL

def create_static_system(n_particles=100, radius=2.0):
    """Static cluster with random motion (low coherence)"""
    positions = []
    velocities = []
    # Total mass = 1.0
    mass_per_particle = 1.0 / n_particles
    
    # Random positions within sphere
    for _ in range(n_particles):
        r = radius * np.random.rand()**(1/3)
        theta = 2 * np.pi * np.random.rand()
        phi = np.arccos(2 * np.random.rand() - 1)
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        positions.append((x, y, z))
        
        # Random velocities (low coherence)
        vx = np.random.randn() * 0.5
        vy = np.random.randn() * 0.5
        vz = np.random.randn() * 0.5
        velocities.append((vx, vy, vz))
    
    return positions, velocities, mass_per_particle

def create_coherent_system(n_particles=100, radius=2.0):
    """Coherent freefall cluster (high coherence)"""
    positions = []
    velocities = []
    mass_per_particle = 1.0 / n_particles
    
    # Same positions as static system
    for _ in range(n_particles):
        r = radius * np.random.rand()**(1/3)
        theta = 2 * np.pi * np.random.rand()
        phi = np.arccos(2 * np.random.rand() - 1)
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        positions.append((x, y, z))
        
        # Coherent velocities (all moving in same direction)
        v_common = 1.0
        vx = v_common
        vy = v_common * 0.5
        vz = v_common * 0.3
        # Add small random perturbation
        vx += np.random.randn() * 0.05
        vy += np.random.randn() * 0.05
        vz += np.random.randn() * 0.05
        velocities.append((vx, vy, vz))
    
    return positions, velocities, mass_per_particle

def compute_coherence(velocities):
    """Compute Cf from list of velocities"""
    vel_array = np.array(velocities)
    v_avg = np.mean(vel_array, axis=0)
    v_avg_mag = np.linalg.norm(v_avg)
    v_std = np.std(vel_array, axis=0)
    sigma_v = np.linalg.norm(v_std)
    if v_avg_mag + sigma_v == 0:
        return 0
    return v_avg_mag / (v_avg_mag + sigma_v)

def compute_density(positions, masses):
    """Estimate density from positions and masses"""
    # Approximate volume from bounding sphere
    all_pos = np.array(positions)
    center = np.mean(all_pos, axis=0)
    distances = np.linalg.norm(all_pos - center, axis=1)
    max_r = np.max(distances)
    if max_r == 0:
        volume = 1
    else:
        volume = (4/3) * np.pi * max_r**3
    total_mass = sum(masses)
    return total_mass / volume

def external_field(positions, masses, test_distance=10.0):
    """Compute gravitational field at test point"""
    test_pos = np.array([test_distance, 0, 0])
    field = 0.0
    G = 1.0  # G = 1 in simulation units
    
    for pos, mass in zip(positions, masses):
        r_vec = test_pos - np.array(pos)
        r = np.linalg.norm(r_vec)
        if r > 0:
            field += G * mass / r**2
    
    return field

def run_test():
    n_particles = 100
    radius = 2.0
    alpha, beta, gamma = 0.1, 0.1, 0.05
    
    # Create systems
    pos_static, vel_static, mass = create_static_system(n_particles, radius)
    pos_coherent, vel_coherent, _ = create_coherent_system(n_particles, radius)
    
    # Compute parameters
    Cf_static = compute_coherence(vel_static)
    Cf_coherent = compute_coherence(vel_coherent)
    
    rho = compute_density(pos_static, [mass] * n_particles)
    rho_norm = rho / RHO_CRITICAL
    
    # Compute amplification factors
    A_static = 1 + alpha * rho_norm + beta * Cf_static + gamma * rho_norm * Cf_static
    A_coherent = 1 + alpha * rho_norm + beta * Cf_coherent + gamma * rho_norm * Cf_coherent
    
    # Compute Newtonian field (same for both systems, same mass distribution)
    newtonian_field = external_field(pos_static, [mass] * n_particles)
    
    # Emergent fields
    emergent_field_static = newtonian_field * A_static
    emergent_field_coherent = newtonian_field * A_coherent
    
    result = {
        "test": "S1F",
        "parameters": {
            "n_particles": n_particles,
            "radius": radius,
            "alpha": alpha,
            "beta": beta,
            "gamma": gamma,
            "rho_critical": RHO_CRITICAL
        },
        "static_system": {
            "rho": rho,
            "rho_norm": rho_norm,
            "Cf": Cf_static,
            "amplification": A_static,
            "newtonian_field": newtonian_field,
            "emergent_field": emergent_field_static
        },
        "coherent_system": {
            "rho": rho,
            "rho_norm": rho_norm,
            "Cf": Cf_coherent,
            "amplification": A_coherent,
            "newtonian_field": newtonian_field,
            "emergent_field": emergent_field_coherent
        },
        "amplification_ratio": A_coherent / A_static,
        "field_ratio": emergent_field_coherent / emergent_field_static
    }
    
    print(json.dumps(result, indent=2))
    
    with open("results_S1F.json", "w") as f:
        json.dump(result, f, indent=2)
    
    # Print summary
    print("\n" + "="*50)
    print("S1F RESULTS SUMMARY")
    print("="*50)
    print(f"Static system Cf: {Cf_static:.4f}")
    print(f"Coherent system Cf: {Cf_coherent:.4f}")
    print(f"Amplification ratio (coherent/static): {A_coherent / A_static:.4f}")
    print(f"External field ratio: {emergent_field_coherent / emergent_field_static:.4f}")
    print("="*50)

if __name__ == "__main__":
    run_test()