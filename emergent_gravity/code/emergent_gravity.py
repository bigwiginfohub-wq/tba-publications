"""
Emergent Gravity Model
F_eff = G*m1*m2/r^2 * (1 + α*ρ_norm + β*Cf + γ*ρ_norm*Cf)
"""

import numpy as np

# Normalization constants
RHO_CRITICAL = 1e6  # Reference density

def compute_amplification(rho, Cf, alpha=0.1, beta=0.1, gamma=0.05):
    """
    Compute amplification factor A = 1 + α*ρ_norm + β*Cf + γ*ρ_norm*Cf
    
    Parameters:
    - rho: local mass density
    - Cf: coherence factor (0 to 1)
    - alpha, beta, gamma: coefficients
    
    Returns:
    - amplification factor A
    """
    rho_norm = rho / RHO_CRITICAL
    A = 1 + alpha * rho_norm + beta * Cf + gamma * rho_norm * Cf
    return A

def compute_rho_norm(rho):
    """Return normalized density"""
    return rho / RHO_CRITICAL