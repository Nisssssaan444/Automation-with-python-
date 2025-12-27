import os
import shutil
from datetime import datetime

# Source directory
source_dir = "/home/nissan/Download"

# Configuration for destination directories
# Format: "Category": {"extensions": [...], "base_path": "...", "recent_sub": "..."}
config = {
    "Music": {
        "extensions": (".mp3",),
        "base_path": "/home/nissan/Music",
        "recent_sub": "recent"
    },
    "Pictures": {
        "extensions": (".png", ".jpg", ".jpeg"),
        "base_path": "/home/nissan/Pictures",
        "recent_sub": "recents"
    },
    "Videos": {
        "extensions": (".mp4", ".mov"),
        "base_path": "/home/nissan/Videos",
        "recent_sub": "recent"
    },
    "Documents": {
        "extensions": (".pdf",),
        "base_path": "/home/nissan/Documents",
        "recent_sub": "recent"
    }
}

# Ensure destination directories exist
for key, data in config.items():
    recent_path = os.path.join(data["base_path"], data["recent_sub"])
    os.makedirs(recent_path, exist_ok=True)

now = datetime.now()
threshold_days = 3

print(f"Scanning {source_dir}...")

if os.path.exists(source_dir):
    for filename in os.listdir(source_dir):
        source_path = os.path.join(source_dir, filename)
        
        # Skip if it is a directory
        if not os.path.isfile(source_path):
            continue

        file_ext = os.path.splitext(filename)[1].lower()
        
        # Determine destination
        target_folder = None
        
        for category, data in config.items():
            if file_ext in data["extensions"]:
                # Check file age
                file_mtime = datetime.fromtimestamp(os.path.getmtime(source_path))
                age_days = (now - file_mtime).days
                
                if age_days < threshold_days:
                    target_folder = os.path.join(data["base_path"], data["recent_sub"])
                else:
                    # If older than 3 days, move to the base category folder
                    target_folder = data["base_path"]
                break
        
        if target_folder:
            destination_path = os.path.join(target_folder, filename)
            try:
                # Handle potential duplicate filenames
                if os.path.exists(destination_path):
                    base, ext = os.path.splitext(filename)
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    new_filename = f"{base}_{timestamp}{ext}"
                    destination_path = os.path.join(target_folder, new_filename)
                    print(f"File exists. Renaming to {new_filename}")

                shutil.move(source_path, destination_path)
                print(f"Moved [{filename}] to [{target_folder}]")
            except Exception as e:
                print(f"Error moving {filename}: {e}")
else:
    print(f"Source directory {source_dir} does not exist.")
