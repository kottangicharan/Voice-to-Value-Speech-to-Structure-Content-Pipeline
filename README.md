# 🎙️ Voice-to-Value: Speech-to-Structure Content Pipeline

> **Transform raw voice dictation into polished, publication-ready multilingual HTML articles — automatically.**

This project solves the biggest bottleneck in content strategy: Subject Matter Experts (SMEs) who have brilliant insights but zero time to write. Instead of typing, they simply speak — and the pipeline does the rest. A messy 5-minute audio brain dump, full of filler words, code-switching, and non-linear thoughts, becomes a clean, structured, CMS-ready HTML document with zero manual reformatting.

---

## 🧩 What's Inside

The project ships **two independent pipelines** that achieve the same goal through different AI stacks:

| File | Engine | Best For |
|---|---|---|
| `geminisot.py` | Google Gemini 2.5 Flash | Long-form audio (no duration limit), high accuracy, deep multilingual understanding |
| `sarvamsot.py` | Sarvam AI saaras:v3 + sarvam-m | India-first STT with a dedicated Indian language model for structuring |

---

## ⚙️ How to Install

Make sure you have **Python 3.9+** installed, then install the required packages:

### For `geminisot.py` (Gemini Pipeline)

```bash
pip install google-genai
```

### For `sarvamsot.py` (Sarvam Pipeline)

```bash
pip install sarvamai
```

If you are using `uv` (as configured in this project):

```bash
uv sync
```

---

## 🔄 Workflow: How Each Pipeline Works

### Pipeline 1 — `geminisot.py` (Gemini)

This is a **single-step pipeline**. The entire intelligence — transcription, language detection, translation, and HTML structuring — lives in one powerful multimodal model call.

```
[Audio/Video File]
        │
        ▼
[Upload to Gemini Files API]
        │
        ▼
[Gemini 2.5 Flash — Single Prompt]
   ├── Detects dominant language (Telugu / Hindi / English / etc.)
   ├── Transcribes every spoken word
   ├── Removes only filler words and stutters
   ├── Translates non-dominant words into the dominant language
   ├── Preserves original words in native script inside brackets
   └── Outputs a complete, styled HTML5 document
        │
        ▼
[transcript_output.html] — Ready for TinyMCE / CMS
```

**Supported formats:** `.mp3`, `.mp4`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.aac`, `.webm`, `.mkv`, `.mov`, `.avi`

---

### Pipeline 2 — `sarvamsot.py` (Sarvam)

This is a **two-step pipeline** that separates transcription from structuring.

```
[Audio File — up to 30 seconds]
        │
        ▼
[Step 1 — Sarvam saaras:v3 STT]
   ├── Detects dominant language (via translate endpoint)
   └── Transcribes audio in original multilingual text
        │
        ▼
[Raw Multilingual Transcript]
        │
        ▼
[Step 2 — Sarvam sarvam-m Chat Model]
   ├── Applies dominant language detection
   ├── Translates non-dominant words into dominant language
   ├── Preserves originals in native script inside brackets
   └── Outputs a complete, styled HTML5 document
        │
        ▼
[transcript_output_sarvam.html] — Ready for TinyMCE / CMS
```

---

## ⚠️ Limitation of `sarvamsot.py` — 30-Second Audio Cap

> **Important:** Sarvam AI's `saaras:v3` Speech-to-Text API has a **hard limit of 30 seconds per audio request** on the current free/standard tier.

This pipeline has been tested with 30-second audio clips and performs well within that limit — transcription is accurate and the structured HTML output is clean and publication-ready.

**For audio longer than 30 seconds, you have two options:**

1. **Upgrade your Sarvam AI plan** — higher tiers may support longer audio durations. Check [Sarvam AI's pricing](https://www.sarvam.ai) for the latest limits.

2. **Manually split your audio into 30-second clips** and run each through the pipeline separately — however, this approach is **not recommended** because:
   - It breaks the natural flow of speech mid-sentence, causing context loss at the boundaries.
   - Each segment is structured independently, so the final HTML pieces won't connect smoothly.
   - Stitching multiple outputs together requires manual editing, which defeats the purpose of the pipeline.
   - Overall accuracy and coherence of the output will likely be lower.

**Recommendation:** For audio longer than 30 seconds, use `geminisot.py` (Gemini pipeline) instead — it has **no duration limit** and processes the entire file in a single pass with no loss of context.

---

## 📊 Performance

### `geminisot.py` — Gemini Pipeline

- **Accuracy:** Very high. Gemini 2.5 Flash natively handles multilingual Indian speech including code-switching (mid-sentence language switches between Telugu, Hindi, and English).
- **Speed:** Typically 15–60 seconds for a 5-minute audio file depending on file size and server load.
- **Output quality:** The HTML output is publication-ready, with correct headings, bullet points, key-point callout boxes, and professional styling embedded in the file.
- **Language coverage:** Telugu, Hindi, English, Tamil, and most other Indian languages. Mixed-language audio is handled in a single pass.
- **Reliability:** Built-in 3-attempt retry logic. Handles Gemini's occasional empty response gracefully.

### `sarvamsot.py` — Sarvam Pipeline

- **Accuracy:** Good for Hindi and Telugu-dominant audio within the 30-second limit. Sarvam's `saaras:v3` is purpose-built for Indian languages and performs well on regional accents.
- **Speed:** Two-step process. STT takes 5–20 seconds, structuring takes another 15–60 seconds. Total for a 30-second clip: ~30–90 seconds.
- **Output quality:** Comparable HTML output with the same multilingual bracket formatting. Quality depends on the raw STT transcript quality, which can vary with audio noise.
- **Limitation:** Hard capped at 30 seconds of audio per request on the current tier. Tested and verified to work well within this limit.
- **Reliability:** Built-in 3-attempt retry logic on both the STT and structuring steps.

### General Success Metric

Both pipelines are designed to meet the core goal: **take a rambling voice note and produce a clean, localized HTML article requiring less than 5 minutes of human editing.**

---

## 📁 Output

The pipeline generates structured HTML files that can be directly pasted into any TinyMCE editor or CMS. To see real examples of what the output looks like, check the uploaded output files included in this repository:

- **`transcript_output.html`** — Output generated by the Gemini pipeline (`geminisot.py`)
- **`transcript_output_sarvam.html`** — Output generated by the Sarvam pipeline (`sarvamsot.py`)

Open these files in any browser to preview the formatted result, or paste the HTML source directly into your CMS editor.

---

## 🔑 API Keys

Before running, set your API keys in the respective script files:

- `geminisot.py` → Set `GEMINI_API_KEY`
- `sarvamsot.py` → Set `SARVAM_API_KEY`

---

## 🚀 Quick Start

```bash
# Gemini Pipeline
python geminisot.py
# Edit AUDIO_FILE_PATH inside the script to point to your audio file

# Sarvam Pipeline
python sarvamsot.py
# Edit AUDIO_FILE_PATH inside the script to point to your audio file
```

Output HTML files will be saved in the same directory as the script.