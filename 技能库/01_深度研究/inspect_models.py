from pyrekordbox import Rekordbox6Database

def main():
    db = Rekordbox6Database()
    content = list(db.get_content())
    if not content:
        print("No content found")
        return
        
    track = content[0]
    # Check if we can find cues on a track
    if hasattr(track, 'Cues'):
        cues = list(track.Cues)
        print(f"Track '{track.Title}' has {len(cues)} cues.")
        for i, cue in enumerate(cues):
            print(f"\nCue {i+1}:")
            # Print all non-private attributes
            for attr in dir(cue):
                if not attr.startswith('_') and not hasattr(getattr(cue, attr), '__call__'):
                    print(f"  {attr}: {getattr(cue, attr)}")
    else:
        print(f"Track '{track.Title}' has no Cues attribute.")

if __name__ == "__main__":
    main()
