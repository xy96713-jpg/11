---
name: netease_expert
description: Specialized skill for downloading high-quality audio from NetEase Cloud Music (163.com) using PyNCM.
---

# NetEase Music Expert

This skill provides direct integration with NetEase Cloud Music for downloading tracks, albums, and playlists.

## Capabilities
- Search and download songs by title/artist.
- Download by direct ID or URL.
- Automatic VIP quality selection (requires cookies if VIP).
- Metadata and cover art embedding.

## Dependencies
- `pyncm`: Core API interaction.
- `mutagen`: For ID3 tagging.
- `requests`: for downloading.

## Usage
Run the main script:
`python scripts/netease_handler.py [SEARCH_QUERY_OR_ID]`
