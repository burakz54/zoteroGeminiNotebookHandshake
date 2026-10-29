# 📚 NotebookLM-to-Zotero Auto-Highlighter

Automatically highlight verified quotes and attach structured research annotations directly inside your local **Zotero PDF library** from **Google NotebookLM** outputs — with a single click on macOS.

![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![PyMuPDF](https://img.shields.io/badge/PDF_Engine-PyMuPDF-green)
![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC_BY--NC--SA_4.0-lightgrey.svg)

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

📖 Usage Workflow
Step 1: Set Up Google NotebookLM

Create a notebook in Google NotebookLM and upload the PDF sources from your Zotero library.

Open xx_NotebookLM Mastertext.txt, fill in your Document Title, Research Questions, and custom project context (and adjust any university-specific citation rules if needed, don't forget to upload them also!)

Paste the prompt into NotebookLM together with the draft paragraph/sentences you want to verify.

Step 2: Copy the Output
NotebookLM will generate a strictly formatted response looking like this:
### Abschnitt: Chapter 2 – Literature Review, Paragraph 1

#### **Satz 1:**
> „Your draft thesis sentence to be verified.“
* **Quelle 1:** `Author_2023_Paper.pdf` – Author (2023)
  * **Fundstelle:** S. 14, Abschnitt *3.2 Results*
  * **Markierungstext:** „Exact verbatim sentence directly from the PDF without omissions.“
  * **Einordnung:** Dimension: D1 | Cluster: K2 | Funktion: (a)
  * **Tag:** `[DOKUMENTANGABE]`
  * **Aussageart:** empirischer Befund
  * **Belegbezug:** Explains how this passage empirically supports Sentence 1.

-->Copy the entire NotebookLM output to your clipboard by clicking the copy button in the bottom (or with markdown and Cmd + C).

Step 3: Run the Auto-Highlighter
Keep zotero closed, Double-click start_highlighter.command in Finder or run the script from your terminal: python3 1_clipboard_highlighter.py
(be sure, that both files are in the same folder!)

Step 4: View Highlights in Zotero
Reopen the PDF tab in Zotero (or restart Zotero) to see your newly created highlights and structured notes!

⚙️ Configuration (zotero_config.json)
On its first run, the script automatically detects your Zotero storage directory and saves it to a local zotero_config.json file:
{
  "storage_path": "/Users/yourname/Zotero/storage"
}
If you ever move your Zotero data directory, simply delete zotero_config.json and run the script again.

🌍 Customizing for Other Languages
Currently, the parser keywords in 1_clipboard_highlighter.py match the German labels defined in xx_NotebookLM Mastertext.txt (Abschnitt:, Satz, Quelle, Fundstelle, Markierungstext:, Einordnung, Tag, Aussageart, Belegbezug).
Note that English quotes inside PDFs are already supported out of the box (Rule 9 in the Master Prompt instructs NotebookLM to keep Markierungstext: in the original document language). Feel free to translate this!

🤝 Contributing & License
Contributions, issues, and feature requests are welcome!



LICENSE
Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)

Copyright (c) 2026 [Dein Name]

You are free to:
- Share: copy and redistribute the material in any medium or format
- Adapt: remix, transform, and build upon the material

Under the following terms:
- Attribution (BY): You must give appropriate credit, provide a link to the license, and indicate if changes were made.
- NonCommercial (NC): You may not use the material for commercial purposes.
- ShareAlike (SA): If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

Full license text: https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode
