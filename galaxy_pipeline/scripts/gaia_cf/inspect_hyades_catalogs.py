"""
Inspect VizieR Hyades membership catalogs to verify schema before hardcoding.
Run ONCE to choose the correct catalog for Phase 4.
License: CC0 1.0 Universal
"""
from astroquery.vizier import Vizier

CATALOGS = {
    "Lodieu+2019": "J/A+A/623/A35",
    "Nunez+2022":  "J/ApJ/931/45",
    "CantatGaudin+2022": "J/A+A/658/A41",
}

viz = Vizier()
viz.ROW_LIMIT = 3

for label, cat_id in CATALOGS.items():
    print(f"\n{'='*70}")
    print(f"📚 {label} ({cat_id})")
    print('='*70)
    try:
        tables = viz.get_catalogs(cat_id)
        if len(tables) == 0:
            print("   ⚠️  No tables returned")
            continue
        for name in tables.keys():
            t = tables[name]
            print(f"\n   Table: {name} ({len(t)} sample rows)")
            print(f"   Columns: {t.colnames}")
            # Check for key columns
            has_cluster = any('cluster' in c.lower() for c in t.colnames)
            has_pmem = any('pmem' in c.lower() or 'member' in c.lower() for c in t.colnames)
            has_sourceid = any('source' in c.lower() or 'gaia' in c.lower() for c in t.colnames)
            print(f"   Has Cluster col: {has_cluster}")
            print(f"   Has Membership col: {has_pmem}")
            print(f"   Has Gaia Source ID: {has_sourceid}")
            if len(t) > 0:
                print(f"   Sample row: {dict(zip(t.colnames, t[0]))}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "="*70)
print("✅ INSPECTION COMPLETE")
print("Choose the catalog with: Cluster column + Membership probability + Gaia DR3 source_id")
print("Then hardcode those exact column names in phase4_real_hyades.py")