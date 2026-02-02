# Music Download Expert - Dev Snapshot (Non-YouTube Focus)

**Date**: 2026-01-28
**Objective**: Strict "No YouTube" high-quality audio download with perfect metadata.

## 🌟 Core Strategy
1.  **Source Restriction**:
    *   Strictly block `youtube` extractors in `yt-dlp`.
    *   **SoundCloud (SC)**: 仅允许通过 `soundcloud_agent.py` 及其模块化链进行下载。
    *   **NetEase (163)**: 保持原有逻辑。
2.  **Modular Chain**:
    *   `download_and_tag.py` -> `soundcloud_agent.py` -> `ultra_fast_download.py`
    *   强制并行下载、正方形封面裁剪与 ID3 v2.3 写入。

## 📂 Key Scripts (Current State)

### 1. Robust Tagger (`scripts/robust_tagger.py`)
*   **Purpose**: Fixes missing covers and ensures Windows compatibility.
*   **Key Logic**:
    ```python
    # Force ID3 v2.3 for Windows
    audio.save(v2_version=3)
    # iTunes High-Res Cover
    cover_url = result['artworkUrl100'].replace('100x100bb.jpg', '1000x1000bb.jpg')
    ```

### 2. Direct Downloader (`scripts/final_force_download.py`)
*   **Purpose**: Bypass search ambiguity by downloading specific SoundCloud/NetEase IDs.
*   **Key Logic**:
    *   Uses `yt_dlp` with `scsearch1:ID` or direct URL.
    *   Can filter by duration range (e.g., 260-270s for a 4:26 song).

### 3. Main Logic (`scripts/download_and_tag.py`)
*   **Modifications**:
    *   Removed `ytsearch` fallbacks.
    *   Added `extractor_args` to block YouTube.

## 🚀 Workflow for Exact Matches
1.  **Identify**: Get Artist/Title and **Duration** (crucial for distinguishing official from remixes).
2.  **Search & Filter**:
    *   Run `yt-dlp "scsearch20:QUERY" --get-duration` to find the ID with matching length.
3.  **Download**:
    *   Use `final_force_download.py` with the found ID.
4.  **Tag**:
    *   Run `robust_tagger.py` to apply iTunes metadata and high-res cover (ID3 v2.3).

## 📝 Future Optimization Plan
- [ ] consolidate `download_and_tag.py`, `robust_tagger.py`, and `final_force_download.py` into one unified CLI.
- [ ] Add `spotDL` as a first-class provider for metadata, but strictly force non-YT audio sources.
- [ ] Auto-duration matching: Script should auto-reject results with >5s duration difference.
