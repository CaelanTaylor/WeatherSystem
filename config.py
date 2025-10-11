# config.py

DEFAULT_LOCATION = "Test Location"
DEFAULT_DB_ENABLED = True

def load_config():
    """Loads configuration settings from a file or uses defaults."""
    try:
        # Attempt to load from a file (e.g., config.txt)
        with open("config.txt", "r") as f:
            lines = f.readlines()
            location = lines[0].strip() if len(lines) > 0 else DEFAULT_LOCATION
            db_enabled = (lines[1].strip().lower() == "true") if len(lines) > 1 else DEFAULT_DB_ENABLED
            return location, db_enabled
    except FileNotFoundError:
        # If the file doesn't exist, use the default values
        return DEFAULT_LOCATION, DEFAULT_DB_ENABLED

def save_config(location, db_enabled):
    """Saves configuration settings to a file."""
    with open("config.txt", "w") as f:
        f.write(location + "\n")
        f.write(str(db_enabled) + "\n")