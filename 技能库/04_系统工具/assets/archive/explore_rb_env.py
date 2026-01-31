import pyrekordbox
import os

def explore_rekordbox_env():
    print("=== Rekordbox Env Exploration ===")
    try:
        # Check database path
        db_path = pyrekordbox.config.get_config("db6")["db_path"]
        print(f"Database Path: {db_path}")
        
        # Pioneer folder is usually where analysis files live
        pioneer_path = os.path.dirname(os.path.dirname(db_path))
        print(f"Pioneer Root: {pioneer_path}")
        
    except Exception as e:
        print(f"Error exploring config: {e}")

if __name__ == "__main__":
    explore_rekordbox_env()
