import os
import json
from pathlib import Path
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

USB_PATH=r"F:\\" #<--USB Path Here
OUTPUT_JSON="usb_music_metadata.json"

def find_mp3_files(root):
    for dirpath,_,filename in os.walk(root):
        for fn in filename:
            if fn.lower().endswith(".mp3"):
                yield Path(dirpath)/fn
            
def extract_metadata(path:Path):
    data={
        "file_path":str(path),
        "title":path.stem,
        "artist":"Unknown Artist",
        "album":"Unknown Album",
        "composer":"Unknown Composer",
        "duration":None
    }

    try:
        audio=MP3(path, ID3=EasyID3)
        tags=audio.tags or {}

        if "title" in tags:
            data["title"]=tags["title"][0]

        if "artist" in tags:
            data["artist"]=tags["artist"][0]
 
        if "album" in tags:
            data["album"]=tags["album"][0]

        if "composer" in tags:
            data["composer"]=tags["composer"][0]

        if audio.info.length:
            data["duration"]=round(audio.info.length,2)

    except Exception as e:
        print(f"Error reading {path}: {e}")

    return data


def main():
    print(f"Scanning USB drive at {USB_PATH} for MP3 files...")

    songs=[]
    for mp3_file in find_mp3_files(USB_PATH):
        print(f"ReadingL {mp3_file}...")
        metadata=extract_metadata(mp3_file)
        songs.append(metadata)

    print(f"\nFound {len(songs)} MP3 files. Writing metadata to {OUTPUT_JSON}...")

    with open(OUTPUT_JSON,"w",encoding="utf-8") as f:
        json.dump(songs,f,indent=4,ensure_ascii=False)

    print(f"Metadata written to {OUTPUT_JSON} successfully.")

if __name__ == "__main__":
    main()  