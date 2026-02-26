"""
Vikaspedia Speech-to-HTML Converter (Sarvam AI Edition)
=========================================================
Transcribes audio/video files with multilingual support (Telugu, Hindi, English mixes)
Outputs clean, structured HTML suitable for TinyMCE editor
No hallucinations. No noise. No missing lines.
Models: Sarvam AI saaras:v3 (STT) + sarvam-m (Chat/Structuring)
"""

# ── 1. IMPORTS & CLIENT SETUP ──────────────────────────────────────────────────

import os
import sys
import time
from pathlib import Path
from sarvamai import SarvamAI

# ── CLIENT SETUP ──────────────────────────────────────────────────────────────
SARVAM_API_KEY = "YOUR_API_KEY_HERE" # <-- UPDATE THIS with your Sarvam API key
client = SarvamAI(api_subscription_key=SARVAM_API_KEY)


# ── 2. PROMPTS ─────────────────────────────────────────────────────────────────

STRUCTURING_SYSTEM_PROMPT = """
You are an EXPERT multilingual speech transcription and content structuring system 
specialized in Indian languages - Telugu, Hindi, English, and any mix of these.

YOUR JOB:
You will receive a raw transcript of spoken audio. Your task is to:
1. Structure EVERY point from the transcript - do NOT skip or summarize any part
2. Detect the DOMINANT language and write ALL output in that language's script
3. Remove ONLY non-content noise: filler sounds (um, uh, hmm), repeated stutters (I I I mean => I mean)
4. Preserve ALL meaningful content - every instruction, every point, every sentence
5. Structure the content logically using proper HTML

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOMINANT LANGUAGE DETECTION (do this FIRST before writing anything):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1 - Read the FIRST 3-5 sentences: whatever language/script is used there gives strong priority.
Step 2 - Count overall: which language occupies the MOST words/sentences across the full transcript?
Step 3 - The language that wins by BOTH signals (or the stronger one) = DOMINANT LANGUAGE.
Step 4 - Write the ENTIRE output in that dominant language's native script.

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
  Speaker says Hindi "bahut acha"       → చాలా బాగుంది (बहुत अच्छा)        ✓ Hindi in Devanagari in brackets
  Speaker says Hindi "theek hai"        → సరే (ठीक है)                      ✓ Hindi in Devanagari in brackets
  Speaker says Hindi "kya baat hai"     → ఏమిటి విషయం (क्या बात है)         ✓ Hindi in Devanagari in brackets
  Speaker says Hindi "bahut mushkil"    → చాలా కష్టం (बहुत मुश्किल)         ✓ Hindi in Devanagari in brackets
  Speaker says Hindi "samajh gaye"      → అర్థమైంది (समझ गए)                ✓ Hindi in Devanagari in brackets
  Speaker says English "super"          → అద్భుతంగా (super)                 ✓ English as-is in brackets
  Speaker says English "mind-blowing"   → అద్భుతంగా (mind-blowing)          ✓ English as-is in brackets
  Speaker says English "process"        → ప్రక్రియ (process)                ✓ English as-is in brackets
  Speaker says English "sacrifice"      → త్యాగం (sacrifice)                ✓ English as-is in brackets
  Speaker says English "expect"         → ఊహించు (expect)                   ✓ English as-is in brackets

  ✗ WRONG: సరే (theek hai)             — romanized Hindi in brackets, should be ठीक है
  ✗ WRONG: చాలా బాగుంది (very good)   — English translation in brackets, not original
  ✗ WRONG: అద్భుతంగా (అద్భుతంగా)     — repeating Telugu in brackets, not the original

━━━━━━━━━━━━━━━━━━━━
EXAMPLES when dominant = Hindi:
━━━━━━━━━━━━━━━━━━━━
  Speaker says Telugu "bagundi"         → अच्छा है (బాగుంది)                ✓ Telugu script in brackets
  Speaker says Telugu "cheyyadam"       → करना है (చేయడం)                   ✓ Telugu script in brackets
  Speaker says Telugu "chala"           → बहुत (చాలా)                       ✓ Telugu script in brackets
  Speaker says English "super"          → शानदार (super)                    ✓ English as-is in brackets
  Speaker says English "process"        → प्रक्रिया (process)               ✓ English as-is in brackets
  Speaker says English "mind-blowing"   → अविश्वसनीय (mind-blowing)         ✓ English as-is in brackets
  Speaker says Hindi "theek hai"        → ठीक है                            ✓ already Hindi — no brackets needed

  ✗ WRONG: अच्छा है (bagundi)          — romanized Telugu in brackets, should be బాగుంది
  ✗ WRONG: शानदार (शानदार)             — repeating Hindi, not the original

━━━━━━━━━━━━━━━━━━━━
EXAMPLES when dominant = English:
━━━━━━━━━━━━━━━━━━━━
  Speaker says Telugu "bagundi"         → it's good (బాగుంది)               ✓ Telugu script in brackets
  Speaker says Telugu "cheyyadam"       → to do (చేయడం)                     ✓ Telugu script in brackets
  Speaker says Hindi "theek hai"        → it's fine (ठीक है)                ✓ Hindi Devanagari in brackets
  Speaker says Hindi "bahut acha"       → very good (बहुत अच्छा)            ✓ Hindi Devanagari in brackets

  ✗ WRONG: it's fine (theek hai)       — romanized Hindi in brackets, should be ठीक है
  ✗ WRONG: it's good (bagundi)         — romanized Telugu in brackets, should be బాగుంది

KEY RULES:
- ALWAYS translate full MEANING into dominant language — ALL non-dominant languages including English get translated
- If dominant = Telugu: Hindi words → Telugu, English words → Telugu, both with originals in brackets
- If dominant = Hindi: Telugu words → Hindi, English words → Hindi, both with originals in brackets
- If dominant = English: Telugu words → English, Hindi words → English, both with originals in brackets
- NEVER keep a foreign word untranslated in the main text — always give the dominant language meaning
- NEVER mix scripts — ONE dominant language and script for all main text
- Brackets contain ONLY the original spoken word(s) in their NATIVE SCRIPT — NEVER romanize inside brackets
- Proper nouns, people's names, brand names, place names: keep as-is, no translation, no brackets needed
- Words already in the dominant language: write normally, no brackets
- Full sentence in non-dominant language: translate whole sentence naturally, put original in brackets at end
- Goal: a native dominant-language reader reads fluently, while every original spoken word is visible in brackets

NOISE REMOVAL RULES (remove ONLY these):
- Filler sounds: "um", "uh", "er", "hmm", "ah" (standalone, not part of a word)
- Repeated stutters: "I I I" => "I", "the the" => "the"
- Microphone clicks, coughs (not words)
- Silence gaps (just skip them)
- DO NOT remove: corrections ("actually no, I mean..."), emphasis repetitions ("very very important")

CONTENT EXTRACTION RULES:
- Extract EVERY point the speaker makes - zero omissions
- If speaker lists steps/tips, identify each one as a separate point
- Preserve speaker's exact phrasing - but render in dominant script with brackets for non-dominant words
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
1. DO NOT hallucinate - only include what is in the transcript
2. DO NOT summarize or paraphrase - use the speaker's actual content
3. DO NOT skip any point, step, tip, warning, or piece of advice
4. DO NOT add information not present in the transcript
5. ALWAYS translate non-dominant words FULLY into the dominant language meaning and script
6. Non-dominant language words MUST appear as: dominant_language_translation (original in native script)
   — Hindi in brackets = Devanagari (ठीक है), Telugu in brackets = Telugu script (బాగుంది),
   — English in brackets = English (sacrifice) — NEVER romanize inside brackets
7. Start output with <!DOCTYPE html> - no markdown fences, no extra text before it
8. Every section must be complete - do not truncate anything
9. ABSOLUTELY NO <h2> or <h3> tags anywhere in the content body - use <p> paragraphs only
10. DO NOT invent section label headings - just write the spoken words as paragraphs
11. The <h1> title must be written in the dominant language script
"""


# ── 3. HELPER: SPLIT AUDIO FOR LONG FILES ─────────────────────────────────────

def split_audio_if_needed(file_path: str, max_size_mb: int = 20) -> list:
    """
    Sarvam STT works best with files under 20MB.
    Splits into 5-minute chunks using pydub if needed.
    Returns a list of file paths to process (original or chunks).
    """
    path = Path(file_path)
    size_mb = path.stat().st_size / 1024 / 1024

    if size_mb <= max_size_mb:
        return [file_path]

    print(f"  File is {size_mb:.1f} MB — splitting into 5-minute chunks...")

    try:
        from pydub import AudioSegment

        ext = path.suffix.lower().lstrip(".")
        audio = AudioSegment.from_file(file_path, format=ext)

        chunk_ms = 5 * 60 * 1000
        chunks = []
        for i, start in enumerate(range(0, len(audio), chunk_ms)):
            chunk = audio[start:start + chunk_ms]
            chunk_path = str(path.parent / f"_chunk_{i:03d}_{path.stem}.mp3")
            chunk.export(chunk_path, format="mp3")
            chunks.append(chunk_path)
            print(f"  Created chunk {i+1}: {Path(chunk_path).name}")

        return chunks

    except ImportError:
        print("  Warning: pydub not installed — sending full file.")
        print("  Install with: pip install pydub")
        return [file_path]
    except Exception as e:
        print(f"  Warning: Could not split audio ({e}) — sending full file.")
        return [file_path]


# ── 4. STEP 1: SPEECH TO TEXT ─────────────────────────────────────────────────

def transcribe_audio(file_path: str) -> str:
    """
    Transcribe audio using Sarvam AI saaras:v3 in transcribe mode.
    Uses 'transcribe' mode (NOT 'translate') to preserve original languages
    so the structuring model can detect the dominant language correctly.

    Args:
        file_path: Path to audio file (.mp3 or .wav recommended)

    Returns:
        str: Raw multilingual transcript text
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    file_size_mb = path.stat().st_size / 1024 / 1024
    print(f"  File: {path.name} ({file_size_mb:.2f} MB)")

    chunks = split_audio_if_needed(file_path)
    all_transcripts = []

    for i, chunk_path in enumerate(chunks):
        chunk_label = f"chunk {i+1}/{len(chunks)}" if len(chunks) > 1 else "file"
        print(f"  Transcribing {chunk_label}: {Path(chunk_path).name}")

        # Retry up to 3 times per chunk
        transcript = None
        detected_lang = "unknown"
        last_error = None

        for attempt in range(1, 4):
            try:
                # Step A: detect dominant language using translate endpoint
                try:
                    with open(chunk_path, "rb") as af:
                        lang_response = client.speech_to_text.translate(
                            file=af,
                            model="saaras:v3"
                        )
                    if isinstance(lang_response, dict):
                        detected_lang = lang_response.get("language_code") or lang_response.get("language") or "unknown"
                    elif hasattr(lang_response, "language_code"):
                        detected_lang = lang_response.language_code or "unknown"
                    elif hasattr(lang_response, "language"):
                        detected_lang = lang_response.language or "unknown"
                    print(f"    Detected language: {detected_lang}")
                except Exception as lang_err:
                    print(f"    Language detection skipped: {lang_err}")
                    detected_lang = "unknown"

                # Step B: transcribe keeping original multilingual text
                with open(chunk_path, "rb") as audio_file:
                    response = client.speech_to_text.transcribe(
                        file=audio_file,
                        language_code="unknown",  # Auto-detect, keep original languages
                        model="saaras:v3",
                        mode="transcribe"         # Keep original — NOT translate
                    )

                # Safely extract transcript text (Sarvam returns dict)
                if isinstance(response, dict):
                    transcript = response.get("transcript", "")
                elif hasattr(response, "transcript"):
                    transcript = response.transcript or ""
                else:
                    transcript = ""

                if not transcript:
                    raise ValueError(f"Empty transcript in response: {response}")

                print(f"    ✓ Got {len(transcript)} chars (attempt {attempt})")
                break

            except Exception as e:
                last_error = e
                print(f"    Attempt {attempt}/3 failed: {e}")
                if attempt < 3:
                    time.sleep(3)

        if transcript:
            all_transcripts.append(transcript)
        else:
            print(f"  ✗ Failed to transcribe {chunk_label} after 3 attempts: {last_error}")

        # Clean up temp chunk files (not the original)
        if chunk_path != file_path and Path(chunk_path).exists():
            try:
                os.remove(chunk_path)
            except Exception:
                pass

    if not all_transcripts:
        raise ValueError("All chunks failed to transcribe. Check audio quality and API key.")

    full_transcript = "\n\n".join(all_transcripts)
    print(f"  Total transcript length: {len(full_transcript)} characters")
    return full_transcript, detected_lang


# ── 5. STEP 2: STRUCTURE TRANSCRIPT INTO HTML ─────────────────────────────────

def structure_transcript_to_html(transcript: str, detected_lang: str = "unknown") -> str:
    """
    Send raw transcript to Sarvam sarvam-m for HTML structuring.
    Applies dominant language detection + full translation with bracket formatting.

    Args:
        transcript: Raw multilingual transcript from STT
        detected_lang: BCP-47 language code detected by Sarvam (e.g. "te-IN", "hi-IN")

    Returns:
        str: Complete HTML5 document
    """
    print("  Sending transcript to sarvam-m for structuring...")
    print("  Please wait (15-60 seconds)...")

    lang_hint = f"\n\nNote: Sarvam AI detected the dominant spoken language as: {detected_lang}" if detected_lang != "unknown" else ""

    user_message = f"""Here is the raw transcript from an audio file.
Please structure it into a complete, well-formatted HTML document following your instructions exactly.{lang_hint}

RAW TRANSCRIPT:
{transcript}

Return ONLY the HTML document starting with <!DOCTYPE html>. No markdown. No extra text before or after."""

    # Retry up to 3 times
    html_output = None
    last_error = None

    for attempt in range(1, 4):
        try:
            print(f"  Attempt {attempt}/3...")
            response = client.chat.completions(
                messages=[
                    {"role": "system", "content": STRUCTURING_SYSTEM_PROMPT},
                    {"role": "user",   "content": user_message}
                ],
                temperature=0.1,
                max_tokens=8000
            )

            # Safely extract content
            if (response and
                hasattr(response, "choices") and
                response.choices and
                hasattr(response.choices[0], "message") and
                response.choices[0].message and
                hasattr(response.choices[0].message, "content") and
                response.choices[0].message.content):

                html_output = response.choices[0].message.content.strip()
                if html_output:
                    print(f"  ✓ Got response on attempt {attempt}")
                    break
                else:
                    raise ValueError("Response content is empty string")
            else:
                raise ValueError(f"Unexpected response structure: {response}")

        except Exception as e:
            last_error = e
            print(f"  Attempt {attempt} failed: {e}")
            if attempt < 3:
                time.sleep(5)

    if not html_output:
        raise RuntimeError(f"All 3 structuring attempts failed. Last error: {last_error}")

    # ── Clean markdown fences if model wraps in them ──────────────────────────
    if html_output.startswith("```html"):
        html_output = html_output[7:]
        if html_output.endswith("```"):
            html_output = html_output[:-3]
        html_output = html_output.strip()
    elif html_output.startswith("```"):
        html_output = html_output[3:]
        if html_output.endswith("```"):
            html_output = html_output[:-3]
        html_output = html_output.strip()

    # ── Safety fallback if DOCTYPE missing ───────────────────────────────────
    if not html_output.lower().startswith("<!doctype") and not html_output.lower().startswith("<html"):
        print("  Warning: response missing DOCTYPE — applying fallback wrapper")
        html_output = (
            "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
            "  <meta charset=\"UTF-8\">\n"
            "  <style>\n"
            "    body { font-family: Arial, sans-serif; font-size: 16px; color: #222; "
            "line-height: 1.7; max-width: 900px; margin: 0 auto; padding: 20px; }\n"
            "    h1 { font-size: 26px; color: #1a237e; }\n"
            "    p { margin: 10px 0; }\n"
            "    ul, ol { margin: 10px 0 10px 20px; }\n"
            "    li { margin-bottom: 8px; }\n"
            "    .key-point { border-left: 4px solid #43a047; padding: 8px 14px; "
            "background: #f1f8e9; margin: 12px 0; }\n"
            "    .transcript-meta { background: #e8eaf6; padding: 12px 16px; "
            "border-radius: 6px; font-size: 14px; margin-bottom: 24px; }\n"
            "  </style>\n</head>\n<body>\n"
            + html_output
            + "\n</body>\n</html>"
        )

    print(f"  HTML output size: {len(html_output):,} characters")
    return html_output


# ── 6. MAIN PIPELINE ──────────────────────────────────────────────────────────

def transcribe_and_structure(file_path: str) -> str:
    """
    Full pipeline: Audio file → STT transcript → Structured HTML.

    Args:
        file_path: Path to the audio or video file

    Returns:
        str: Complete HTML document with structured transcript
    """
    print("\n" + "=" * 75)
    print("  VIKASPEDIA SPEECH-TO-HTML CONVERTER  (Sarvam AI)")
    print("=" * 75)
    print(f"  Input: {file_path}")

    # ── Step 1: Transcribe ────────────────────────────────────────────────────
    print("\n[STEP 1] Transcribing audio with Sarvam saaras:v3...")
    transcript, detected_lang = transcribe_audio(file_path)

    if not transcript.strip():
        raise ValueError("Transcription returned empty — check audio quality or file format.")

    print(f"\n  Dominant language detected: {detected_lang}")
    print("\n  --- Transcript Preview (first 400 chars) ---")
    print(transcript[:400] + ("..." if len(transcript) > 400 else ""))
    print("  ---")

    # ── Step 2: Structure into HTML ───────────────────────────────────────────
    print("\n[STEP 2] Structuring transcript with Sarvam sarvam-m...")
    html_output = structure_transcript_to_html(transcript, detected_lang)

    print("\n  Pipeline complete!")
    return html_output


# ── 7. SAVE OUTPUT ────────────────────────────────────────────────────────────

def save_html_output(html_content: str, output_path: str) -> None:
    """Save HTML output to a file."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    size_kb = len(html_content.encode("utf-8")) / 1024
    print(f"  Saved: {Path(output_path).absolute()}  ({size_kb:.1f} KB)")


# ── 8. MAIN BLOCK ─────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # ── CONFIG: Set these before running ──────────────────────────────────────
    # Supported formats: .mp3, .wav (mp3 and wav work best with Sarvam)
    AUDIO_FILE_PATH = r"path/to/your/audio_or_video_file.mp3"  # <-- UPDATE THIS with your file path

    # Where to save the HTML output
    OUTPUT_HTML_PATH = "transcript_output_sarvam.html"
    # ─────────────────────────────────────────────────────────────────────────

    if not Path(AUDIO_FILE_PATH).exists():
        print(f"ERROR: File not found: {AUDIO_FILE_PATH}")
        print("  Please update AUDIO_FILE_PATH in the script.")
        sys.exit(1)

    try:
        result = transcribe_and_structure(AUDIO_FILE_PATH)

        print("\n" + "=" * 75)
        print("  COMPLETE")
        print("=" * 75)

        save_html_output(result, OUTPUT_HTML_PATH)

        print(f"\n  HTML file ready: {Path(OUTPUT_HTML_PATH).absolute()}")
        print("  Open in browser to preview, or paste source into TinyMCE.")

        print("\n" + "-" * 75)
        print("OUTPUT PREVIEW:")
        print("-" * 75)
        print(result[:600] + ("\n..." if len(result) > 600 else ""))

    except FileNotFoundError as e:
        print(f"\nFile Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\nTranscription Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\nStructuring Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)