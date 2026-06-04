import pandas as pd
import numpy as np
import time
import logging
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
import astropy.units as u

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Configure Vizier for Pan-STARRS DR2 (Catalog II/349/ps2)
Vizier.ROW_LIMIT = -1
# We want r-band and i-band Kron (K) and PSF (P) magnitudes
Vizier.columns = ['rKmag', 'rPmag', 'iKmag', 'iPmag']

def query_panstarrs(ra, dec, radius_arcsec=1.5):
    """Queries Pan-STARRS DR2 for morphology metrics"""
    coord = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
    try:
        result = Vizier.query_region(coord, radius=radius_arcsec * u.arcsec, catalog="II/349/ps2")
        if result and len(result) > 0:
            tab = result[0]
            # Extract r-band magnitudes safely
            rk = tab['rKmag'][0]
            rp = tab['rPmag'][0]
            
            rk = np.nan if np.ma.is_masked(rk) else float(rk)
            rp = np.nan if np.ma.is_masked(rp) else float(rp)
            
            if not np.isnan(rk) and not np.isnan(rp):
                return rp - rk # PSF - Kron. >0.05 means extended (Galaxy). ~0 means Point Source (QSO/Star).
            return np.nan
        return np.nan
    except Exception as e:
        logging.warning(f"VizieR Pan-STARRS query failed: {e}")
        return np.nan

if __name__ == "__main__":
    print("="*60)
    print("PHASE 5: PAN-STARRS MORPHOLOGY BREAK")
    print("="*60)
    print("Testing the 3 High-Priority WISE AGN Candidates...")
    
    # The 3 Top Candidates identified by the pipeline
    top_candidates = [
        {"source_id": "3784388077842869120", "ra": None, "dec": None, "w1_w2": 1.212},
        {"source_id": "1651306279820174720", "ra": None, "dec": None, "w1_w2": 1.275},
        {"source_id": "5682539391022643072", "ra": None, "dec": None, "w1_w2": 1.274}
    ]
    
    # Load coordinates from our final ranked list
    df = pd.read_csv('phase4_final_ranked_candidates.csv')
    
    for cand in top_candidates:
        row = df[df['source_id'] == int(cand['source_id'])]
        if not row.empty:
            cand['ra'] = row['ra'].values[0]
            cand['dec'] = row['dec'].values[0]
            
    print(f"\n{'Source ID':<22} | {'W1-W2':>6} | {'PSF-Kron':>8} | {'Morphology Interpretation'}")
    print("-" * 75)
    
    for cand in top_candidates:
        if cand['ra'] is not None:
            psf_kron = query_panstarrs(cand['ra'], cand['dec'])
            
            if np.isnan(psf_kron):
                morph = "Not found in Pan-STARRS DR2"
                psf_kron_str = "  N/A  "
            else:
                psf_kron_str = f"{psf_kron:+.3f}"
                if psf_kron > 0.05:
                    morph = "EXTENDED (Likely Galaxy)"
                else:
                    morph = "POINT SOURCE (Likely QSO/AGN)"
                    
            print(f"{cand['source_id']:<22} | {cand['w1_w2']:>6.3f} | {psf_kron_str:>8} | {morph}")
            time.sleep(0.5) # Polite rate limiting
            
    print("\n" + "="*60)
    print("ASTROPHYSICAL CONTEXT:")
    print("Stars:      PSF-Kron ≈ 0.0, W1-W2 ≈ 0.0")
    print("Quasars:    PSF-Kron ≈ 0.0, W1-W2 > 0.8  (Point source, hot dust)")
    print("Galaxies:   PSF-Kron > 0.05, W1-W2 varies (Extended)")
    print("="*60)