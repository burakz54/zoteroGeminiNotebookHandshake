import os
import re
import sys
import json
import glob
import subprocess
from pathlib import Path
import fitz

# ==============================================================================
# ZOTERO AUTO-HIGHLIGHTER (Zwischenablage)
# Pfadsuche: 1) zotero_config.json  2) prefs.js (dataDir)  3) Standardpfade
#            4) Suche nach zotero.sqlite  5) Abfrage im Terminal (Drag & Drop)
# ==============================================================================

CONFIG_FILE = Path(__file__).parent / "zotero_config.json"
HOME = Path.home()
AUTHOR_TAG = "NotebookLM"
SCRIPT_MARKERS = ("📌", "[Satz")


# ------------------------------------------------------------------ Zotero-Pfad
def count_pdfs(p):
    try:
        return sum(1 for _ in p.rglob("*.pdf"))
    except Exception:
        return 0


def save_config(path):
    try:
        CONFIG_FILE.write_text(json.dumps({"storage_path": str(path)}), encoding="utf-8")
    except Exception:
        pass


def paths_from_prefs():
    out = []
    pats = [
        HOME / "Library/Application Support/Zotero/Profiles/*/prefs.js",
        HOME / "Library/Application Support/Zotero/Zotero/Profiles/*/prefs.js",
        HOME / ".zotero/zotero/*/prefs.js",
    ]
    for pat in pats:
        for f in glob.glob(str(pat)):
            try:
                txt = Path(f).read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for line in txt.split("\n"):
                if "extensions.zotero.dataDir" in line:
                    parts = line.split('"')
                    if len(parts) >= 4:
                        out.append(Path(parts[3]) / "storage")
    return out


def paths_from_sqlite_search():
    roots = [
        HOME,
        HOME / "Library/Mobile Documents/com~apple~CloudDocs",
        HOME / "Library/CloudStorage",
        HOME / "Documents",
        HOME / "Desktop",
    ]
    found = []
    for root in roots:
        if not root.exists():
            continue
        base = len(root.parts)
        try:
            for dp, dn, fn in os.walk(root):
                if len(Path(dp).parts) - base > 4:
                    dn[:] = []
                    continue
                dn[:] = [d for d in dn if not d.startswith(".") and d not in ("node_modules", "Applications")]
                if "zotero.sqlite" in fn:
                    found.append(Path(dp) / "storage")
        except Exception:
            continue
    return found


def get_zotero_storage_path():
    if CONFIG_FILE.exists():
        try:
            p = Path(json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("storage_path", ""))
            if p.exists() and count_pdfs(p) > 0:
                return p
        except Exception:
            pass

    standard = [
        HOME / "Zotero" / "storage",
        HOME / "Documents" / "Zotero" / "storage",
        HOME / "Library/Application Support/Zotero/storage",
    ]
    seen = set()
    for stage in (paths_from_prefs() + standard, None):
        if stage is None:
            print("Standardorte leer - suche nach zotero.sqlite ...")
            stage = paths_from_sqlite_search()
        for p in stage:
            if p in seen:
                continue
            seen.add(p)
            if p.exists():
                n = count_pdfs(p)
                if n > 0:
                    print(f"Zotero-Ordner erkannt: {p} ({n} PDFs)")
                    save_config(p)
                    return p
                try:
                    ic = list(p.rglob("*.icloud"))
                except Exception:
                    ic = []
                if ic:
                    print(f"⚠️ {p}: {len(ic)} PDFs sind nur iCloud-Platzhalter. Im Finder 'Jetzt laden' wählen!")

    print("\n" + "=" * 60)
    print("ZOTERO-STORAGE ORDNER NICHT GEFUNDEN")
    print("Ziehe den 'storage'-Ordner hierher ins Terminal und drücke ENTER:")
    print("=" * 60)
    raw = input("Pfad: ").strip().strip("'\"").replace("\\ ", " ")
    p = Path(raw)
    if not p.is_dir():
        print("Fehler: Pfad existiert nicht.")
        sys.exit(1)
    save_config(p)
    return p


# ------------------------------------------------------------------ Eingabe
def get_clipboard_text():
    try:
        return subprocess.run(["pbpaste"], capture_output=True).stdout.decode("utf-8")
    except Exception as e:
        print(f"Fehler Zwischenablage: {e}")
        return ""


QUOTE_CHARS = "„“\"”«»"
LB, RB, LP, RP = (re.escape(c) for c in "[]()")
ELLIPSIS_SPLIT = (LB + "[ ]*(?:[.][.][.]|…)[ ]*" + RB + "|"
                  + LP + "[ ]*(?:[.][.][.]|…)[ ]*" + RP + "| / ")
FOOTNOTE_RE = LB + "[0-9, –-]+" + RB


def clean(s):
    return " ".join(s.replace("**", "").replace("`", "").split()).strip()


def strip_outer_quotes(s):
    s = s.strip()
    while s and s[0] in QUOTE_CHARS:
        s = s[1:]
    while s and s[-1] in QUOTE_CHARS:
        s = s[:-1]
    return " ".join(s.split())


def clean_footnotes(s):
    s = re.sub(FOOTNOTE_RE, "", s)
    return " ".join(s.split())


def split_segments(raw):
    parts = re.split(ELLIPSIS_SPLIT, raw)
    segs = []
    for p in parts:
        c = clean_footnotes(strip_outer_quotes(p))
        if len(c.split()) >= 3:
            segs.append(c)
    return segs


def field(line, label):
    marker = label + ":**"
    if marker in line:
        return clean(line.split(marker, 1)[1])
    return None


def parse_notebooklm_output(text):
    items = []
    section, sentence, thesis, current_file = "", "Satz", "", None
    meta = {}
    for line in text.split("\n"):
        s = line.strip()

        if s.startswith("#"):
            head = s.lstrip("#").strip()
            if head.startswith("Abschnitt:"):
                section = clean(head.split(":", 1)[1])
            m = re.search("(Satz[ ]+[0-9]+)", head, re.I)
            if m:
                sentence = m.group(1)
                thesis = ""

        if s.startswith(">"):
            thesis = strip_outer_quotes(clean(s.lstrip("> ")))

        if s.startswith(("*", "-")) and "**Quelle" in s:
            meta = {"section": section, "sentence": sentence, "thesis": thesis}
            fm = re.search("`([^`]+[.]pdf)`", s, re.I)
            current_file = fm.group(1).strip() if fm else None

        for key, label in (("fundstelle", "Fundstelle"), ("einordnung", "Einordnung"),
                           ("tag", "Tag"), ("aussageart", "Aussageart"),
                           ("belegbezug", "Belegbezug")):
            v = field(s, label)
            if v is not None:
                meta[key] = v

        if "Markierungstext:" in s and not s.startswith(">"):
            raw = s.split("Markierungstext:", 1)[1].replace("**", "").strip()
            for seg in split_segments(raw):
                items.append({"sentence": sentence, "hint_file": current_file,
                              "segment": seg, "meta": meta})
    return items


def build_comment(it):
    m = it["meta"]
    return (
        f"📌 ZOTERO-BELEG FÜR: {m.get('section', '')} | {m.get('sentence', '')}\n"
        f"📝 Thesis-Satz: „{m.get('thesis', '')}“\n"
        f"📍 Fundstelle: {m.get('fundstelle', '')}\n"
        f"🧭 Einordnung: {m.get('einordnung', '')}\n"
        f"🏷️ Methodik: {m.get('tag', '')} | {m.get('aussageart', '')}\n"
        f"💡 Belegbezug: {m.get('belegbezug', '')}"
    )


# ------------------------------------------------------------------ PDF-Suche
FLAGS = fitz.TEXT_DEHYPHENATE if hasattr(fitz, "TEXT_DEHYPHENATE") else 0


def variants(seg):
    v = [seg]
    straight = (seg.replace("“", '"').replace("”", '"').replace("„", '"')
                   .replace("’", "'").replace("‘", "'"))
    curly = seg.replace('"', "”").replace("'", "’")
    dash = seg.replace("—", "-").replace("–", "-")
    for x in (straight, curly, dash):
        if x not in v:
            v.append(x)
    return v


def find_segment(page, seg):
    for v in variants(seg):
        rects = page.search_for(v, flags=FLAGS)
        if rects:
            return rects, "voll"
    words = seg.split()
    if len(words) >= 8:
        rects_all, hits, size = [], 0, 6
        chunks = [" ".join(words[i:i + size]) for i in range(0, len(words), size)]
        for ch in chunks:
            for v in variants(ch):
                r = page.search_for(v, flags=FLAGS)
                if r:
                    rects_all += r[:1]
                    hits += 1
                    break
        if hits >= max(2, int(len(chunks) * 0.7)):
            return rects_all, "teilweise"
    return [], ""


def existing_highlights(page):
    return [a for a in (page.annots() or []) if a.type[0] == 8]


def is_script_note(annot):
    info = annot.info
    content = (info.get("content") or "").strip()
    return (info.get("title") == AUTHOR_TAG) or content.startswith(SCRIPT_MARKERS) or content == ""


def norm(s):
    return re.sub("[^a-z0-9]", "", s.lower())


def save_doc(doc, pdf):
    """Inkrementell speichern; Fallback: kurze temporaere Datei im selben Ordner.
    Wirft eine Exception, wenn beides scheitert. Gibt True zurueck, wenn doc noch offen ist."""
    try:
        doc.saveIncr()
        return True
    except Exception:
        pass
    tmp = pdf.parent / "_hl_tmp.pdf"
    doc.save(str(tmp), garbage=1, deflate=True)
    doc.close()
    os.replace(str(tmp), str(pdf))
    return False


# ------------------------------------------------------------------ Hauptlogik
def highlight_in_zotero(items, storage):
    pdfs = list(storage.rglob("*.pdf"))
    print(f"Zotero-Pfad: {storage}\n{len(pdfs)} PDFs gefunden.\n", flush=True)
    stats = {"neu": 0, "aktualisiert": 0, "unveraendert": 0, "geschuetzt": 0,
             "fehlt": 0, "fehler": 0}
    errors = {}

    for n, it in enumerate(items, 1):
        seg, hint = it["segment"], it["hint_file"]
        print(f"[{n}/{len(items)}] Suche {it['sentence']}: {seg[:50]}...", flush=True)
        new_comment = build_comment(it)
        hint_n = norm(Path(hint).stem) if hint else ""
        ordered = sorted(pdfs, key=lambda p: 0 if hint_n and hint_n[:15] in norm(p.name) else 1)
        done = False

        for pdf in ordered:
            try:
                doc = fitz.open(pdf)
            except Exception as e:
                errors[pdf.name] = str(e)
                continue

            log = []
            local = {"neu": 0, "aktualisiert": 0, "unveraendert": 0, "geschuetzt": 0}
            modified = False
            failed = None
            try:
                for page in doc:
                    rects, mode = find_segment(page, seg)
                    if not rects:
                        continue
                    done = True
                    pg = f"S.{page.number + 1}/{mode}"
                    existing = existing_highlights(page)

                    to_create, to_update, protected, same = [], {}, set(), set()
                    for r in rects:
                        hit = [a for a in existing if a.rect.intersects(r)]
                        if not hit:
                            to_create.append(r)
                            continue
                        for a in hit:
                            if not is_script_note(a):
                                protected.add(a.xref)
                            elif (a.info.get("content") or "").strip() == new_comment.strip():
                                same.add(a.xref)
                            else:
                                to_update[a.xref] = a

                    if to_create:
                        annot = page.add_highlight_annot(to_create)
                        annot.set_info(title=AUTHOR_TAG, content=new_comment)
                        annot.update()
                        modified = True
                        local["neu"] += 1
                        log.append(f"   ✓ Neu markiert ({it['sentence']}, {pg})")

                    for a in to_update.values():
                        old = (a.info.get("content") or "").strip().replace("\n", " | ")
                        a.set_info(title=AUTHOR_TAG, content=new_comment)
                        a.update()
                        modified = True
                        local["aktualisiert"] += 1
                        log.append(f"   ✎ Notiz aktualisiert ({it['sentence']}, {pg})\n"
                                   f"        alt: {old[:110]}\n"
                                   f"        neu: {new_comment.splitlines()[0][:110]}")

                    if same and not to_create and not to_update:
                        local["unveraendert"] += 1
                        log.append(f"   ↺ Unverändert ({it['sentence']}, {pg})")
                    if protected and not to_create and not to_update and not same:
                        local["geschuetzt"] += 1
                        log.append(f"   🔒 Eigene Markierung, nicht verändert ({it['sentence']}, {pg})")

                if modified:
                    try:
                        still_open = save_doc(doc, pdf)
                        if still_open:
                            doc.close()
                    except Exception as e:
                        failed = str(e)
                        if not doc.is_closed:
                            doc.close()
                elif not doc.is_closed:
                    doc.close()
            except Exception as e:
                failed = str(e)
                errors[pdf.name] = str(e)
                if not doc.is_closed:
                    doc.close()

            if done:
                if failed:
                    stats["fehler"] += 1
                    print(f"   ✗ Speichern fehlgeschlagen: {failed}")
                    print(f"        Datei: {pdf}", flush=True)
                else:
                    for k, v in local.items():
                        stats[k] += v
                    for l in log:
                        print(l)
                    print(f"        Datei: {pdf}", flush=True)
                break

        if not done:
            stats["fehlt"] += 1
            print("   ✗ Nicht gefunden", flush=True)

    print("\n" + "=" * 50)
    print(f"Ergebnis von {len(items)} Segmenten:")
    print(f"  neu markiert:        {stats['neu']}")
    print(f"  Notiz aktualisiert:  {stats['aktualisiert']}")
    print(f"  unverändert:         {stats['unveraendert']}")
    print(f"  geschützt (eigene):  {stats['geschuetzt']}")
    print(f"  nicht gefunden:      {stats['fehlt']}")
    print(f"  Speicherfehler:      {stats['fehler']}")
    if errors:
        print("Dateien mit Fehlern (z. B. iCloud/gesperrt):")
        for k, v in list(errors.items())[:10]:
            print(f"  - {k}: {v}")
    print("=" * 50)
    print("Hinweis: Zotero beenden oder den Reader-Tab neu öffnen, damit Änderungen sichtbar werden.")


if __name__ == "__main__":
    content = get_clipboard_text()
    if not content:
        print("⚠️ Die Zwischenablage ist leer.")
        sys.exit(1)
    parsed = parse_notebooklm_output(content)
    if not parsed:
        print("⚠️ Keine 'Markierungstext:'-Zitate in der Zwischenablage gefunden.")
        sys.exit(1)
    print(f"{len(parsed)} Zitat-Segmente extrahiert.", flush=True)
    highlight_in_zotero(parsed, get_zotero_storage_path())

