import pyrekordbox

def run():
    try:
        db = pyrekordbox.Rekordbox6Database()
        playlists = list(db.get_playlist())
        print(f"Total playlists: {len(playlists)}")
        for p in playlists:
            print(f"ID: {p.ID} | Name: {p.Name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
