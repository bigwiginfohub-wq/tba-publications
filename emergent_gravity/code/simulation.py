"""
N-body simulation with emergent gravity
Uses REBOUND for integration
"""

import rebound
import numpy as np
from emergent_gravity import compute_amplification, RHO_CRITICAL

class EmergentGravitySimulation:
    def __init__(self, alpha=0.1, beta=0.1, gamma=0.05):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.sim = None
        self.particles = []
        
    def init_sim(self, dt=0.01):
        """Initialize REBOUND simulation"""
        self.sim = rebound.Simulation()
        self.sim.integrator = "ias15"  # High-precision integrator
        self.sim.dt = dt
        
    def add_particles(self, positions, velocities, masses):
        """
        Add particles to simulation
        
        Parameters:
        - positions: list of (x, y, z) tuples
        - velocities: list of (vx, vy, vz) tuples
        - masses: list of masses
        """
        self.particles = []
        for i, (pos, vel, mass) in enumerate(zip(positions, velocities, masses)):
            p = rebound.Particle(
                x=pos[0], y=pos[1], z=pos[2],
                vx=vel[0], vy=vel[1], vz=vel[2],
                m=mass
            )
            self.sim.add(p)
            self.particles.append(p)
            
    def emergent_force(self, reb_sim):
        """
        Additional force callback for REBOUND
        Adds emergent amplification to existing gravity
        """
        # This is called by REBOUND after standard gravity
        # For now, we modify acceleration directly
        pass
    
    def compute_local_density(self, particle_index, smoothing_length=0.5):
        """
        Compute local density around a particle using neighbor search
        """
        p = self.particles[particle_index]
        neighbors = self.sim.get_neighbors(p, smoothing_length)
        total_mass = sum(neighbor.m for neighbor in neighbors)
        volume = (4/3) * np.pi * smoothing_length**3
        return total_mass / volume if volume > 0 else 0
    
    def compute_coherence(self):
        """
        Compute global coherence Cf = |v_avg| / (|v_avg| + σ_v)
        """
        velocities = np.array([[p.vx, p.vy, p.vz] for p in self.particles])
        v_avg = np.mean(velocities, axis=0)
        v_avg_mag = np.linalg.norm(v_avg)
        v_std = np.std(velocities, axis=0)
        sigma_v = np.linalg.norm(v_std)
        if v_avg_mag + sigma_v == 0:
            return 0
        return v_avg_mag / (v_avg_mag + sigma_v)
    
    def run(self, tmax=10.0, output_interval=100):
        """Run simulation"""
        times = []
        positions = []
        velocities = []
        
        for i, t in enumerate(np.arange(0, tmax, self.sim.dt)):
            self.sim.integrate(t)
            if i % output_interval == 0:
                times.append(t)
                positions.append([(p.x, p.y, p.z) for p in self.particles])
                velocities.append([(p.vx, p.vy, p.vz) for p in self.particles])
                
        return {
            'times': times,
            'positions': positions,
            'velocities': velocities
        }