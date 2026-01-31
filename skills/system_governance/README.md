# System Governance & Protocols (V7.5)

## 👑 Core Directives
1.  **Single Source of Truth**: `scripts/enhanced_harmonic_set_sorter.py` is the ONLY allowed engine for Set Generation.
2.  **No Ad-Hoc Scripts**: DO NOT create temporary scripts like `test_sort.py` or `old_version_v6.py`.
    - If you must test, use a branch or a `tests/` directory (and delete after use).
    - Features must be integrated into Main or discarded.

## 🛡️ Feature Protocols
- **Remix Guard**: System MUST prevent duplicate versions of the same song (e.g., Original vs Remix) in the same set unless explicitly overridden.
- **Universal Output**: System MUST output ALL analyzed tracks (including those rejected) to a "Residuals" or "Incompatible" section to ensure transparency.

## 🚀 Standard Workflow
- Please follow the official **[DJ Set Generation Workflow](file:///d:/anti/.agent/workflows/generate-set.md)** for all production runs.
