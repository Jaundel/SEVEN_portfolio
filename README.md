# SEVEN portfolio article

An evidence-led account of Team SEVEN's local model, live-data tools and cloud fallback. The article uses a complete 1920 × 1140 application recording, paired decisions on 15,011 prompts, 180 preserved local responses and whole-laptop battery traces. Browser controls select recorded evidence; they do not run inference or accept an API key.

Preview from this directory with `python evidence/serve_preview.py`, then open http://127.0.0.1:8765/. This local server supports the byte-range requests needed for native video chapter seeking. A basic server that ignores ranges can play the video but clamp chapter jumps to zero.

Read [the supplement](supplement.html) for complete responses, measurement methods and downloads. [Methods and provenance](evidence/PROVENANCE.md) records source versions, dataset hashes, limitations and licences. The [30-page figure audit](evidence/FIGURE_AUDIT.md) informs the current presentation.

`evidence/analyse_study.py` validates all three preserved studies. `evidence/build_publication_figures.py` typesets all five main figures and the supplementary traces with TikZ/PGFPlots through Tectonic, then exports vector SVGs from the PDFs. `evidence/observation_plates.py` composes the observation figures using the system architecture's shared palette. Editable TeX and plotting CSV are retained in `evidence/figures`; `evidence/publication-figures.json` pins their source data and output hashes. Python dependencies are pinned in `evidence/requirements.txt`. Tectonic must be installed separately, or passed with `--tectonic PATH`. Run both scripts, then `python evidence/verify_article.py`.

The opening gallery silently plays the complete recording in a loop while visible. Eight view selectors seek to the retained checkpoint times; their active state follows playback. Pause/resume and native video controls remain available. Reduced-motion preferences disable automatic playback. Chapter selection does not splice, accelerate or alter the recording.

The restored application source and setup are packaged at `evidence/demo/restored-source.zip`. Its capture source is separate from the earlier November 12 local studies. Models, runtime binaries, credentials and personal chat history are excluded. Live outputs are historical records and contain unedited model errors.

The system architecture describes the captured application source. The energy comparison executes its archived estimator and reproduces saved values; it explicitly identifies the GPT-4o profile / GPT-4o-mini adapter mismatch. It is separate from the whole-laptop measurements.

Legacy browser-console files and pre-existing evidence remain in the checkout; `index.html`, `article.css` and `article.js` form the current article. GitHub Pages publishes the repository's main branch at https://jaundel.github.io/SEVEN_portfolio/ . Exact evidence bytes are preserved across platforms for manifest verification.
