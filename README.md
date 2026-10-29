# 📚 NotebookLM-to-Zotero Auto-Highlighter

Automatically highlight verified quotes and attach structured research annotations directly inside your local **Zotero PDF library** from **Google NotebookLM** outputs — with a single click on macOS.

![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![PyMuPDF](https://img.shields.io/badge/PDF_Engine-PyMuPDF-green)
---

## ✨ Overview & Motivation

When writing an academic thesis or literature review, **Google NotebookLM** is an exceptional tool for verifying claims against your uploaded PDF sources. However, transferring those verified quotes, page numbers, and methodological notes back into **Zotero** by hand is tedious and error-prone.

**NotebookLM-to-Zotero Auto-Highlighter** bridges this gap:
1. You use the included **Master Prompt** in NotebookLM to verify your draft sentences against your literature corpus.
2. You copy NotebookLM's structured response to your macOS clipboard (`Cmd + C`).
3. You double-click the launcher script (or run the Python script).
4. The tool locates the exact passages in your local Zotero `storage` PDFs, highlights them, and attaches rich, structured annotations — while keeping your manual Zotero highlights completely safe.

---

## 🚀 Key Features

- **Zero-Config Zotero Path Discovery:** Automatically locates your local Zotero `storage` directory across 5 fallback stages:
  1. Cached `zotero_config.json`
  2. Zotero profile preferences (`prefs.js` -> `extensions.zotero.dataDir`)
  3. Standard macOS/Linux Zotero directories (`~/Zotero/storage`, etc.)
  4. Automated search for `zotero.sqlite` across local and cloud folders (with warnings for unloaded `.icloud` placeholder files)
  5. Interactive Drag & Drop terminal fallback
- **Smart PDF Quote Matching:**
  - Prioritizes the source PDF filename returned by NotebookLM before scanning the rest of your library.
  - Handles typographic variations (curly vs. straight quotes, em/en dashes, and line-break hyphenation via `TEXT_DEHYPHENATE`).
  - **Chunk-based Fallback Search:** If an exact full-sentence match fails due to PDF layout artifacts, the script falls back to 6-word chunk matching (requiring >= 70% chunk overlap for quotes with >= 8 words).
  - Automatically splits multi-part quotes separated by `[...]`, `(...)`, or ` / ` and strips inline footnote brackets.
- **Rich Zotero Annotations:** Every highlight includes a structured note tagged with author `NotebookLM`:
  - 📌 Section & Sentence ID (`Abschnitt` & `Satz`)
  - 📝 Verified Thesis Sentence (`Thesis-Satz`)
  - 📍 Exact Location (`Fundstelle`)
  - 🧭 Taxonomic Classification (`Einordnung`)
  - 🏷️ Epistemological Tag & Statement Type (`Methodik`)
  - 💡 Relevance to Thesis Claim (`Belegbezug`)
- **Non-Destructive & Idempotent Updates:**
  - 🔒 **Protects manual highlights:** Existing highlights created by you in Zotero are never overwritten or modified.
  - ✎ **Smart updates:** If you re-run the script with updated commentary from NotebookLM, existing `NotebookLM` notes are updated in place.
  - ↺ **Skips duplicates:** Identical existing highlights are left untouched.
  - Saves changes incrementally (`saveIncr()`) or via a safe atomic temporary file fallback.

---

## 📂 Repository Structure
├── 1_clipboard_highlighter.py     # Core Python script (clipboard parser & PDF highlighter)
├── start_highlighter.command      # macOS double-click launcher script
├── xx_NotebookLM Mastertext.txt   # Structured Master Prompt template for Google NotebookLM
├── requirements.txt               # Python dependencies (PyMuPDF)
├── LICENSE                        #  License
└── README.md                      # Project documentation (English)
