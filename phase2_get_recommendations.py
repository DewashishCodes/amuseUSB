import os
import json
import re
from google import generativeai as genai


# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
genai.configure(api_key=os.getenv("GENAI_API_KEY"))
MODEL_NAME = "gemini-flash-latest"
CHUNK_SIZE = 50  # number of songs per Gemini request


# ------------------------------------------------------------
# Load metadata from Phase 1 output
# ------------------------------------------------------------
def load_metadata():
    print("Loading MP3 metadata from USB scan...")
    with open("usb_music_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded metadata for {len(data)} songs.\n")
    return data


# ------------------------------------------------------------
# Utility to chunk list into smaller groups
# ------------------------------------------------------------
def chunks(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


# ------------------------------------------------------------
# Extract first JSON object from Gemini output
# ------------------------------------------------------------
def extract_json(text):
    """
    Extract the first valid JSON object from a string.
    Handles markdown, extra text, and multiple blocks.
    """
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None
    return None


# ------------------------------------------------------------
# Summarize a batch of songs safely
# ------------------------------------------------------------
def summarize_batch(batch, model):
    prompt = f"""
You are analyzing a music library.

Summarize this batch of songs into a compact "music taste profile".

RETURN ONLY JSON like:
{{
  "genres": [],
  "moods": [],
  "languages": [],
  "top_artists": []
}}

Batch Songs:
{json.dumps(batch, indent=2)}
"""

    response = model.generate_content(prompt)

    # Collect all text parts
    all_text = ""
    for cand in response.candidates:
        for part in cand.content.parts:
            if hasattr(part, "text"):
                all_text += part.text

    if not all_text.strip():
        print("ERROR: Gemini returned empty text for a batch")
        raise ValueError("Empty Gemini response")

    # Extract JSON
    json_data = extract_json(all_text)
    if json_data is None:
        print("\n----- RAW GEMINI OUTPUT -----\n")
        print(all_text)
        print("\n----- END RAW OUTPUT -----\n")
        raise ValueError("Gemini did not return valid JSON for a batch.")

    return json_data


# ------------------------------------------------------------
# Get final song recommendations
# ------------------------------------------------------------
def get_recommendations(final_profile, model):
    prompt = f"""
Based on this music taste profile:

{json.dumps(final_profile, indent=2)}

Recommend EXACTLY 100 NEW songs the user is likely to enjoy.

RETURN ONLY JSON:
{{
  "recommendations": [
    {{
      "song": "",
      "artist": "",
      "reason": ""
    }}
  ]
}}
"""

    response = model.generate_content(prompt)

    all_text = ""
    for cand in response.candidates:
        for part in cand.content.parts:
            if hasattr(part, "text"):
                all_text += part.text

    json_data = extract_json(all_text)

    if json_data is None:
        print("\n----- RAW GEMINI OUTPUT -----\n")
        print(all_text)
        print("\n----- END RAW OUTPUT -----\n")
        raise ValueError("Gemini did not return valid JSON.")

    return json_data


# ------------------------------------------------------------
# MAIN PROCESS
# ------------------------------------------------------------
def main():
    metadata = load_metadata()
    model = genai.GenerativeModel(MODEL_NAME)

    print("Summarizing batches...\n")
    batch_profiles = []

    for idx, batch in enumerate(chunks(metadata, CHUNK_SIZE)):
        print(f"Processing batch {idx + 1}...")
        profile = summarize_batch(batch, model)
        batch_profiles.append(profile)

    print(f"\nCreated {len(batch_profiles)} taste summaries.\n")

    # Combine profiles
    final_profile = {
        "genres": [],
        "moods": [],
        "languages": [],
        "top_artists": []
    }

    for p in batch_profiles:
        final_profile["genres"].extend(p.get("genres", []))
        final_profile["moods"].extend(p.get("moods", []))
        final_profile["languages"].extend(p.get("languages", []))
        final_profile["top_artists"].extend(p.get("top_artists", []))

    # Remove duplicates
    for key in final_profile:
        final_profile[key] = list(set(final_profile[key]))

    print("Final taste profile created. Asking Gemini for recommendations...\n")

    recommendations = get_recommendations(final_profile, model)

    # Save recommendations
    with open("music_recommendations.json", "w", encoding="utf-8") as f:
        json.dump(recommendations, f, indent=2, ensure_ascii=False)

    print("DONE! Saved recommendations to music_recommendations.json\n")


# ------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------
if __name__ == "__main__":
    main()
