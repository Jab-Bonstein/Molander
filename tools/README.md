These are the scripts used to turn the handwriting sheet into the font. They are kept for reference; `sources/Molander.glyphs` is the master source that the font is built from.

- `seg.py` — isolates the ink on the photographed sheet and segments it into characters
- `build.py` / `extend.py` — normalises size and stroke weight, traces outlines, and builds accented and extra glyphs
- `finalize.py` — sets naming, licence and vertical metrics
