import pandas as pd
import hashlib
import json
import os
from datetime import datetime

def seal_time_capsule():
    catalog_file = 'data/tracebind_followup_top100_refined.csv'
    if not os.path.exists(catalog_file):
        print(f"❌ Could not find {catalog_file}.")
        return

    print("⏳ Sealing TRACEBIND DR4 Time Capsule...")
    
    # 1. Read the catalog
    df = pd.read_csv(catalog_file)
    
    # 2. Compute SHA-256 Hash (Cryptographic proof the file hasn't been altered)
    with open(catalog_file, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
        
    # 3. Generate the Manifest
    manifest = {
        "project": "TRACEBIND",
        "capsule_name": "DR4 NSS Prediction Time Capsule",
        "date_sealed": datetime.utcnow().isoformat() + "Z",
        "catalog_file": catalog_file,
        "sha256_hash": file_hash,
        "total_targets": len(df),
        "mean_followup_score": float(df['followup_score'].mean()),
        "min_followup_score": float(df['followup_score'].min()),
        "max_followup_score": float(df['followup_score'].max()),
        "scientific_purpose": (
            "This catalog contains the Top 100 'Unexplained' high-tension stars "
            "identified by TRACEBIND v1.0. These stars are currently NOT in the "
            "Gaia DR3 NSS catalog, but are ranked by their mathematical similarity "
            "to known NSS systems. This capsule is sealed prior to Gaia DR4 release "
            "to serve as a blind, prospective prediction test of the TRACEBIND framework."
        ),
        "status": "SEALED"
    }
    
    # 4. Save the Manifest
    manifest_file = 'data/DR4_TIME_CAPSULE_MANIFEST.json'
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=4)
        
    print("="*85)
    print("✅ DR4 TIME CAPSULE SEALED")
    print("="*85)
    print(f"Timestamp:  {manifest['date_sealed']}")
    print(f"SHA-256:    {file_hash}")
    print(f"Targets:    {len(df)}")
    print(f"Score Range: {manifest['min_followup_score']:.4f} to {manifest['max_followup_score']:.4f}")
    print("="*85)
    print("This manifest proves the catalog was generated BEFORE Gaia DR4.")
    print("Do not modify 'tracebind_followup_top100_refined.csv' from this point forward.")
    print("When DR4 is released, cross-match these Source IDs against the new NSS tables.")
    print("="*85)

if __name__ == "__main__":
    seal_time_capsule()