import sys
import os
from pathlib import Path

# Path setup
sys.path.insert(0, r"d:/anti/core")
try:
    from mastering_core import MasteringAnalyzer
    print("🚀 [Diagnostic] Importing MasteringAnalyzer...")
    analyzer = MasteringAnalyzer()
    print("🧬 [Diagnostic] Attempting initialization...")
    report = analyzer.initialize() # Assuming initialize returns the report
    print("✅ [Diagnostic] Initialization SUCCESS!")
except Exception as e:
    import traceback
    print(f"❌ [Diagnostic] Initialization FAILED: {e}")
    traceback.print_exc()
