import numpy as np
import pandas as pd
from astroquery.gaia import Gaia
import time
import logging
import json
from datetime import datetime
from astropy.coordinates import SkyCoord
import astropy.units as u

# Configure logging for audit trail
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

class GaiaRawSampler:
    def __init__(self, n_samples=25, seed=42, max_sources_per_region=500):
        self.n_samples = n_samples
        self.rng = np.random.default_rng(seed)
        self.max_sources_per_region = max_sources_per_region
        Gaia.MAIN_GAIA_TABLE = "gaiadr3.gaia_source"
        Gaia.ROW_LIMIT = -1

    def generate_uniform_sky_coords(self):
        """
        Generates uniformly distributed random points on a sphere.
        Mathematically rigorous alternative to HEALPix for unbiased sampling.
        """
        # u is uniform in [-1, 1], which corresponds to cos(theta)
        u = self.rng.uniform(-1, 1, size=self.n_samples)
        # ra is uniform in [0, 360] degrees
        ra = self.rng.uniform(0, 360, size=self.n_samples)
        # dec = arcsin(u) converted to degrees
        dec = np.degrees(np.arcsin(u))
        return ra, dec

    def query_gaia_region(self, ra, dec, timestamp: str, sample_id: int, radius_deg=0.3):
        # TOP 5000 prevents massive downloads from dense fields
        query = f"""
        SELECT TOP 5000
            source_id, ra, dec,
            parallax, parallax_error,
            pmra, pmra_error, pmdec, pmdec_error,
            phot_g_mean_mag, phot_g_mean_flux_error,
            bp_rp, phot_bp_mean_mag, phot_rp_mean_mag,
            ruwe, astrometric_excess_noise,
            radial_velocity, radial_velocity_error
        FROM gaiadr3.gaia_source
        WHERE CONTAINS(
            POINT('ICRS', ra, dec),
            CIRCLE('ICRS', {ra}, {dec}, {radius_deg})
        ) = 1
        """
        try:
            job = Gaia.launch_job_async(query)
            result = job.get_results()
            df = result.to_pandas()
            
            if not df.empty:
                # Compute accurate Galactic coordinates using Astropy
                coords = SkyCoord(ra=df["ra"].values*u.deg, dec=df["dec"].values*u.deg, frame="icrs")
                df["l"] = coords.galactic.l.deg
                df["b"] = coords.galactic.b.deg
                
                # Uniform source sampling within the region to prevent dense-region domination
                if len(df) > self.max_sources_per_region:
                    df = df.sample(n=self.max_sources_per_region, random_state=self.rng.integers(0, 10000))
                
                # Append provenance trail
                df['query_ra'] = ra
                df['query_dec'] = dec
                df['query_radius_deg'] = radius_deg
                df['query_timestamp'] = timestamp
                df['sample_id'] = sample_id
            return df
        except Exception as e:
            logging.error(f"Query failed at RA={ra:.2f}, DEC={dec:.2f}: {e}")
            return None

    def run(self):
        dataset = []
        ra_array, dec_array = self.generate_uniform_sky_coords()
        timestamp = datetime.utcnow().isoformat()
        
        logging.info(f"Sampling {self.n_samples} random uniform sky regions (max {self.max_sources_per_region} sources/region, radius=0.3 deg)...")

        for i in range(self.n_samples):
            ra, dec = ra_array[i], dec_array[i]
            logging.info(f"Querying Region {i+1}/{self.n_samples}: RA={ra:.2f}, DEC={dec:.2f}")
            
            df = self.query_gaia_region(ra, dec, radius_deg=0.3, timestamp=timestamp, sample_id=i)
            if df is not None and len(df) > 0:
                dataset.append(df)
            
            time.sleep(1.5) # Rate limiting

        if not dataset:
            logging.warning("No data collected.")
            return None
            
        full_df = pd.concat(dataset, ignore_index=True)
        
        # Duplicate-source protection
        initial_count = len(full_df)
        full_df = full_df.drop_duplicates(subset=["source_id"])
        if initial_count != len(full_df):
            logging.info(f"Removed {initial_count - len(full_df)} duplicate sources from overlapping regions.")
            
        logging.info(f"Successfully aggregated {len(full_df)} UNIQUE sources with balanced sky-area weighting.")
        return full_df

    def phase_1b_audit(self, df):
        logging.info("--- PHASE 1B: DATA QUALITY & BIAS AUDIT ---")
        
        ruwe_dist = {
            "median": float(df['ruwe'].median()),
            "p95": float(df['ruwe'].quantile(0.95)),
            "fraction_gt_1.4": float((df['ruwe'] > 1.4).mean()),
            "fraction_gt_2.0": float((df['ruwe'] > 2.0).mean())
        }
        
        audit_report = {
            "total_unique_sources": len(df),
            "unique_sample_regions": int(df['sample_id'].nunique()),
            "null_parallax_pct": float((df['parallax'].isna().sum() / len(df)) * 100),
            "mean_parallax_error": float(df['parallax_error'].mean()),
            "ruwe_distribution": ruwe_dist,
            "galactic_latitude_coverage": {
                "mid_plane_frac": float((df['b'].abs() < 10).mean()),
                "halo_frac": float((df['b'].abs() > 30).mean())
            }
        }
        
        for key, value in audit_report.items():
            if isinstance(value, dict):
                logging.info(f"{key}:")
                for k, v in value.items():
                    logging.info(f"  - {k}: {v:.4f}" if isinstance(v, float) else f"  - {k}: {v}")
            else:
                logging.info(f"{key}: {value}")
                
        # Save audit JSON for reproducibility
        with open("phase1d_audit.json", "w") as f:
            json.dump(audit_report, f, indent=2)
        logging.info("Saved phase1d_audit.json")
                
        return audit_report


if __name__ == "__main__":
    # Target: ~5,000 to 12,500 rows (25 regions * 500 max)
    sampler = GaiaRawSampler(n_samples=25, seed=42, max_sources_per_region=500)
    
    logging.info("Starting Phase 1D: Large-scale unbiased sampling...")
    data = sampler.run()
    
    if data is not None:
        sampler.phase_1b_audit(data)
        
        output_file = "gaia_phase1_scaled_10k.csv"
        data.to_csv(output_file, index=False)
        logging.info(f"✅ SUCCESS! Saved {len(data)} unique sources to {output_file}")
    else:
        logging.error("Pipeline halted: No data collected.")