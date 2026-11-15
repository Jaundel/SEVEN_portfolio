# SEVEN figure audit

Reviewed 15 November 2026. This supersedes the visual recommendations in `REFERENCE_REVIEW.md`.

## Finding

SEVEN's current presentation exposes its evidence archive before explaining its findings. The route cards repeat category names; the square matrix encodes arbitrary question order; the answer browser makes readers inspect a test harness. Matching fonts, producing valid vectors and retaining source records did not resolve those communication problems.

The references organise figures around an observable output, an actual mechanism, a controlled comparison or a measured relationship. Their visual detail carries information: the things connected by arrows are real operations, the images are actual inputs or outputs, and the colours identify a stable role. That is the standard SEVEN should meet.

## Scope and inspection

The audit covers **30 distinct public pages**: all 14 project articles linked from the representative-project and selected-publication sections of [Shikun's current project index](https://shikun.io/projects), his Clarity guide, eight selected project pages from the named graphics researchers, four David Ha/otoro articles, and three Jonathan Chang articles. The latter two groups extend the previously identified references; they are not a claim to cover those authors' entire publication histories. Jonathan here is [jonathanc.net](https://jonathanc.net/).

I inspected page text, captions, media references and rendered figure sections; collected two browser views per page and additional detail views; checked the linked Prismer plotting source and MTAN's inline SVG; and compared SEVEN's current local rendering. Omni's local article was read as a separate layout and evidence reference. Reference captures are inspection material, not SEVEN results or assets for publication.

Selected Kaleido, CamP, Rays as Pixels, Saber and vMAP media were still buffering or unrendered in the captured views. Their declared comparisons, other figures and source structure were inspectable; those screenshots do not prove complete playback. This audit does not reproduce the reference papers' experiments or infer undocumented authoring tools from appearance. The page/source inventory and hashes are in `figure-audit.json`.

## How the figures are actually made

- **Shikun's stated plot workflow:** Python/Matplotlib prototypes, conversion with tikzplotlib, then refinement of the final TikZ. Clarity separately names Poppins and Charter for its public template. [Clarity, Fundamentals and Data Plots](https://shikun.io/projects/clarity).
- **Direct source evidence:** the public `vqav2.tex` example linked there contains PGFPlots axes, numeric tables, explicit RGB colours, individually positioned model labels and a positioned comparison arrow. The composition is authored, rather than left to a plotting default. This establishes the example's construction, not the provenance of every figure on his site.
- **Diagram authoring evidence:** MTAN's two inline architecture SVGs carry “Produced by OmniGraffle 7.18.3” metadata. Their text elements explicitly specify Athletics. This is a concrete instance of the typography cohesion the user noticed. [MTAN](https://shikun.io/projects/multi-task-attention-network).
- **Browser figures can still be scientific:** Jonathan's rank article exposes Altair chart construction, and its rendered charts use measured singular values and layer facets. HyperNeRF uses an interactive coordinate viewer; Nerfies uses an interpolation slider. A browser implementation earns its place through the relationship it reveals. [Rank study](https://jonathanc.net/blog/llm-effective-rank), [HyperNeRF](https://hypernerf.github.io/), [Nerfies](https://nerfies.github.io/).

The sources establish a mixed workflow: authored vector diagrams, typeset plots, photographic or computed outputs, and purposeful browser interaction. A PNG extension alone does not identify the drawing tool. A polished appearance alone does not validate a result.

## Shikun: every project article linked from the current index

Each row covers the page's principal figure families, not just its cover image.

| Article | Figures and explanation inspected | What SEVEN should learn |
| --- | --- | --- |
| [Prismer](https://shikun.io/projects/prismer) | Real image and expert-label overview; encoder/decoder architecture with resampler/adaptor detail; paired data-versus-performance bubble plots; model and benchmark tables; image/expert/caption examples; three expert ablations. The ablations vary number, quality and noise separately. | Show concrete intermediate products. Give an experiment one question. Keep methods aligned and put the interpretation beside the result. The architecture's boxes name actual transformations. |
| [Kaleido](https://shikun.io/projects/kaleido) | Single-image videos, camera templates, multi-method/multi-view comparisons, reference frames beside a long generated sequence, reconstruction comparisons with ground truth, unusual-input demonstrations. Dataset, view count and resolution identify conditions. | Lead with the working project. A control should vary a meaningful condition while preserving the comparison. Separate reconstruction quality from generation demonstrations. |
| [EscherNet](https://kxhit.github.io/EscherNet) | Input/reference versus novel-view grids; multi-view architecture; camera positional encoding diagrams; comparisons against diffusion and neural-rendering methods; object and mesh results. | A mechanism diagram should show actual representations and their transformations. Reference inputs remain visible, so the output is interpretable. |
| [Auto-Lambda](https://shikun.io/projects/auto-lambda) | Task-grouping formulation, weight evolution, benchmark tables, task-relationship heatmaps across architectures/datasets, task-specific studies. Prose introduces named observations before the corresponding analysis. | A heatmap works when both axes have domain meaning and the colour encodes a defined quantity. Arbitrary sample position is a weaker main-story axis. |
| [ReCo](https://shikun.io/projects/regional-contrast) | Contrastive-learning explanation; label-budget setup; aligned ground-truth, supervised, ClassMix and ReCo output plates; class-relation visualisations. Arrows identify specific segmentation differences. | Compare the same input under fixed conditions, and identify exactly what the reader should inspect. Put the relevant output on the page instead of a status label. |
| [Shape Adaptor](https://shikun.io/projects/shape-adaptor) | Resizing example, two-branch module diagram, sampling detail, robustness plots/tables, learned network shapes, and accuracy versus MACs. Shape examples explain points in the quantitative study. | Pair a mechanism with its measurable consequence. Small multiples are useful when the panels answer related questions. |
| [MAXL](https://shikun.io/projects/meta-auxiliary-learning) | Label-hierarchy table; four auxiliary-learning curves; two-network method and masking explanation; benchmark table; grouped MNIST examples. The text explicitly discusses when the learned grouping lacks an obvious human interpretation. | Use actual cases to interrogate a claim. Discuss a failure or ambiguity at the point where the figure exposes it. |
| [MTAN](https://shikun.io/projects/multi-task-attention-network) | Authored encoder/attention SVGs; weighting formulation and robustness plots; task benchmark tables; aligned input, shared features, attention masks and resulting features. The caption discloses per-image colour rescaling. | Colour and spatial arrangement identify real components. State consequential display transformations; avoid turning every caption into an execution log. |
| [VSL](https://shikun.io/projects/variational-shape-learner) | Hierarchical latent design; generated voxel examples with nearest neighbours; within/across-class morphs; classification table; input/ground-truth/reconstruction comparison; shape arithmetic. | Label distinct evaluation modes. A gallery works when arrangement itself explains generation, interpolation or comparison. |
| [Rays as Pixels](https://wbjang.github.io/raysaspixels/) | Training/inference overview, paired video/raxel/camera-trajectory clips, single-image generation, named camera motions, ablation/self-consistency examples. The page explains the position of each output and the scale alignment to COLMAP. | Show input, intermediate representation and result together. A necessary comparability condition belongs beside the figure. |
| [Saber](https://franciszzj.github.io/Saber/) | Actual masked-frame construction; token/attention architecture; reference images and prompts above named-method video comparisons; multi-view and cross-modal examples. | A prompt is useful when linked visibly to the output it conditions. It should not float in a box as a substitute for showing execution. |
| [MarDini](https://mardini-vidgen.github.io/) | Input-conditioned video galleries for image-to-video, expansion, interpolation, slow motion and view synthesis. Interpolation pairs conditioning frames with generated video; the caption states frame count, speed and data source. | Captions should supply the conditions needed to interpret the demonstration. Group examples by capability; avoid an unexplained collection of screenshots. |
| [vMAP](https://kxhit.github.io/vMAP) | Object-association/training/rendering diagram; scene/object reconstruction, recomposition and novel-view comparisons; Replica, ScanNet and live table examples. The method picture connects masks, samples, object models and the composed scene. | Explain the actual system's data products, then demonstrate its capabilities with outputs. This is a strong systems-project reference for SEVEN. |
| [iMAP](https://edgarsucar.github.io/iMAP/) | Overview video; tracking versus mapping processes; joint optimisation detail; loss bars over corresponding RGB/depth keyframes; additional scene recordings. | A chart and an image can explain each other. Connect a number or decision to the actual event that produced it. |
| [Clarity](https://shikun.io/projects/clarity) | Diagram containers, table styling, galleries, conditional selection, image comparison and coordinated video controls; explicit type, colour and plotting guidance. | Borrow the hierarchy and disciplined comparison patterns. A component's presence in a template is not a reason to add it to SEVEN. |

## Keunhong Park, Ben Mildenhall and Dor Verbin

These are shared/coauthored projects; they are counted once, rather than once per author. Their indices were checked to establish the connections.

| Article | Figure construction and narrative | Consequence for SEVEN |
| --- | --- | --- |
| [HyperNeRF](https://hypernerf.github.io/) | Result videos; simple level-set shapes extended into sliced surfaces; architecture; a coordinate-controlled hyper-space viewer. The abstract geometry is worked through before the representation is used. | Abstraction needs an explicit mapping to the implemented operation and observable consequence. A generic branching metaphor skips that explanation. |
| [Nerfies](https://nerfies.github.io/) | Free-viewpoint portraits; matting/animation examples; an interpolation control between visible endpoint frames; re-rendered input sequences with depth. | A slider should answer a question about a continuous variable or aligned result. Keep the endpoints and output visible. |
| [mip-NeRF 360](https://jonbarron.info/mipnerf360/) | Large rendered-scene/depth teaser and presentation video in a very short project page, with paper/code/data resources. | A strong direct demonstration can carry a project page without numerous supporting widgets. |
| [Zip-NeRF](https://jonbarron.info/zipnerf/) | Sampling geometry, a baseline/ours moving-image wipe for XY aliasing, and image/ray-weight panels for Z aliasing. Each section names a specific failure mode. | Show the defect, then its mechanism, then the changed result. This is a better model for the substring-routing bug than two route cards. |
| [Ref-NeRF](https://dorverbin.github.io/refnerf/) | Reflection-direction explanation, directional encoding, synthetic and captured-scene results, normals, and material-editing demonstrations. | Keep rendering, captured-scene evaluation and controllability distinct. SEVEN likewise needs separate claims for routing, answer quality and measured power. |
| [CamP](https://camp-nerf.github.io/) | Ground-truth and method comparisons with inspection/zoom, camera-parameter perturbation visualisations, convergence videos and matched RGB/depth comparisons. | Controls direct attention to a defined difference under matched conditions. Inspect the delivered media, not just the component shell. |
| [ReconFusion](https://reconfusion.github.io/) | Reconstruction/diffusion method diagram; same-scene named-baseline comparisons; PSNR versus view count; reconstruction-versus-diffusion-sample video plate. | Pair qualitative evidence with an aggregate that tests the same claim. Use a small explicit set of comparison axes. |
| [Eclipse](https://dorverbin.github.io/eclipse/) | Physical occlusion setup, decomposition/ablation plate, and aligned recovered versus true albedo/illumination results. | Explain where measurements come from and show what an internal representation means through its actual outputs. |

## David Ha / otoro

| Article | Figure construction and narrative | Consequence for SEVEN |
| --- | --- | --- |
| [World Models](https://worldmodels.github.io/) | Model schematics with named latent/state/action variables; observation/reconstruction videos; controller variants; real-versus-model environments; reward histograms and failure examples. | It combines diagrams, videos and distributions because each serves a distinct question. The arrows carry specified variables rather than generic “AI” labels. |
| [Weight Agnostic Neural Networks](https://weightagnostic.github.io/) | Animated agents; actual graph mutation operators; network structures; task/weight performance tables and profiles; failure demonstrations. Detailed supplementary questions sit after the main argument. | Keep mechanism and behaviour together. Move exhaustive trials to supporting material. The main article does not need to expose every stored record. |
| [A Visual Guide to Evolution Strategies](https://blog.otoro.net/2017/10/29/visual-evolution-strategies/) | Algorithm animations use the same objective landscapes; covariance is explained in steps; MNIST tables and learning curves provide a separate empirical check. | A teaching graphic can be abstract when its coordinates and operations have precise meaning. Consistent comparison conditions do more work than decorative polish. |
| [Self-Interpretable Agents](https://attentionagent.github.io/) | Input/attention/selected-patch pipeline, agent overlays, architecture and learning curves, and original/perturbed-environment comparisons with named perturbations. | Show the intermediate signal responsible for behaviour. For SEVEN, that means the matched rule or actual response, not a generic complexity label. |

## Jonathan Chang

| Article | Figure construction and narrative | Consequence for SEVEN |
| --- | --- | --- |
| [vLLM from scratch with FlexAttention](https://jonathanc.net/blog/vllm-flex-attention-from-scratch) | Block-mask explanation and code; throughput bars across named memory/batch configurations; request/memory time series used to explain the performance difference. | Ordinary bars can be sufficient. Specific quantities, conditions and an explanation make them useful; an exotic chart is not required. |
| [MIST Bench](https://jonathanc.net/blog/mist-bench) | Physical robot photograph and embedded demonstrations, supported by an account of construction attempts and remaining limitations. | A project article can be visually persuasive with authentic project evidence and little quantitative plotting. SEVEN's terminal footage is an asset. |
| [Effective Rank](https://jonathanc.net/blog/llm-effective-rank) | Exposed computation and interactive Altair facets for singular values, cumulative energy and component counts across layers. The first Q/K/V/O chart was observed rendering in the browser. | Facets work because each panel shares a defined mathematical comparison. Notebook-style code volume is not the right main-page model for SEVEN. |

## What Omni already gets right

The local Omni article leads with an actual reconstruction and then aligns RGB inputs, depth/height, labels and model outputs. Its media illustrate the implemented pipeline. Its plots answer named training/evaluation questions. The reading column and wider media regions support different kinds of content.

Reuse that relationship between project and evidence. Omni also has substantial source-detail captions; the user's current request calls for a lighter presentation here. Copying every caption detail would preserve the clutter being criticised.

## Disposition of every current SEVEN visual component

| Current item | Verdict | Concrete revision specification |
| --- | --- | --- |
| Original PROJECT SEVEN sign and full-window video | **Keep as the lead evidence.** | Preserve the footage. Use a short caption describing what the viewer sees. Put recording dimensions, date, capture procedure and raw files in Methods. |
| Eight video chapter buttons | **Reduce the primary choices.** | Expose the three execution paths; place utility/history moments in the extended walkthrough. Avoid repeating another navigation row immediately below. |
| Video caption/source row | **Cut its repeated metadata and file links.** | It currently has 77 words and three links. Keep a result description and the demonstration/benchmark distinction; relocate capture details and downloads to one evidence section. |
| Six-link article navigation row | **Remove from this short main flow.** | Section headings already provide the structure. It currently adds another group of controls between the demonstration and the argument. |
| Seven-item full-window screenshot gallery | **Consolidate with the walkthrough.** | Retain a full-size relevant frame only where it adds evidence beyond the video. Put the remaining frames in supporting material. Do not shrink three whole terminals into unreadable tiles. |
| Original/restored route selector cards | **Replace.** | The entanglement selection shows “Cloud model” twice and offers no explanation beyond a repeated rule category. Show the actual `eth` match within `whether`, the original and whole-word predicates, and their recorded decisions on that same input. No prompt-to-box metaphor is needed. |
| Routing alluvial ribbons | **Replace as the main aggregate.** | Their area is dominated by unchanged local decisions, while the two-case transition needs a separate note. A compact labelled transition-count table is sufficient unless a new plot makes a specific comparison clearer. Counts do not establish routing accuracy. |
| Local-study results table | **Retain and simplify.** | Its three configurations, numeric matches and missed uncertainty flags state the result directly. Keep the sample and grading definition nearby. Avoid duplicating the same totals in another decorative figure. |
| 180-square outcome matrix | **Remove from the main article.** | The x-position is sample order within arbitrary blocks, not a meaningful predictor. Small grey/blue marks hide the text of the failure and require a legend. The table already states the aggregate. Preserve the records in the supplement. |
| Latency ECDF beside that matrix | **Separate or move to the supplement.** | It answers a different question from uncertainty detection. Give latency its own stated engineering question before using a distribution plot. |
| 60-question / 180-answer browser | **Move to a separate evidence page.** | Replace the main-page wall with one clearly identified, typeset case from the archived responses: question, reference, relevant response lines and the failed check. Keep complete replies accessible without making them the main figure. |
| Three whole-laptop power panels | **Retain the data; redesign the explanation.** | A main figure should explain one actual inference interval and its measurement boundary. Put the complete three-run traces in supporting material. Never present these runs as a controlled model-efficiency or cloud-savings comparison. |
| Raw data/code/PDF links in each caption | **Consolidate.** | Four current captions carry 3–4 links each and roughly 72–81 words. Use one Methods and evidence location for the archive; captions should explain the finding and essential conditions. |

## Language and figure production for the next revision

Use headings that state a concrete question or observation. Replace “Read the answers behind the squares” with a sentence about the actual failure, such as “Wrong answers did not reliably trigger escalation.” Explain the test before showing its outcome. Use ordinary prose for limitations instead of repeated labels such as “not measured,” “captured in,” and “execution records” around the media. Preserve a qualification when removing it would change the claim.

For example, the video needs only: “SEVEN running on the laptop: a local answer, live-data requests and cloud inference in one conversation. This walkthrough demonstrates functionality.” Recording details can then be stated once in Methods. An uncertainty result can say: “In the revised-prompt run, 38 of 60 replies failed the numeric check; none triggered the uncertainty rule.” That remains narrower than a claim about general answer correctness.

For data figures, retain Python for verified calculations and export the plotting tables. Typeset the final composition in PGFPlots/TikZ with deliberate label placement and the established portfolio typography. For a mechanism that earns a separate figure, use an editable vector drawing whose operations correspond to the source. Preserve exact outputs as media or faithful typeset quotations. Inspect each export at its actual page size and in PDF, rather than approving it because it is vector.

This follows the [HKUST guidance](https://library.hkust.edu.hk/news-events/news/using-ai-create-scientific-figures-responsibly): choose tools according to whether the material explains a concept, analyses data or records an observation; preserve sources and check meaning, labels, axes and units. No generative reconstruction of SEVEN footage or invented data is needed.

Before building any replacement, specify its one-sentence finding, source records, meaningful comparison, annotations and intended display width. The main page should be readable without touching a control. Interactions should deepen a visible result. A small set of strong figures is sufficient; there is no target figure count to fill.

## Status

This pass delivers the audit and revision specifications. The article's rejected figures remain in the local preview pending implementation; no claim is made that the article is finished. No reference images or results have been substituted for SEVEN evidence. Nothing has been published.
