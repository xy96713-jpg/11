---
description: Generate a DJ Set from a Rekordbox playlist or search query
---

# Generate DJ Set Workflow

This workflow uses `enhanced_harmonic_set_sorter.py` (V7.5+) to create professional DJ sets.

## Prerequisites
- Rekordbox running (for DB access)
- Python 3.12+ with dependencies installed
- Tracks analyzed in Rekordbox

## Workflow Steps

// turbo-all

### 1. Set Environment
```powershell
$env:PYTHONPATH="d:/anti;d:/anti/core;d:/anti/core/rekordbox-mcp"
```

### 2. Run Set Generator

**Option A: From Playlist Name**
```powershell
python d:/anti/scripts/enhanced_harmonic_set_sorter.py "PLAYLIST_NAME" --master
```

**Option B: From Search Query (V6.3+)**
```powershell
python d:/anti/scripts/enhanced_harmonic_set_sorter.py --query "ARTIST_NAME" --master
```

### 3. Available Flags
| Flag | Description |
|------|-------------|
| `--master` | Generate single unified M3U + Master XML |
| `--boutique` | Limit to 30-45 high-quality tracks |
| `--live` | Include ALL tracks (extended set) |
| `--query "X"` | Search DB instead of using playlist name |

### 4. Output Location
All generated files are saved to:
```
D:\生成的set\
```
- `*_Master_Unified_*.m3u` - Import to Rekordbox/CDJ
- `*_混音建议_*.txt` - Mixing advice report
- `*_*.csv` - Spreadsheet view

## Troubleshooting
- **ModuleNotFoundError**: Check `PYTHONPATH` includes `d:/anti` and subfolders.
- **Rekordbox Warning**: Close Rekordbox or use read-only mode.
- **2 Song Set**: Check search query spelling (e.g., "NewJeans" vs "New Jeans").
