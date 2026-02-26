# Voice-to-Value: Speech-to-Structure Content Pipeline
### Project Report

> Transforming raw voice dictation into publication-ready multilingual HTML articles — automatically.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Background & Problem Statement](#2-project-background--problem-statement)
3. [System Architecture](#3-system-architecture)
4. [Multilingual Handling — The Bracket System](#4-multilingual-handling--the-bracket-system)
5. [Known Limitations](#5-known-limitations)
6. [Performance](#6-performance)
7. [Pipeline Comparison](#7-pipeline-comparison)
8. [Installation & Setup](#8-installation--setup)
9. [Output & Results](#9-output--results)
10. [Conclusion](#10-conclusion)

---

## 1. Executive Summary

This report documents the design, implementation, and performance of the Voice-to-Value Content Pipeline — an AI-driven system built to eliminate the biggest bottleneck in multilingual content production: Subject Matter Experts (SMEs) who have brilliant insights but no time to write.

The pipeline takes a raw, unstructured voice recording — full of filler words, non-linear thinking, and code-switching between Telugu, Hindi, and English — and automatically produces a clean, structured, CMS-ready HTML article. The goal is for a developer's rambling 5-minute brain dump to become a polished, localized technical guide requiring less than 5 minutes of human editing.

> **Core Mission — "Speech-to-Structure":** Not just transcription. The pipeline extracts the thesis, reorganises the logic into a coherent outline, and rewrites the content to match a professional publishing standard before it reaches any translation layer.

Two independent pipelines were built and tested:

- **`geminisot.py`** — Powered by Google Gemini 2.5 Flash. A single-step multimodal pipeline with no audio duration limit.
- **`sarvamsot.py`** — Powered by Sarvam AI's `saaras:v3` (STT) and `sarvam-m` (structuring). A two-step pipeline optimised for Indian regional languages, tested on audio clips up to 30 seconds.

---

## 2. Project Background & Problem Statement

### 2.1 The Problem

Content teams working with domain experts face a universal challenge: the people with the most knowledge are the least likely to write. SMEs — developers, doctors, agronomists, government officers — carry vast knowledge in their heads but have neither the time nor the inclination to sit and write structured articles.

The result is one of three bad outcomes:

- Content never gets created because experts are unavailable.
- Interviews are conducted and transcribed manually — a slow, expensive process.
- Ghostwriters are used, but they lack the domain depth and introduce inaccuracies.

For a platform like Vikaspedia that publishes content in multiple Indian languages, the problem compounds further: confusion written in English gets translated into multiple languages, spreading inaccurate or poorly structured content at scale.

### 2.2 The Solution Approach

The Voice-to-Value pipeline inverts this workflow. Instead of asking experts to write, we ask them to speak — a far lower barrier. A developer records a 5-minute voice note on their phone. The pipeline handles everything else:

- **Transcription** of multilingual speech (Telugu + Hindi + English code-switching).
- **Noise removal** — filler sounds, stutters, and silence are stripped automatically.
- **Language detection** — the dominant language is identified and the entire output is rendered in its native script.
- **Mixed-language formatting** — non-dominant words are translated into the dominant language, with the original spoken word preserved in brackets in its native script (Devanagari for Hindi, Telugu script for Telugu).
- **Structural transformation** — raw monologue becomes a document with headings, paragraphs, bullet points, and callout boxes.
- **HTML output** — the final article is a complete, self-contained HTML5 file ready to paste into TinyMCE or any CMS.

> **The "Golden Source" Principle:** The pipeline ensures the dominant-language draft is structurally sound and culturally neutral before it hits any translation layer — preventing us from translating confusion into other languages.

---

## 3. System Architecture

### 3.1 Pipeline A — `geminisot.py` (Gemini 2.5 Flash)

This is a **single-step multimodal pipeline**. The audio file is uploaded directly to the Gemini Files API, and a single richly-engineered prompt handles the entire chain — transcription, language detection, translation, noise removal, and HTML structuring — all in one model call.

#### Workflow

```
[Audio / Video File]
         │
         ▼
[Upload to Gemini Files API]
         │
         ▼
[Gemini 2.5 Flash — Single Prompt]
    ├── Detects dominant language (Telugu / Hindi / English / Tamil / etc.)
    ├── Transcribes every spoken word
    ├── Removes filler words and stutters
    ├── Translates non-dominant words into dominant language
    ├── Preserves original words in native script inside brackets
    └── Outputs a complete, styled HTML5 document
         │
         ▼
[transcript_output.html] — Ready for TinyMCE / CMS
```

#### Step-by-Step

1. **File Upload** — The audio or video file is uploaded to Gemini's Files API. Supported formats: `.mp3`, `.mp4`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.aac`, `.webm`, `.mkv`, `.mov`, `.avi`.
2. **Single Model Call** — A detailed system prompt instructs Gemini 2.5 Flash to perform dominant language detection, full transcription, noise removal, mixed-language translation with bracket formatting, and HTML generation in one inference pass.
3. **Response Processing** — The raw output is cleaned of markdown fences, validated for proper HTML structure, and a safety fallback DOCTYPE wrapper is applied if needed.
4. **Cleanup** — The temporary file is deleted from Gemini's servers after the response is received.
5. **Output** — A complete, styled HTML5 document is written to disk.

> No duration limit. No chunking. No stitching. The entire audio is processed as one coherent unit, preserving full context from start to finish.

#### Retry Logic

The model call is wrapped in a 3-attempt retry loop with a 5-second backoff between attempts. If all three attempts return an empty or blocked response, the pipeline raises a descriptive `RuntimeError` with the finish reason from the Gemini API.

---

### 3.2 Pipeline B — `sarvamsot.py` (Sarvam AI)

This is a **two-step pipeline** that deliberately separates the Speech-to-Text (STT) task from the content structuring task, using two different Sarvam AI models for each.

#### Workflow

```
[Audio File — up to 30 seconds]
         │
         ▼
[Step 1A — Sarvam saaras:v3 (translate endpoint)]
    └── Detects dominant language → BCP-47 code (e.g. te-IN, hi-IN)
         │
         ▼
[Step 1B — Sarvam saaras:v3 (transcribe endpoint)]
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

#### Step-by-Step

1. **Language Detection** — Audio is sent to Sarvam's `translate` endpoint (`saaras:v3`) to detect the dominant spoken language.
2. **Transcription** — The same audio is sent to Sarvam's `transcribe` endpoint (`saaras:v3`) in `transcribe` mode (not `translate`) to preserve the original multilingual text. `language_code` is set to `"unknown"` to enable automatic multi-language detection.
3. **Structuring** — The raw transcript is sent to `sarvam-m` with a detailed system prompt covering dominant language detection, bracket formatting, and HTML generation.
4. **Output** — A complete, styled HTML5 document is written to disk.

#### Retry Logic

Each step has its own independent 3-attempt retry loop — a 3-second backoff for the STT step and a 5-second backoff for the structuring step.

---

## 4. Multilingual Handling — The Bracket System

One of the most technically demanding aspects of the pipeline is handling **code-switching** — the common Indian phenomenon of speakers fluidly mixing Telugu, Hindi, and English mid-sentence.

### 4.1 Dominant Language Detection

Both pipelines perform dominant language detection before producing any output:

1. Analyse the first 3–5 sentences — the opening language carries strong priority.
2. Count total words and sentences per language across the full audio.
3. The language that wins on both signals (or the stronger one) becomes the **Dominant Language**.
4. All output is written exclusively in the dominant language's native script.

Examples:
- Telugu 70% + Hindi 20% + English 10% → **Telugu** → entire output in తెలుగు script
- Hindi 60% + English 30% + Telugu 10% → **Hindi** → entire output in हिंदी script
- English 80% + Telugu 20% → **English** → entire output in English

### 4.2 The Bracket Rule

Every non-dominant word is handled as follows:

- The **meaning** is translated into the dominant language and written naturally in the dominant script.
- The **original spoken word** is placed in brackets immediately after, written in its own native script — never romanized, never translated inside the brackets.

**Examples when Dominant = Telugu:**

| Speaker says | Output |
|---|---|
| Hindi "bahut acha" | చాలా బాగుంది (बहुत अच्छा) |
| Hindi "theek hai" | సరే (ठीक है) |
| English "sacrifice" | త్యాగం (sacrifice) |
| English "process" | ప్రక్రియ (process) |

**Examples when Dominant = English:**

| Speaker says | Output |
|---|---|
| Telugu "bagundi" | it's good (బాగుంది) |
| Hindi "theek hai" | it's fine (ठीक है) |
| Hindi "bahut acha" | very good (बहुत अच्छा) |

> **Result:** A native dominant-language reader reads the article fluently, while every original spoken word remains visible in brackets for reference, context, and translation verification.

### 4.3 Noise Removal

**Removed automatically:**
- Filler sounds: `um`, `uh`, `er`, `hmm`, `ah` (standalone)
- Repeated stutters: `I I I mean` → `I mean`
- Microphone clicks, coughs, silence gaps

**Deliberately preserved:**
- Corrections: `"actually no, I mean..."` — these are meaningful content
- Emphasis repetitions: `"very very important"` — the speaker intends the repetition

---

## 5. Known Limitations

### 5.1 Sarvam AI — 30-Second Audio Limit

> ⚠️ **IMPORTANT:** Sarvam AI's `saaras:v3` STT API enforces a hard limit of **30 seconds of audio per request** on the current free/standard tier.

This pipeline has been tested on 30-second audio clips and delivers strong, accurate results within this constraint. However, for real-world SME voice notes that are typically 3–10 minutes long, this is a significant limitation.

**Options for working around the 30-second limit:**

**Option 1 — Upgrade your Sarvam AI plan:** Higher tiers may support longer audio durations. Refer to [Sarvam AI's pricing](https://www.sarvam.ai) for the latest limits.

**Option 2 — Manually split audio into 30-second clips:** Technically possible, but **NOT recommended** because:

- Sentences and thoughts are cut mid-flow at every boundary, destroying natural context.
- Each segment is structured independently — the resulting HTML pieces do not connect narratively.
- Manual stitching of multiple HTML outputs requires human editing, which defeats the automation goal.
- Overall coherence and accuracy of the final article will be lower than processing as a single unit.

> **Recommendation:** For audio longer than 30 seconds, use `geminisot.py` (Gemini Pipeline) instead. It processes the entire file in a single pass with no duration limit and no loss of context.

### 5.2 General Limitations

- Very poor audio quality (heavy background noise, overlapping speakers) will reduce transcription accuracy on both pipelines.
- Both pipelines require a working internet connection and valid API keys.
- For extremely rare accents or highly technical jargon, occasional misrecognition may occur — human review in under 5 minutes handles these cases.
- API keys are currently hardcoded in the scripts. For production use, move these to environment variables.

---

## 6. Performance

| Metric | Gemini Pipeline | Sarvam Pipeline |
|---|---|---|
| Transcription Accuracy | Very High | High (within 30s limit) |
| Code-Switching Handling | Excellent (native multilingual) | Good (India-tuned) |
| Output HTML Quality | Publication-ready | Publication-ready |
| Filler Word Removal | Automatic (in-prompt) | Automatic (in-prompt) |
| Error Handling | Robust (3-retry + fallback) | Robust (3-retry per step) |
| Avg. Processing Time | 15–60 sec (5 min audio) | 30–90 sec (30 sec clip) |
| Long Audio (>30s) | ✅ Fully supported | ❌ Not supported on free tier |

### 6.1 Gemini Pipeline Performance

The Gemini 2.5 Flash pipeline handles the full Speech-to-Structure workflow in a single inference pass. For a 5-minute audio file, end-to-end processing (including upload) typically completes in 15 to 60 seconds depending on server load and file size. The output HTML is immediately publication-ready with headings, body paragraphs, bullet lists, and colour-coded callout boxes. Multilingual code-switching is handled natively with very high accuracy across Telugu, Hindi, English, and Tamil.

### 6.2 Sarvam Pipeline Performance

The Sarvam AI pipeline is purpose-built for Indian regional languages and performs with strong accuracy — particularly for Telugu and Hindi. For audio clips up to 30 seconds, end-to-end processing (STT + structuring) completes in approximately 30 to 90 seconds. Results within the 30-second limit are clean and well-structured.

### 6.3 Success Metric

> Both pipelines meet the core success metric: a rambling voice note from a developer or SME can be automatically transformed into a crisp, structured, localized HTML article requiring **less than 5 minutes of human editing.**

---

## 7. Pipeline Comparison

| Feature | `geminisot.py` (Gemini) | `sarvamsot.py` (Sarvam) |
|---|---|---|
| AI Model (STT) | Gemini 2.5 Flash (multimodal) | Sarvam saaras:v3 |
| AI Model (Structure) | Gemini 2.5 Flash (same call) | Sarvam sarvam-m (chat) |
| Pipeline Steps | Single-step | Two-step (STT → Structure) |
| Audio Duration Limit | No limit | 30 seconds per request |
| Language Detection | Automatic (multimodal) | Automatic (translate endpoint) |
| Languages Supported | Telugu, Hindi, English, Tamil, and more | Hindi, Telugu, English (India-optimised) |
| Avg. Processing Time | 15–60 sec (5 min audio) | 30–90 sec (30 sec clip) |
| Output Format | Styled HTML5 | Styled HTML5 |
| Retry Logic | 3 attempts | 3 attempts per step |
| Best For | Long-form, multilingual, high accuracy | Short clips, India-first STT |

### When to Use Each Pipeline

**Use `geminisot.py` when:**
- The audio is longer than 30 seconds (real developer voice notes of 3–10 minutes).
- You need the highest possible multilingual accuracy, especially for complex code-switching.
- You want a single-step, lowest-latency pipeline.
- The audio includes Tamil or other Indian languages beyond Hindi and Telugu.

**Use `sarvamsot.py` when:**
- The audio is 30 seconds or shorter.
- You want an India-first STT model tuned specifically for regional accents.
- You prefer a two-step architecture where STT and structuring are independently tunable.

---

## 8. Installation & Setup

### Requirements

- Python 3.9 or higher (Python 3.14 recommended per `pyproject.toml`)
- A valid Google Gemini API key (for `geminisot.py`)
- A valid Sarvam AI API subscription key (for `sarvamsot.py`)
- Internet connection (both pipelines call external APIs)

### Install — Gemini Pipeline

```bash
pip install google-genai
```

### Install — Sarvam Pipeline

```bash
pip install sarvamai
```

### Install — Full Project (using uv)

```bash
uv sync
```

This installs all dependencies declared in `pyproject.toml`: `google-genai`, `sarvamai`, `pydub`, `scikit-learn`, and `nltk`.

### Running the Pipelines

Edit the `AUDIO_FILE_PATH` variable inside the script to point to your audio file, then run:

```bash
python geminisot.py    # Gemini pipeline → saves transcript_output.html
python sarvamsot.py    # Sarvam pipeline → saves transcript_output_sarvam.html
```

---

## 9. Output & Results

Both pipelines produce complete, self-contained HTML5 documents that can be directly pasted into any TinyMCE editor or CMS without further formatting. Each output includes:

- A document title (`h1`) extracted from the content.
- A metadata banner showing detected languages, dominant language, and content summary.
- Structured sections with `h2` and `h3` subheadings.
- Body paragraphs in clean, natural prose.
- Bullet and numbered lists where the speaker enumerates points.
- Green callout boxes (`.key-point`) for important statements.
- Professional embedded CSS — fonts, colours, spacing, and responsive layout.

> **To see real examples of the pipeline output, open the sample files included in this repository:**
> - `transcript_output.html` — Generated by `geminisot.py` (Gemini pipeline)
> - `transcript_output_sarvam.html` — Generated by `sarvamsot.py` (Sarvam pipeline)
>
> Open either file in any browser for a full preview, or paste the HTML source directly into your CMS editor.

The Gemini pipeline was tested on an English-language historical audio recording (*People and Personalities of Chhatarpur District*) and produced a fully structured multi-section HTML article covering four distinct personalities — each with their own biographical section, correct paragraph flow, and contextual detail — with no hallucinations and no omissions.

---

## 10. Conclusion

The Voice-to-Value pipeline successfully solves the identified content bottleneck. By combining multimodal AI (Gemini) and India-first STT (Sarvam AI) with carefully engineered prompt chains, the system delivers on its core promise: a rambling voice note becomes a publication-ready HTML article in under 90 seconds, requiring less than 5 minutes of human editing.

The two-pipeline approach gives the content team flexibility — Gemini for long-form, complex multilingual audio with no constraints, and Sarvam for short, India-first clips where regional accuracy matters most.

The bracket-based mixed-language formatting system is a standout feature: it makes the output readable to native speakers of the dominant language while preserving every original spoken word in its native script — a capability that is critical for a multilingual platform like Vikaspedia where translation accuracy and cultural authenticity are non-negotiable.

> **The pipeline is production-ready for short to medium audio clips.** For full deployment at scale, the recommended next step is moving API keys to environment variables and integrating the HTML output directly into the CMS upload workflow.

---

*Prepared for: Vikaspedia Content Team | Version: 1.0 | Technology: Google Gemini 2.5 Flash + Sarvam AI*