# Article and figure fonts

Poppins regular, medium, semibold and italic are from Google Fonts' `ofl/poppins` family, under the SIL Open Font License in `OFL.txt`. The article, Matplotlib labels and PDF exports use these same TTF files.

The four Charter WOFF2 files are copied unchanged from the existing portfolio's `assets/fonts/Charter` directory. Their embedded Bitstream copyright notice is preserved and reproduced in `CHARTER-LICENSE.txt`. BITSTREAM CHARTER is a registered trademark of Bitstream Inc.

`evidence/figure-style.json` defines type roles, palette and font faces. Running `analyse_study.py` generates both `article-tokens.css` and the figures from that source. `figure-manifest.json` hashes the font files and exports. SVG glyphs are outlined for stable rendering; PDF fonts are embedded as TrueType. Live article text remains accessible HTML.
