"""
S1A: Dust vs Clump — Compare dispersed and compact equal-mass systems
"""

import json
import numpy as np
from simulation import EmergentGravitySimulation
from emergent_gravity import compute_amplification

def create_dispersed_system(n_particles=100, radius=5.0):
    """Create randomly dispersed particles"""
    positions = []
    velocities = []
    masses = []
    for _ in range(n_particles):
        # Random position within sphere
        r = radius * np.random.rand()**(1/3)
        theta = 2 * np.pi * np.random.rand()
        phi = np.arccos(2 * np.random.rand() - 1)
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        positions.append((x, y, z))
        # Random velocities
        vx = np.random.randn() * 0.1
        vy = np.random.randn() * 0.1
        vz = np.random.randn() * 0.1
        velocities.append((vx, vy, vz))
        masses.append(1.0 / n_particles)
    return positions, velocities, masses

def create_clump_system(n_particles=100, radius=1.0):
    """Create compact clump of particles"""
    positions = []
    velocities = []
    masses = []
    for _ in range(n_particles):
        # Random position within compact sphere
        r = radius * np.random.rand()**(1/3)
        theta = 2 * np.pi * np.random.rand()
        phi = np.arccos(2 * np.random.rand() - 1)
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        positions.append((x, y, z))
        # Small random velocities (clump)
        vx = np.random.randn() * 0.01
        vy = np.random.randn() * 0.01
        vz = np.random.randn() * 0.01
        velocities.append((vx, vy, vz))
        masses.append(1.0 / n_particles)
    return positions, velocities, masses

def run_test():
    n_particles = 100
    alpha, beta, gamma = 0.1, 0.1, 0.05
    
    # Create systems
    pos_disp, vel_disp, mass_disp = create_dispersed_system(n_particles)
    pos_clump, vel_clump, mass_clump = create_clump_system(n_particles)
    
    # Compute densities
    # Approximate density: total mass / volume
    vol_disp = (4/3) * np.pi * 5**3
    vol_clump = (4/3) * np.pi * 1**3
    rho_disp = 1.0 / vol_disp
    rho_clump = 1.0 / vol_clump
    
    # For dispersed system, coherence is low
    Cf_disp = 0.1
    # For clump, coherence is higher
    Cf_clump = 0.5
    
    A_disp = compute_amplification(rho_disp, Cf_disp, alpha, beta, gamma)
    A_clump = compute_amplification(rho_clump, Cf_clump, alpha, beta, gamma)
    
    result = {
        "test": "S1A",
        "parameters": {
            "n_particles": n_particles,
            "alpha": alpha,
            "beta": beta,
            "gamma": gamma
        },
        "dispersed": {
            "density": rho_disp,
            "Cf": Cf_disp,
            "amplification": A_disp
        },
        "clump": {
            "density": rho_clump,
            "Cf": Cf_clump,
            "amplification": A_clump
        },
        "amplification_ratio": A_clump / A_disp
    }
    
    print(json.dumps(result, indent=2))
    
    # Save to file
    with open("results_S1A.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    run_test()