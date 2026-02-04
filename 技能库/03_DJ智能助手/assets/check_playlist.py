
import os
import sys
from pyrekordbox import db6
from sqlalchemy import text

def check_tags():
    pid = "226494199"
    print(f"\nChecking Tags for Playlist {pid}...")
    try:
        db = db6.Rekordbox6Database()
        
        # 1. Check if any MyTags exist in the system
        tags = db.session.execute(text("SELECT ID, Name FROM djmdMyTag LIMIT 10")).fetchall()
        print(f"System Tags Sample: {tags}")
        
        # 2. Check tags for playlist tracks
        # We need to join djmdSongMyTag
        print("\nChecking tags for first 5 tracks in playlist:")
        playlist_songs = list(db.get_playlist_songs(PlaylistID=pid))
        
        for i, s in enumerate(playlist_songs[:5]):
            # Get basic content
            content = db.session.execute(
                text("SELECT ID, Title, AnalysisDataPath FROM djmdContent WHERE ID = :id"), 
                {"id": s.ContentID}
            ).fetchone()
            
            if content:
                print(f" Track: {content.Title} (ID: {content.ID})")
                
                # Fetch associated tags
                # content.ID matches djmdSongMyTag.ContentID
                # djmdSongMyTag.MyTagID matches djmdMyTag.ID
                query = text("""
                    SELECT t.Name, t.ParentID 
                    FROM djmdMyTag t
                    JOIN djmdSongMyTag st ON st.MyTagID = t.ID
                    WHERE st.ContentID = :cid
                """)
                track_tags = db.session.execute(query, {"cid": content.ID}).fetchall()
                if track_tags:
                    print(f"  -> Tags: {[t[0] for t in track_tags]}")
                else:
                    print(f"  -> No Tags found.")
                    
    except Exception as e:
        print(f"Check failed: {e}")

if __name__ == "__main__":
    check_tags()
