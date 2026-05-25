"""
Run all six tests (S1A through S1F)
"""

import subprocess
import sys

tests = ["S1A", "S1B", "S1C", "S1D", "S1E", "S1F"]

for test in tests:
    print(f"\n{'='*60}")
    print(f"Running test_{test}.py")
    print('='*60)
    result = subprocess.run([sys.executable, f"test_{test}.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("ERRORS:")
        print(result.stderr)