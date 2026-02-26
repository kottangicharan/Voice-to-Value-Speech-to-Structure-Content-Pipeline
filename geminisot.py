# ── 1. IMPORTS & CLIENT SETUP ──────────────────────────────────────────────────

import os
import sys
from pathlib import Path
from google import genai
from google.genai import types

# ── CLIENT SETUP ───────────────────────────────────────────────────────────────
GEMINI_API_KEY = "YOUR_API_KEY_HERE"  # <-- UPDATE THIS with your Gemini API key
client = genai.Client(api_key=GEMINI_API_KEY)


# ── 2. PROMPTS ─────────────────────────────────────────────────────────────────

TRANSCRIPTION_PROMPT = """
You are an EXPERT multilingual speech transcription and content structuring system 
specialized in Indian languages - Telugu, Hindi, English, and any mix of these.

YOUR JOB:
You will receive an audio or video file. Your task is to:
1. Transcribe EVERY spoken word - do NOT skip or summarize any part
2. Detect the DOMINANT language (see rules below) and write ALL output in that language's script
3. Remove ONLY non-content noise: filler sounds (um, uh, hmm), repeated stutters (I I I mean => I mean)
4. Preserve ALL meaningful content - every instruction, every point, every sentence
5. Structure the content logically using proper HTML

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOMINANT LANGUAGE DETECTION (do this FIRST before writing anything):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1 - Listen to the FIRST 3-5 sentences: whatever language/script is used there gives strong priority.
Step 2 - Count overall: which language occupies the MOST words/sentences across the full audio?
Step 3 - The language that wins by BOTH signals (or the stronger one) = DOMINANT LANGUAGE.
Step 4 - Write the ENTIRE transcript output in that dominant language's native script.

Examples:
- Telugu 70% + Hindi 20% + English 10%  →  Dominant = Telugu  →  Write everything in తెలుగు script
- Hindi 60% + English 30% + Telugu 10%  →  Dominant = Hindi   →  Write everything in हिंदी script
- English 80% + Telugu 20%              →  Dominant = English  →  Write everything in English
- Tamil 65% + English 35%              →  Dominant = Tamil    →  Write everything in தமிழ் script

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MIXED LANGUAGE RENDERING RULES (after dominant language is decided):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORE RULE — FULL TRANSLATION INTO DOMINANT LANGUAGE:
- Translate the MEANING of every non-dominant word/phrase into the dominant language
- Write the translated meaning naturally in the dominant language's script
- Put the ORIGINAL spoken word(s) in brackets immediately after
- The entire output reads as natural dominant-language text, with originals preserved in brackets

FORMAT: translated_dominant_language_word (original spoken word AS SPOKEN — no translation in brackets)

BRACKET RULE — CRITICAL:
- Brackets contain ONLY the raw original word(s) the speaker actually said — in their ORIGINAL SCRIPT
- Do NOT romanize/transliterate the original word inside brackets
- Do NOT put translated meaning inside brackets
- Hindi spoken word → brackets show Hindi in Devanagari script (ठीक है), NOT romanized (theek hai)
- Telugu spoken word → brackets show Telugu in Telugu script (బాగుంది), NOT romanized (bagundi)
- English spoken word → brackets show English as-is (sacrifice), English is already its own script
- Brackets = exactly what came out of the speaker's mouth, in its NATIVE SCRIPT

━━━━━━━━━━━━━━━━━━━━
EXAMPLES when dominant = Telugu:
━━━━━━━━━━━━━━━━━━━━
  Speaker says Hindi "bahut acha"       → చాలా బాగుంది (बहुत अच्छा)        ✓ Hindi in Devanagari script in brackets
  Speaker says Hindi "theek hai"        → సరే (ठीक है)                      ✓ Hindi in Devanagari script in brackets
  Speaker says Hindi "kya baat hai"     → ఏమిటి విషయం (क्या बात है)         ✓ Hindi in Devanagari script in brackets
  Speaker says Hindi "bahut mushkil"    → చాలా కష్టం (बहुत मुश्किल)         ✓ Hindi in Devanagari script in brackets
  Speaker says Hindi "samajh gaye"      → అర్థమైంది (समझ गए)                ✓ Hindi in Devanagari script in brackets
  Speaker says English "super"          → అద్భుతంగా (super)                 ✓ English as-is in brackets
  Speaker says English "mind-blowing"   → అద్భుతంగా (mind-blowing)          ✓ English as-is in brackets
  Speaker says English "process"        → ప్రక్రియ (process)                ✓ English as-is in brackets
  Speaker says English "sacrifice"      → త్యాగం (sacrifice)                ✓ English as-is in brackets
  Speaker says English "expect"         → ఊహించు (expect)                   ✓ English as-is in brackets
  Speaker says English "last twist"     → చివరి మలుపు (last twist)          ✓ English as-is in brackets

  ✗ WRONG: సరే (theek hai)             — romanized Hindi in brackets, should be ठीक है
  ✗ WRONG: చాలా బాగుంది (very good)   — English translation in brackets, not original
  ✗ WRONG: అద్భుతంగా (అద్భుతంగా)     — repeating Telugu in brackets, not the original

━━━━━━━━━━━━━━━━━━━━
EXAMPLES when dominant = Hindi:
━━━━━━━━━━━━━━━━━━━━
  Speaker says Telugu "bagundi"      → अच्छा है (బాగుంది)          ✓ Telugu in Telugu script in brackets
  Speaker says Telugu "cheyyadam"    → करना है (చేయడం)             ✓ Telugu in Telugu script in brackets
  Speaker says Telugu "chala"        → बहुत (చాలా)                 ✓ Telugu in Telugu script in brackets
  Speaker says English "super"       → शानदार (super)              ✓ English as-is in brackets
  Speaker says English "process"     → प्रक्रिया (process)          ✓ English as-is in brackets
  Speaker says English "mind-blowing"→ अविश्वसनीय (mind-blowing)   ✓ English as-is in brackets
  Speaker says Hindi "theek hai"     → ठीक है                      ✓ already Hindi — no brackets needed

  ✗ WRONG: अच्छा है (bagundi)       — romanized Telugu in brackets, should be బాగుంది
  ✗ WRONG: शानदार (शानदार)          — repeating Hindi in brackets, not the original

━━━━━━━━━━━━━━━━━━━━
EXAMPLES when dominant = English:
━━━━━━━━━━━━━━━━━━━━
  Speaker says Telugu "bagundi"      → it's good (బాగుంది)         ✓ Telugu in Telugu script in brackets
  Speaker says Telugu "cheyyadam"    → to do (చేయడం)               ✓ Telugu in Telugu script in brackets
  Speaker says Hindi "theek hai"     → it's fine (ठीक है)           ✓ Hindi in Devanagari script in brackets
  Speaker says Hindi "bahut acha"    → very good (बहुत अच्छा)       ✓ Hindi in Devanagari script in brackets

  ✗ WRONG: it's fine (theek hai)    — romanized Hindi in brackets, should be ठीक है
  ✗ WRONG: it's good (bagundi)      — romanized Telugu in brackets, should be బాగుంది

KEY RULES:
- ALWAYS translate full MEANING into dominant language — ALL non-dominant languages including English get translated
- If dominant = Telugu: Hindi words → Telugu, English words → Telugu, both with originals in brackets
- If dominant = Hindi: Telugu words → Hindi, English words → Hindi, both with originals in brackets
- If dominant = English: Telugu words → English, Hindi words → English, both with originals in brackets
- NEVER keep a foreign word untranslated in the main text — always give the dominant language meaning
- NEVER mix scripts — ONE dominant language and script for all main text
- Brackets contain ONLY the original spoken word(s) in their NATIVE SCRIPT — Hindi spoken → ठीक है in brackets (NOT 'theek hai'); Telugu spoken → బాగుంది in brackets (NOT 'bagundi'); English spoken → sacrifice in brackets (English is already its own script); NEVER romanize, NEVER translate inside brackets
- Proper nouns, people's names, brand names, place names: keep as-is, no translation, no brackets needed
- Words already in the dominant language: write normally, no brackets
- Full sentence in non-dominant language: translate whole sentence naturally, put original sentence in brackets at end
- Goal: a native dominant-language reader reads fluently, while every original spoken word is still visible in brackets

NOISE REMOVAL RULES (remove ONLY these):
- Filler sounds: "um", "uh", "er", "hmm", "ah" (standalone, not part of a word)
- Repeated stutters: "I I I" => "I", "the the" => "the"
- Microphone clicks, coughs (not words)
- Silence gaps (just skip them)
- DO NOT remove: corrections ("actually no, I mean..."), emphasis repetitions ("very very important")

CONTENT EXTRACTION RULES:
- Extract EVERY point the speaker makes - zero omissions
- If speaker lists steps/tips, identify each one as a separate point
- Preserve speaker's exact phrasing - but render it in dominant script with brackets for non-dominant words
- If speaker repeats a point for emphasis, include it once

HTML OUTPUT FORMAT:
Return a COMPLETE, self-contained HTML5 document with embedded CSS.

The CSS to use inside <style>:
  body { font-family: Arial, sans-serif; font-size: 16px; color: #222; line-height: 1.7; max-width: 900px; margin: 0 auto; padding: 20px; }
  h1 { font-size: 26px; color: #1a237e; border-bottom: 3px solid #1a237e; padding-bottom: 10px; margin-bottom: 20px; }
  h2 { font-size: 20px; color: #283593; margin-top: 30px; margin-bottom: 10px; border-left: 4px solid #3949ab; padding-left: 10px; }
  h3 { font-size: 17px; color: #37474f; margin-top: 20px; }
  p { margin: 10px 0; }
  ul, ol { margin: 10px 0 10px 20px; }
  li { margin-bottom: 8px; }
  .section { background: #f5f7ff; border-radius: 6px; padding: 16px 20px; margin: 20px 0; }
  .lang-note { font-size: 13px; color: #757575; font-style: italic; }
  .key-point { border-left: 4px solid #43a047; padding: 8px 14px; background: #f1f8e9; margin: 12px 0; }
  .warning { border-left: 4px solid #e53935; padding: 8px 14px; background: #ffebee; margin: 12px 0; }
  .tip { border-left: 4px solid #fb8c00; padding: 8px 14px; background: #fff3e0; margin: 12px 0; }
  table { width: 100%; border-collapse: collapse; margin: 16px 0; }
  th { background: #1a237e; color: white; padding: 10px 14px; text-align: left; }
  td { padding: 8px 14px; border: 1px solid #ddd; }
  tr:nth-child(even) { background: #f5f5f5; }
  .transcript-meta { background: #e8eaf6; padding: 12px 16px; border-radius: 6px; font-size: 14px; margin-bottom: 24px; }

STRUCTURE:
- <h1> for the main topic (infer from content if not stated)
- <div class="transcript-meta"> with: Languages detected, Dominant language (script used for output), Total points covered
- DO NOT use <h2> or <h3> headings anywhere in the content body - NO section headings, NO sub-headings, NO topic labels
- Write ALL content as <p> paragraphs only - group naturally flowing sentences together in one paragraph
- Start a new <p> whenever the speaker shifts to a clearly new thought or point
- <ul> or <ol> ONLY if the speaker explicitly lists numbered/ordered steps out loud
- <div class="key-point"> for important takeaways (no heading inside, just the paragraph text)
- <div class="warning"> for any cautions/warnings the speaker mentions (no heading inside)
- <div class="tip"> for tips/advice (no heading inside)
- <table> if speaker compares items side by side
- <span class="lang-note">[unclear audio]</span> if something is unintelligible

STRICT RULES:
1. DO NOT hallucinate - only include what was actually spoken
2. DO NOT summarize or paraphrase - transcribe faithfully
3. DO NOT skip any point, step, tip, warning, or piece of advice
4. DO NOT add information not present in the audio
5. ALWAYS translate non-dominant words FULLY into the dominant language meaning and script — "theek hai" in Telugu-dominant output = సరే (theek hai), NOT థీక్ హై. Full meaning translation is required, not just script change
6. Non-dominant language words MUST appear as: dominant_language_translation (original in native script) — Hindi in brackets = Devanagari (ठीक है), Telugu in brackets = Telugu script (బాగుంది), English in brackets = English (sacrifice) — NEVER romanize inside brackets
7. Start output with <!DOCTYPE html> - no markdown fences, no extra text before it
8. Every section must be complete - do not truncate anything
9. ABSOLUTELY NO <h2> or <h3> tags anywhere in the output body - use <p> paragraphs only for all spoken content
10. DO NOT invent section label headings - just write the spoken words as paragraphs
11. The <h1> title must be written in the dominant language script

BEGIN TRANSCRIPTION AND STRUCTURING NOW.
"""


# ── 3. FUNCTIONS ───────────────────────────────────────────────────────────────

def upload_audio_file(file_path: str):
    """
    Upload audio/video file to Gemini File API.
    Required for files larger than a few KB (i.e., all real audio/video).

    Args:
        file_path: Path to audio/video file (mp3, mp4, wav, m4a, ogg, flac, etc.)

    Returns:
        Uploaded file object from Gemini File API
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # Determine MIME type from extension
    extension = path.suffix.lower()
    mime_map = {
        ".mp3":  "audio/mpeg",
        ".mp4":  "video/mp4",
        ".wav":  "audio/wav",
        ".m4a":  "audio/m4a",
        ".ogg":  "audio/ogg",
        ".flac": "audio/flac",
        ".aac":  "audio/aac",
        ".webm": "audio/webm",
        ".mkv":  "video/x-matroska",
        ".mov":  "video/quicktime",
        ".avi":  "video/avi",
    }
    mime_type = mime_map.get(extension, "audio/mpeg")

    file_size_mb = path.stat().st_size / 1024 / 1024
    print(f"  File: {path.name} ({file_size_mb:.2f} MB)")
    print(f"  MIME: {mime_type}")

    with open(file_path, "rb") as f:
        uploaded_file = client.files.upload(
            file=f,
            config=types.UploadFileConfig(
                mime_type=mime_type,
                display_name=path.name
            )
        )

    print(f"  Uploaded as: {uploaded_file.name}")
    return uploaded_file


def transcribe_and_structure(file_path: str) -> str:
    """
    Transcribe an audio/video file and return structured HTML output.

    Handles:
    - Any Indian language mix: Telugu, Hindi, English, or all three combined
    - Noise removal (fillers, stutters) without losing any content
    - Full content extraction - every point, step, tip, warning captured
    - Clean HTML5 output ready for TinyMCE

    Args:
        file_path: Path to the audio or video file

    Returns:
        str: Complete HTML document with structured transcript
    """
    print("\n" + "=" * 75)
    print("  VIKASPEDIA SPEECH-TO-HTML CONVERTER")
    print("=" * 75)
    print(f"  Input: {file_path}")

    # ── Step 1: Upload file to Gemini ─────────────────────────────────────────
    print("\n[STEP 1] Uploading audio to Gemini File API...")
    uploaded_file = upload_audio_file(file_path)
    print("  Upload complete.")

    # ── Step 2: Transcribe + structure with Gemini ────────────────────────────
    print("\n[STEP 2] Transcribing and structuring with Gemini 2.5 Flash...")
    print("  Please wait (30-120 seconds depending on audio length)...")

    # Retry up to 3 times in case of transient failures
    response = None
    last_error = None
    for attempt in range(1, 4):
        try:
            print(f"  Attempt {attempt}/3...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    TRANSCRIPTION_PROMPT,
                    uploaded_file
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=65536,
                )
            )
            # Check if we got a valid non-None text response
            got_text = (
                (hasattr(response, "text") and response.text is not None) or
                (hasattr(response, "candidates") and response.candidates and
                 any(
                     hasattr(p, "text") and p.text
                     for c in response.candidates
                     if hasattr(c, "content") and c.content
                     for p in c.content.parts
                 ))
            )
            if got_text:
                print(f"  Got valid response on attempt {attempt}.")
                break
            else:
                print(f"  Attempt {attempt}: empty response, retrying...")
                import time; time.sleep(5)
        except Exception as e:
            last_error = e
            print(f"  Attempt {attempt} failed: {e}")
            import time; time.sleep(5)

    if response is None:
        raise RuntimeError(f"All 3 attempts failed. Last error: {last_error}")

    # ── Step 3: Clean up the response ────────────────────────────────────────
    print("\n[STEP 3] Processing response...")

    # Safely extract text from response — handle None, blocked, or multi-part responses
    html_output = None

    # Try direct .text first
    if hasattr(response, "text") and response.text is not None:
        html_output = response.text.strip()

    # Fallback: extract from candidates/parts (Gemini sometimes returns this way)
    if not html_output and hasattr(response, "candidates") and response.candidates:
        for candidate in response.candidates:
            if hasattr(candidate, "content") and candidate.content:
                for part in candidate.content.parts:
                    if hasattr(part, "text") and part.text:
                        html_output = (html_output or "") + part.text
        if html_output:
            html_output = html_output.strip()

    # If still None, check finish reason and give helpful error
    if not html_output:
        finish_reason = None
        if hasattr(response, "candidates") and response.candidates:
            finish_reason = getattr(response.candidates[0], "finish_reason", None)
        print(f"  ERROR: Gemini returned empty response.")
        print(f"  Finish reason: {finish_reason}")
        print(f"  Full response object: {response}")
        raise ValueError(f"Gemini returned empty/blocked response. Finish reason: {finish_reason}")

    # Remove markdown code fences if Gemini wraps the output in them
    if html_output.startswith("```html"):
        html_output = html_output.replace("```html", "", 1)
        if html_output.endswith("```"):
            html_output = html_output[:-3]
        html_output = html_output.strip()
    elif html_output.startswith("```"):
        html_output = html_output.replace("```", "", 1)
        if html_output.endswith("```"):
            html_output = html_output[:-3]
        html_output = html_output.strip()

    # Safety fallback: if somehow we got non-HTML, wrap it
    if not html_output.lower().startswith("<!doctype") and not html_output.lower().startswith("<html"):
        print("  Warning: response missing DOCTYPE wrapper - applying fallback wrap")
        html_output = (
            "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
            "  <meta charset=\"UTF-8\">\n"
            "  <style>\n"
            "    body { font-family: Arial, sans-serif; font-size: 16px; color: #222; "
            "line-height: 1.7; max-width: 900px; margin: 0 auto; padding: 20px; }\n"
            "    h1 { font-size: 26px; color: #1a237e; }\n"
            "    h2 { font-size: 20px; color: #283593; }\n"
            "    ul, ol { margin: 10px 0 10px 20px; }\n"
            "    li { margin-bottom: 8px; }\n"
            "    .key-point { border-left: 4px solid #43a047; padding: 8px 14px; "
            "background: #f1f8e9; margin: 12px 0; }\n"
            "  </style>\n</head>\n<body>\n"
            + html_output
            + "\n</body>\n</html>"
        )

    print(f"  Output size: {len(html_output):,} characters")

    # ── Step 4: Clean up uploaded file from Gemini servers ───────────────────
    try:
        client.files.delete(name=uploaded_file.name)
        print("  Temporary file deleted from Gemini servers.")
    except Exception:
        pass  # Non-critical, skip silently

    print("\n  Transcription complete!")
    return html_output


def save_html_output(html_content: str, output_path: str) -> None:
    """
    Save HTML output to a file.

    Args:
        html_content: The full HTML string
        output_path: Destination file path (should end in .html)
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    size_kb = len(html_content.encode("utf-8")) / 1024
    print(f"  Saved: {Path(output_path).absolute()}  ({size_kb:.1f} KB)")


# ── 4. MAIN BLOCK ──────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # ── CONFIG: Set these before running ──────────────────────────────────────
    # Supported formats: .mp3 .mp4 .wav .m4a .ogg .flac .aac .webm .mkv .mov .avi
    AUDIO_FILE_PATH = r" path/to/your/audio_or_video_file.mp3"  # <-- UPDATE THIS with your file path

    # Where to save the HTML output
    OUTPUT_HTML_PATH = "transcript_output.html"
    # ─────────────────────────────────────────────────────────────────────────

    # Validate input file exists
    if not Path(AUDIO_FILE_PATH).exists():
        print(f"ERROR: File not found: {AUDIO_FILE_PATH}")
        sys.exit(1)

    try:
        # Run transcription pipeline
        result = transcribe_and_structure(AUDIO_FILE_PATH)

        print("\n" + "=" * 75)
        print("  COMPLETE")
        print("=" * 75)

        # Save HTML file
        save_html_output(result, OUTPUT_HTML_PATH)

        print(f"\n  HTML file ready: {Path(OUTPUT_HTML_PATH).absolute()}")
        print("  Open in browser to preview, or paste source into TinyMCE.")

        # Console preview (first 600 chars)
        print("\n" + "-" * 75)
        print("OUTPUT PREVIEW:")
        print("-" * 75)
        print(result[:600] + ("\n..." if len(result) > 600 else ""))

    except FileNotFoundError as e:
        print(f"\nFile Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)