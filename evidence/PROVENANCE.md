# SEVEN: methods and provenance

This article separates a working application demonstration, an offline routing audit, a small local-answer study and whole-laptop power telemetry. They answer different questions. None establishes general model accuracy or local-versus-cloud energy savings.

## Versions and dates

| Evidence | Version boundary |
| --- | --- |
| Original project | Team SEVEN, 2025. Application commit `713203c0c59fe478a01c6c7ac9a24bb3d86e3bef`. |
| Original / plaintext study | November 12, 2026. Unchanged original local adapter, prompts and heuristics; cached backend falls back to plaintext formatting. |
| Template-exposed study | November 12, 2026. Same application source; backend's bundled Jinja template exposed through tokenizer configuration. |
| Revised-local-prompt study | November 12, 2026. Modified adapter/prompt/heuristic snapshot under `results/2026-11-12-restored/source`. This is earlier than the final interface/tool restoration. |
| Paired route audit | November 14, 2026. Original and restored classifier bytes saved in `results/router-2026-11-14`; SHA-256 in its summary. |
| Full-window demonstration | November 14, 2026, Toronto time; `20261115T032311Z` UTC. Restored working tree, not a committed release. Exact captured source hashes are in [report.json](demo/report.json). |

Original team roles follow the repository README: Jaundel—local adapter; Samin—cloud adapter; Yusuf—routing/prompts; Hamanpreet—energy estimates; Aadil—terminal interface. The terminal adapts Darren Burns' [Elia](https://github.com/darrenburns/elia); the source package retains its MIT licence and authorship.

## Full-window application evidence

[Manifest](demo/manifest.json) · [execution report](demo/report.json) · [captured code only](demo/source-snapshot.zip) · [source plus setup](demo/restored-source.zip) · [package hashes](demo/source-package.json)

The capture selects the uniquely titled, maximized Windows Terminal window using Windows Graphics Capture. Native dimensions are **1920 × 1140 pixels**, including its title bar; the taskbar is outside the window. The application observes **156 columns × 47 rows**. It runs in normal Textual application mode, with Pilot supplying input to the real application. It is not a browser reconstruction or a fixed small test viewport.

The recorder sends unchanged native frames to FFmpeg H.264 at 15 frames/s. Repeating the latest unchanged frame preserves elapsed waiting time; there are no cuts, crops, scaling, speed changes, composited labels or retouched replies. The continuous video is 67.533 seconds. PNG checkpoints are extracted from that same video at manifest times. The article scales media for display; opening an image gives the native file. Video compression is the only lossy visual transformation.

The walkthrough uses real local inference and live Open-Meteo, Coinbase, BBC and OpenAI requests, with isolated demonstration history. The original PROJECT SEVEN sign is retained. Incorrect or misleading generated text is also retained: for example, the local triangle explanation and cloud entanglement wording are not endorsed as factual explanations. This is functional evidence, not an answer-quality evaluation. The missing-key recovery check is `null` in this run because a key was configured; it is not counted as a pass.

The source-only ZIP is the immutable capture artifact. The combined ZIP adds allowlisted setup documents, package metadata, resolved installed dependencies and Elia's licence, collected during packaging. `source-package.json` lists the supplemental files and hashes every member. Neither archive includes keys, env files, personal chat history, model weights or runtime binaries. `package_source.py` builds the combined archive. Follow its `SETUP.md`; the Ryzen AI launcher expects an already-installed runtime. Other compatible local backends use the documented Python entry point.

Two unsuccessful capture approaches are excluded: a `TERM=dumb` session whose reported size was 80 × 25, and GDI capture of a GPU-composited window that returned black frames. The published files come only from the later native Windows Graphics Capture run.

## Initial routing decisions

Dataset: [Databricks Dolly-15k](https://huggingface.co/datasets/databricks/databricks-dolly-15k), all **15,011** records. Each prompt is the stripped instruction followed by two newlines and stripped context when context is present. No dataset reference response is included in a classifier prompt.

`compare_routes.py` executes each checkout's actual `classify_query_type` function in a separate process. It makes no model or provider request. It checks that the original counts reproduce the earlier audit, then saves all paired decisions, reasons, transitions and classifier source hashes.

| Classifier | Local | Live-data check | Cloud |
| --- | ---: | ---: | ---: |
| Original | 10,688 | 3,745 | 578 |
| Restored | 12,288 | 1,191 | 1,532 |

There are 2,556 changed decisions. This comparison includes the actual restoration changes, including word boundaries and removal of the standalone `price` keyword. It is not the earlier hypothetical whole-word-only variant. Figure 2 shows the actual substring versus word-boundary predicate for the same executed example; the adjacent table states changed transition counts. The original lexical audit separately identifies 2,510 API decisions where none of the matched real-time keywords occurs as a complete word. No ground-truth route labels are available; these counts do not establish routing accuracy, completed-request cost or energy savings.

## Local answers and latency

Model: [AMD Llama-3.2-1B-Instruct ONNX Ryzen AI 1.7 hybrid](https://huggingface.co/amd/Llama-3.2-1B-Instruct-onnx-ryzenai-1.7-hybrid), revision `4a814619e51faf20b93d1b14792d1c1d99586dbf`. Backend: Ryzen AI **1.7.0**, hybrid NPU+iGPU, on a Ryzen AI 7 350 Windows laptop. The endpoint's model alias can change from the revision string to `llama-model`; this is not a model-size comparison. Python 3.12 drives the application and experiments.

Dataset: [GSM8K test split](https://github.com/openai/grade-school-math), 1,319 rows. Python `random.Random(7).sample(range(len(dataset)), 60)` chooses 60 distinct row indices; all configurations use the same order. Each run warms the model, then forces every sampled question through local inference, regardless of its logged initial route. Temperature **0.7**, maximum **512 tokens**, one stochastic response per question, no retries to improve correctness. Reported latency is the adapter's elapsed time to a complete response, not time to first token.

The numeric grader extracts the final match of `-?\d[\d,]*(?:\.\d+)?` from the response, removes commas and compares its Decimal value with the dataset answer after `####`. It does not assess reasoning or units and can both miss a valid answer and accept accidental numeric agreement. “No match” is therefore the precise outcome label. Explicit uncertainty is a separate case-insensitive substring rule for `i don't know`, `i'm not sure`, `i not sure`, and `i cannot answer`, with an empty reply also flagged. It is not a calibrated confidence measure.

`analyse_study.py` validates dataset hashes, seeded row identities, question text, reference answers, predicted numbers, grades and uncertainty flags. Source bytes are checked against each run's recorded hashes. `data/answers.json` preserves the complete 180 responses for the separate supplement; it opens at the first sampled question, with no success-based selection. Figure 3 reproduces the complete original reply to that first question (test row 663). The reference arithmetic is editorial explanation, not a second model output. The caption identifies this as the original configuration, not the revised run. No statistical significance claim is used.

| Configuration | Numeric matches / 60 | Uncertainty triggers | No match, unflagged | Median response, s |
| --- | ---: | ---: | ---: | ---: |
| Original / plaintext | 11 | 8 | 41 | 5.831 |
| Template exposed | 13 | 0 | 47 | 8.168 |
| Revised local prompt | 22 | 0 | 38 | 6.523 |

The sequential runs differ in formatting, prompts, generated text and background activity. No repeated trials, randomized ordering or controlled causal comparison was performed. The last run does not benchmark the later final UI/tool working tree. Its strongest finding is that many non-matching answers do not trigger the uncertainty rule.

## Whole-laptop energy

`power_log.ps1` samples Windows `root\wmi:BatteryStatus`, recording Unix time, `PowerOnline`, `DischargeRate` in mW and remaining mWh at roughly 1 Hz. All retained samples have `PowerOnline=0`. Maximum observed sample gaps are 1.159, 1.134 and 1.096 seconds. Three blocks of 20 questions have timestamped start/end boundaries, with four approximately 30-second loaded-idle intervals around them.

`analyse_study.py` converts mW to W and milliseconds to seconds, interpolates power at interval boundaries, and applies the trapezoidal integral divided by 3,600 to obtain Wh. It requires complete telemetry coverage for each inference interval. Figure 5 shows every raw sample in the window from 20 seconds before through 20 seconds after the first original inference block. The 119.993-second block integrates to 0.7286752433 Wh. The complete three-run traces appear in the supplement. There is no smoothing or idle-baseline subtraction.

| Run | Inference-block duration, s | Whole-laptop block integral, Wh |
| --- | ---: | ---: |
| Original | 402.158 | 2.542565 |
| Template exposed | 511.690 | 2.424394 |
| Revised local prompt | 400.021 | 2.163257 |

These are battery-reported whole-device readings, including the display, OS, logger and other applications. They are not independently calibrated wall-plug readings, isolated accelerator energy, energy per correct answer, cloud energy or savings. The TUI's profile-based Wh estimates are separate assumptions and are never substituted for this telemetry.

## System architecture and configured comparison

The architecture revision uses three linked panels, preserving its wide composition on small screens with a full-size vector view. It executes the captured classifier on the first recorded France request; the four false predicates and local result are retained in `../data/system-trace.json`. Only the classifier's annotation-only model import is replaced while loading; function bodies are unchanged. The local detail expands the pretrained Llama model, using the pinned AMD `genai_config.json`: 16 decoder layers and hidden width 2,048. Its architecture fields were checked against the local runtime cache. Token positions are symbolic, not fabricated measured IDs. The repeated planes represent actual repeated layers. This is a schematic of a pretrained component, not a claim that SEVEN designed or trained it.

Figure 1 describes the restored capture source in `demo/source-snapshot.zip`, including the routing order, direct tool return, conditional escalation and SQLite metadata persistence. Figure 4 executes that archive's energy module, independently of the live working tree, and reproduces saved local and comparison estimates. `system_figures.py` checks source hashes against the capture report before building either figure. All three local cases are preserved in `../data/energy-comparison.json`; the first is used in the main article.

The 62-token estimator input is recovered from retained Wh and the configured coefficient, then checked against both saved outputs. It is not independently logged provider usage. Whiskers represent coefficient bounds in the code. The default cloud profile names GPT-4o, while the adapter uses GPT-4o-mini; its coefficients are a proxy, not a measured or calibrated comparison. Per-token coefficients take precedence over a stored 0.43 Wh/query value. Absent usage falls back to 500 tokens. Details, primary-paper context and all computed values are retained in the supplement. No new power or cloud measurement was performed for these figures.

## Rebuild and validate

From this article checkout:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r evidence\requirements.txt
.\.venv\Scripts\python.exe evidence\fetch_datasets.py
.\.venv\Scripts\python.exe evidence\analyse_study.py
.\.venv\Scripts\python.exe evidence\build_publication_figures.py --tectonic <path-to-tectonic>
.\.venv\Scripts\python.exe evidence\verify_article.py
.\.venv\Scripts\python.exe evidence\serve_preview.py
```

The public dataset downloads are byte-checked against SHA-256: GSM8K `3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14`; Dolly `2df9083338b4abd6bceb5635764dab5d833b393b55759dffb0959b6fcbf794ec`. A changed upstream file fails rather than silently replacing study inputs.

To repeat the classifier audit, obtain the pinned original checkout and extract the restored source package, then run `python evidence/compare_routes.py <original-checkout> <restored-checkout>` in the analysis environment. To collect new inference studies, use `measure_local.py` and the documented backend configuration; the script refuses to overwrite preserved response records. Re-running a stochastic model or current provider will not reproduce the recorded text byte-for-byte. There is no fresh-model requirement for validating the published evidence.

## Rights and figure production

Dolly data and derived text records retain [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/); GSM8K retains the repository's [MIT licence](https://github.com/openai/grade-school-math/blob/master/LICENSE). Poppins font files retain the SIL Open Font License in `fonts/OFL.txt`. The four unchanged Charter faces come from the existing portfolio; their embedded Bitstream notice and trademark acknowledgement are retained in `fonts/CHARTER-LICENSE.txt`. Elia retains its MIT licence within the source archive. Reference research pages and papers are linked and studied for communication choices; none of their images or quantitative results is presented as SEVEN evidence.

Terminal media are direct captures. The main article's five figures are authored TikZ/PGFPlots compositions produced by `build_publication_figures.py` from validated source records. Wide and mobile layouts preserve the same case, reply and battery interval. Tectonic compiles the PDFs; PyMuPDF exports SVG glyph paths and inspection PNGs. Editable `.tex` and the power CSV are retained in `figures/`; `publication-figures.json` pins input and output hashes. The supplementary complete power traces use Matplotlib. Legacy plot files remain in the checkout but the rejected matrix and alluvial flow are no longer linked from the article.

The shared colour/type definitions are in `figure-style.json`, which generates article CSS tokens and figure styles. The article retains Omni's real Charter prose and Poppins headings, captions, tables and figure labels. SVG glyphs are outlined; PDFs embed fonts and retain selectable text. AI assistance supported code, typesetting and writing, followed by source, arithmetic, rendering and interaction checks. No generative image tool was used, and no observed image or reply was repaired. This follows [HKUST Library's distinction](https://library.hkust.edu.hk/news-events/news/using-ai-create-scientific-figures-responsibly) between observations and reproducible data graphics. The [30-page figure audit](FIGURE_AUDIT.md) supersedes the earlier presentation review.
