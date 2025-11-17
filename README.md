# amuseUSB

**amuseUSB** is an intelligent, automated USB music loader that scans
your existing songs, gathers metadata, generates AI-based personalized
music recommendations, and batch-downloads new MP3 tracks directly into
your USB drive with high speed and fully visible per-song progress bars.

Built with Python and designed for portability, amuseUSB turns any USB
stick into a dynamically curated music library.

------------------------------------------------------------------------

## 🚀 Features

-   **Reads existing USB music folders** and extracts song metadata
-   **AI-powered recommendation generation** (Gemini API expected)
-   **Parallel downloading (5 at a time)** for maximum speed
-   **Per-song live progress bars** using Rich
-   **FFmpeg-backed MP3 conversion** (high-quality audio)
-   **Automatic retry system** for unstable network links
-   **Clean and safe output file names**
-   **Automatic USB directory handling**
-   **Full logging and error reporting**

------------------------------------------------------------------------

## 📂 Project Structure

    amuseUSB/
     ├── music_recommendations.json
     ├── phase1_scan_usb.py
     ├── phase2_get_recommendations.py
     ├── phase3_download_recommendations.py
     ├── README.md
     

------------------------------------------------------------------------

## 🛠 Requirements

-   Python 3.10+

-   FFmpeg (must set `--ffmpeg-location`)

-   Packages:

        yt_dlp
        rich

    Install:

    ``` bash
    pip install yt-dlp rich
    ```

------------------------------------------------------------------------

## 📥 Setup

1.  **Install FFmpeg**\
    Download from the official site and extract it somewhere permanent.

2.  **Locate FFmpeg path**\
    Example:

        D:\ffmpeg-8.0-essentials_build\bin

3.  **Update the script**\
    Set:

    ``` python
    FFMPEG_PATH = r"D:/ffmpeg-8.0-essentials_build/bin"
    USB_PATH = "E:/AI_Recommendations"
    ```

4.  **Place your `music_recommendations.json`**\
    Format:

    ``` json
    {
      "recommendations": [
        { "song": "Shape of You", "artist": "Ed Sheeran" },
        { "song": "Starboy", "artist": "The Weeknd" }
      ]
    }
    ```

You're ready to go.

------------------------------------------------------------------------

## ▶ Running amuseUSB

``` bash
python phase1_scan_usb.py #Step one
python phase2_get_recommendations.py #Step two
python phase3_download_recommendations.py #Step three
```

You will see progress bars like:

    Searching: "Song Name"
    Downloading: ███████░░░ 74%

Downloads are saved directly into your USB.

------------------------------------------------------------------------

## ⚡ Performance

-   **Parallel downloads:** 5
-   **Total speed:** \~50--80 Mbps depending on network
-   **Average size per 100 HQ MP3 files:** 0.7--1.1 GB

------------------------------------------------------------------------

## 🔧 Configuration

Inside the script:

``` python
MAX_THREADS = 5
RETRY_LIMIT = 3
USB_PATH = "E:/AI_Recommendations"
FFMPEG_PATH = "D:/ffmpeg-8.0-essentials_build/bin"
```

Change these as needed.

------------------------------------------------------------------------

## 🧑‍💻 Author

**Dewashish Lambore**

------------------------------------------------------------------------

## 📄 License

This project is open for personal use and modification. Attribution
appreciated.

------------------------------------------------------------------------

## ⭐ Support

If you enjoyed this project, consider starring the GitHub repo!
