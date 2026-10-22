# DQI: Clearer Hops

**Team:** Ducks are surprisingly cool · **Team member:** Ethan Feldman

An industrial sensor fleet needs to move telemetry through crowded spectrum. Every transmitter chooses a compact
six-hop frequency schedule; every clear hop creates a useful transmission opportunity. This project uses
**Decoded Quantum Interferometry (DQI)** to sample better schedules from a fixed availability-query budget.

The interface follows the full case: the commercial problem, the quantum mechanism, executed Qiskit results,
and the value and hardware scale implied by an explicit operating model. The measured experiment provides
**evidence for quantum query advantage**: **78.904%** mean clear hops versus a **75.806%** ceiling for any
classical planner given six ordinary membership queries and the same hidden balanced-mask prior.

For register maps, logical diagrams, gate-by-gate explanations, measurement estimators, every executed fixture,
and the exact live-job budget, see the **[Circuit guide](CIRCUITS.md)**.

**Contents:** [Run on Qollab](#run-on-qollab) · [Problem and approach](#how-the-interface-builds-the-case) ·
[Results](#experiments-and-measured-signals) · [Commercial value](#commercial-value-and-future-projections) ·
[Files and local setup](#files) · [Disclosure](#disclosure)

## GitHub Pages demo

[Open the DQI frequency-hopping demo](https://ethanfeld.github.io/DQI-Frequency-Hopping/). The page presents the
saved sixteen-fixture Qiskit study, classical controls, measured plans and editable commercial scenario. It runs
as a static site; a fresh simulator job runs when the project is uploaded to Qollab and its **Run** button is used.
This source repository is [`EthanFeld/DQI-Frequency-Hopping`](https://github.com/EthanFeld/DQI-Frequency-Hopping).

## Run on Qollab

1. Create a **JavaScript project** and upload this folder. Keep `index.html`, `main.js`, and `main.css` at the root,
   with `dqi/` and `data/` beside them. Upload the contents directly, without an extra enclosing directory.
   Every file fits the **2 MB per-file limit** (2,000,000 bytes); the largest is 1,952,296 bytes.
2. Select the **ideal built-in Qiskit simulator**, then press Qollab's **Run**. The saved 16-fixture study appears
   immediately while the fresh calculation runs.
3. Read the four numbered sections. Open **Inspect circuits, classical controls and all 16 fixtures** to select
   a fixture and inspect an actual measured six-hop plan.
4. In **Results of run**, the **Project Run** card displays the fresh 512-shot result when the job finishes.
   Its export contains the complete raw counts, physical-channel scores and resource ledger.
5. In **Conclusions and future projections**, edit fleet traffic, radio airtime, avoidable transmission cost and
   the complete extra DQI planning price. The visibility slider changes the analytic hardware projection.

One Run submits **one 24-qubit native circuit in one `backend.run` call**, with **512 shots** and replay seed
`941001`. The decoder and both three-hop windows execute coherently. The selected simulator generates the
measurements; shipped counts populate the separately labelled saved study.

| Backend | Live job | Recorded execution |
|---|---|---|
| Qollab built-in `BasicSimulator`, ideal | 24 qubits, 512 shots, one circuit | 77.962% mean clear hops; 512 raw outputs; zero workspace failures |
| Qiskit Aer MPS, ideal, zero truncation | Same primitive circuit and fixed replay fixture | 76.953% mean clear hops; 512 raw outputs; zero workspace failures |

These two recorded executions are checks of the same fixed replay circuit. Their finite-shot means differ.
The advantage comparison uses the independent 16-fixture bank. Dense 24-qubit simulation can take several
minutes; circuit and query counts determine the resource comparison. The live adapter accepts ideal Qiskit
BasicSimulator or Aer backends; the built-in simulator is the upload's supported starting configuration.

## How the interface builds the case

1. **Problem setting:** choose frequency schedules for industrial telemetry. The six-hop task uses 32 channel
   labels, with 16 clear channels at each hop. Application selection follows the fit between clear-hop quality,
   useful radio opportunities and retry load.
2. **DQI and its advantage:** follow preparation, phase queries, coherent decoding and measurement. Two
   single-parity-check windows, `(u, v, u XOR v)`, turn four five-bit symbols into six physical hops.
3. **Results of run:** compare all 65,536 native outputs with a certified classical ceiling and four executed
   classical strategies. Inspect source hashes, gate costs, every fixture and the fresh selected-backend run.
4. **Conclusions and future projections:** translate clear-hop scores into a packet-per-hop scenario, calculate
   the maximum affordable DQI premium, and inspect larger parallel batches and wider channel alphabets.

The commercial motivation follows the role of channel diversity and retransmission energy in
[industrial wireless sensor networks](https://www.analog.com/en/resources/technical-articles/reliable-lo-power-wsn-for-iot.html).
The selected deployment is **on-demand availability planning**. A quantum implementation needs a reversible,
coherent availability predicate. Ordinary spectrum readings, cached channel maps and conventional APIs provide
classical information. [GPU radio-map tools such as Sionna RT](https://research.nvidia.com/publication/2025-04_sionna-rt-technical-report)
belong in the deployment comparison.

## Experiments and measured signals

| Experiment | Circuit or control | Result |
|---|---|---|
| Held-out DQI study | 16 distinct availability inputs; 24 qubits; 4,096 native shots per circuit | **78.904%** mean clear hops; approximate 95% fixture interval **78.612%–79.197%** |
| Adaptive classical comparison | Four six-query strategies; 256 outputs per strategy per fixture | Best executed mean **74.561%**, from adaptive knowledge gradient |
| All-strategy classical certificate | Unlimited classical arithmetic; even the hopping constraints are relaxed | Ensemble mean **≤47/62 = 75.806%** after six membership queries |
| Readable-input control | Read 192 availability bits; optimize two sets of 1,024 local assignments | **100%** clear hops on all 16 fixtures |
| Live replay | Same DQI family, seed 941001; 24 qubits; 512 shots on the selected backend | Fresh mean, raw counts, workspace check and full-input control after each Run |
| Native state audit | Independent contraction of saved native tensors and comparison with the DQI identity | **16,777,216** decision amplitudes checked; maximum error **1.34 × 10⁻¹¹** |

All quantum benchmark shots contribute to the headline mean. The fixture selector shows one observed output,
rather than selecting the best shot for the headline. The classical bound is an ensemble bound under the specified
input-access model. Public replay seeds and a readable full mask define different information access.

### What is live and what is modeled

| Interface content | Source | Backend work on project Run |
|---|---|---|
| 16-fixture results, counts and classical means | Shipped, completed native Qiskit study | None; saved evidence remains visible |
| Project Run card | Selected Qiskit backend, fixed replay seed | One fresh 24-qubit circuit, 512 shots |
| Physical hopping plan and score | Decode a saved or fresh measured bit string | Classical analysis of existing counts |
| Six-query classical ceiling | Exact finite posterior-gain bound | Classical arithmetic |
| Full-input optimum | Exact local enumeration of the supplied mask | Classical arithmetic |
| Fleet value calculator | Measured scores plus entered traffic and prices | JavaScript calculation |
| Larger machines and wider alphabets | Analytic DQI and classical-bound formulas | JavaScript calculation |
| Visibility slider | Per-window ideal/uniform mixture | JavaScript calculation |

The upload includes the full saved quantum counts, protocol, classical summaries, native audit receipt and the two
backend replay records. Detailed research tensors and classical query transcripts are retained separately from the
upload. Their original file names and hashes remain in the evidence as provenance.

The two saved-study files use compact JSON formatting to fit the upload limit. All measurements and metadata are
preserved. Verification reconstructs the original audited JSON bytes and checks their original SHA-256; the
interface records both the compact upload hash and the original audit hash.

## Commercial value and future projections

The measured lift translates to **30,980 extra clear-hop opportunities per million transmission attempts**.
Under a one-packet-per-hop model with independent refreshed availability on retries, it gives **4.087% more useful
opportunities at fixed attempts**, or **3.926% fewer attempts at fixed successful traffic**.

The default operating scenario uses 10,000 sensors, four packets per 30 seconds per sensor, 10 ms of radio airtime
per attempt and $10 of avoidable cost per million attempts. The reporting rate follows a published
[industrial sensor traffic profile](https://www.analog.com/en/resources/analog-dialogue/articles/designing-your-smart-wireless-industrial-sensor.html);
fleet size, airtime and prices are editable scenario inputs.

| Default scenario output | Value |
|---|---:|
| Successful traffic target | 115.2 million packets/day |
| Avoided attempts | 5.97 million/day |
| Aggregate radio airtime saved across the fleet | 16.57 hours/day |
| Gross annual avoidable cost | **$21,778** |
| Break-even extra DQI price | **$2.452 per million six-hop plans** |

The default planning premium is $0, exposing the gross opportunity ceiling. Enter the complete price above
classical planning—including coherent input access, preparation, gates, readout and error correction—to obtain
net value. Fixed infrastructure costs stay outside the savings model. Capacity gains and retry savings are
alternative uses of the same lift; dollars are counted once.

For delivered traffic `D`, `pQ = 0.7890446981` and `pC = 47/62`:

```text
saved attempts/day = D × (1/pC − 1/pQ)
DQI plans/day      = D / (6 pQ)
annual net value   = 365 × [saved attempts × cost per attempt
                           − DQI plans × extra cost per plan]
```

| Analytic 32-channel projection | 24 algorithm qubits | 96 | 240 | 1,200 |
|---|---:|---:|---:|---:|
| Independent windows in parallel | 2 | 8 | 20 | 100 |
| Physical hops and planning queries/batch | 6 | 24 | 60 | 300 |
| CX gates/batch | 696 | 2,784 | 6,960 | 34,800 |
| Ideal ensemble mean clear hops | 78.8675% | 78.8675% | 78.8675% | 78.8675% |

A reusable 12-qubit core can process these windows sequentially. Larger hardware adds parallel decision capacity;
the percentage gain remains constant at fixed alphabet size. Wider channel alphabets increase the analytic
gap: **3.0611 percentage points at 32 channels**, **3.7695 at 256**, and **3.8431 at 1,024**. Oracle tables and
their synthesis costs grow with the alphabet. Algorithm-qubit counts exclude physical error-correction overhead.

The noise slider uses `pQ(v) = 1/2 + v/(2√3)`, mixing ideal and uniform outputs **per window**. Its 32-channel
break-even visibility is **89.3962%**. Visibility is a model parameter; gate-level noise calibration and device
throughput are deployment inputs. See the [projection derivation](CIRCUITS.md#projections-and-noise-model).

## How it uses Qollab

- **JavaScript project:** `main.js` imports `dqi.checkcode_ui` and invokes
  `.backend_info.callPromising(backend)` and `.live_job.callPromising(backend, 512, 941001)`.
  Python returns JSON; the page renders and exports it.
- **One selected-backend job:** both windows are composed into one 24-qubit circuit and submitted once.
  **Run fresh circuit** repeats this job on the supported ideal simulator.
- **Native preparation and decoding:** the algorithm uses local amplitude preparation, a phase oracle, reversible
  syndrome routing, a code-only decoder and final Hadamards. The output distribution arises from those gates.
- **Portable primitive circuit:** compilation uses `u` and `cx`, followed by 24 computational-basis measurements.
  The replay circuit has **696 CX and 1,041 one-qubit gates per shot**.
- **Simulator support:** Qollab uses its selected built-in backend. Aer is an optional local simulator;
  importing the live adapter does not import Aer.
- **Evidence exports:** saved measurements, a fresh run and the editable commercial scenario are separately
  labelled. A failed run displays its error and retains the saved study.
- **Resource comparison:** each output charges six planning queries and six separate postcommit score checks.
  Quantum gate work and input construction remain in their own ledger.

## Files

```text
README.md                       project, Qollab instructions, results, commercial interpretation
CIRCUITS.md                     registers, logical diagrams, each circuit, estimators and run budget
index.html  main.js  main.css    Qollab entry, selected-backend bridge and presentation
dashboard.js                    current DQI page lifecycle, exports and provenance
query_frontpage.js              four-section commercial case, fixture inspector and controls
query_value.js                  operating model, assumptions and analytic scaling calculations
dqi/__init__.py                 Python package entry
dqi/checkcode_ui.py             ideal selected-backend adapter and one-job live execution
dqi/local_check_hopping.py      frozen circuit, query certificate and classical controls
data/checkcode_results.js       saved study loaded by the browser
data/checkcode_results.json     identical study for direct inspection and verification
data/checkcode_audit.json       receipt from the independent native tensor/transcript audit
data/checkcode_backend_runs.json saved BasicSimulator and Aer replay counts
benchmarks/checkcode_experiment.py frozen generator for a new 16-fixture experiment
tools/verify.py                 verify shipped counts, source hashes, circuits and local links
tools/serve.py                  standalone local saved preview or ideal Qiskit live server
tools/package.py                build the explicit-file-list Qollab ZIP and verify every byte
tools/build_pages.py            assemble the static GitHub Pages demo; not in the Qollab ZIP
.github/workflows/pages.yml     deploy the static GitHub Pages demo; not in the Qollab ZIP
preview.html  preview.js        saved-evidence browser preview
LICENSE                         MIT license
```

### Local verification and packaging

Install `numpy` and `qiskit` for verification; add `qiskit-aer` for the local Aer server.
Run the verification and packaging commands from this project folder:

```text
python tools/verify.py
python tools/package.py
```

The packager writes `dqi-hop-qollab-js.zip` two directories above this project, with entry files directly at ZIP root.
Both verification and packaging enforce the 2,000,000-byte limit on every uncompressed upload file.

The GitHub Actions workflow publishes the saved-evidence preview at the repository root whenever `main` changes.
For the first deployment, set **Settings → Pages → Build and deployment → Source** to **GitHub Actions**. After
deployment, the URL above opens the demo; the Qollab project remains the place to run a fresh circuit.
Pass a destination explicitly with `python tools/package.py path/to/upload.zip`; its parent directory must exist.

Choose a preview mode:

| Mode | Command | Open in a browser |
|---|---|---|
| Saved evidence | `python tools/serve.py --backend saved --port 8776` | `http://127.0.0.1:8776/preview.html` |
| Fresh ideal Aer run | `python tools/serve.py --backend aer --port 8778` | `http://127.0.0.1:8778/` |

Each server keeps its terminal occupied until stopped with **Ctrl+C**. Use separate terminals to run both.
Replace `aer` with `builtin` for a local BasicSimulator run; that mode needs NumPy and Qiskit only.

To generate a new held-out bank, install `scipy` and `qiskit-aer` as well, then run
`python benchmarks/checkcode_experiment.py` **in a separate working copy**. That command draws fresh fixture seeds
and writes a new experiment, raw transcripts and native tensors. The shipped bank preserves the existing audited run.

## Disclosure

- **Prior work:** the project builds on [Decoded Quantum Interferometry](https://www.nature.com/articles/s41586-025-09527-5)
  and the supplied [DQI paper, arXiv:2610.06753](https://arxiv.org/abs/2610.06753). This project's parity-check
  construction and finite classical certificate are derived explicitly in [CIRCUITS.md](CIRCUITS.md).
- **AI assistance:** parts of the original starter were drafted with Claude (Anthropic). OpenAI Codex assisted
  with the DQI implementation, benchmarking and verification, the Qollab interface, and project documentation.
  Source hashes, raw counts and verification commands make the reported calculations inspectable.
- **Human review:** review all generated code, results and documentation before submission.
- **Evidence:** synthetic availability masks and ideal native Qiskit executions. The measured advantage concerns
  six-query access to independent hidden balanced predicates. Readable full inputs select the 100% classical control.
- **Commercial quantities:** operating scenarios calculated from measured scores and user-entered prices.
- This effort is supported via compute credits from Qollab and IonQ.

MIT License (see [LICENSE](LICENSE)).
