# Software Aging in LLM-Generated Applications: Runtime Evidence, Static Analysis, and Human-Written Comparisons

This repository contains the experimental artifacts used in the research study:
**"Software Aging in LLM-Generated Applications: Runtime Evidence, Static Analysis, and Human-Written Comparisons"**,
authored by Cézar Santos, Michele Vitagliano, Roberto Natella, and Ermeson Andrade.

## 📋 Project Overview

The goal of this study is to evaluate how software aging manifests in service-based backend applications generated automatically by Large Language Models (LLMs). Using backend scenarios derived from [BaxBench](https://github.com/eth-sri/baxbench), we generated applications in three generation-and-execution environments:

- **JavaScript** — generated with [Bolt](https://bolt.new/), implemented with Node.js and Express.
- **Python** — generated with ChatGPT, implemented with FastAPI.
- **Rust** — generated with Gemini, implemented with Actix Web.

Each application was functionally validated with BaxBench-derived tests and then subjected to a **48-hour continuous workload execution** using Apache JMeter. During each run, memory usage, response time, and throughput were monitored and later analyzed with the Mann–Kendall test and Sen's slope estimator to detect statistically significant aging trends.

Beyond the runtime experiments, the study also includes:

- A **static analysis** of the LLM-generated source code (traditional tools + an LLM-assisted code-review workflow) to identify plausible code-level aging mechanisms.
- An **exploratory comparison** with functionally related human-written open-source implementations, executed under the same workload and monitoring pipeline.

## 📁 Repository Structure

```text
generated-software-llm/
├── Annex-RQ1.pdf                  # Annex with the full time-series plots for RQ1 (referenced in the paper)
├── data/                          # Sample images and aggregate data used in the experiments
├── jmeter/                        # JMeter test plans (.jmx) used for stress testing each LLM-generated application
├── generated-projects/            # Source code of the LLM-generated applications (RQ1/RQ2)
│   ├── js/                        # JavaScript/Node.js/Express implementations (Bolt)
│   ├── python/                    # Python/FastAPI implementations (ChatGPT)
│   └── rust/                      # Rust/Actix Web implementations (Gemini)
├── open-source-projects/          # Human-written baselines used for the RQ4 comparison
│   ├── ImageConverter_flask/      # Human-written Image Converter (Flask) — gif-creator-python
│   ├── Monitor_fastAPI/           # Human-written Monitor (FastAPI) — System-Monitor
│   ├── UptimeService_fastAPI/     # Human-written Uptime (FastAPI) — calmmage-service-registry-api
│   └── jmeter_test_plans_open/    # JMeter test plans used against the human-written baselines
├── code-review-reports/           # Static-analysis and LLM-assisted code-review outputs (RQ3)
│   ├── JavaScript_Express/        # CodeQL, SemgrepCE, SlowQL, and AI (Claude Code) reports
│   ├── Python_FastAPI/            # CodeQL, SemgrepCE, SlowQL, LeakAudit, and AI (Claude Code) reports
│   ├── Python_Flask/              # CodeQL, SemgrepCE, LeakAudit, and AI (Claude Code) reports
│   └── Rust_Actix/                # CodeQL, SemgrepCE, and AI (Claude Code) reports
├── prompt/                        # Prompts used to generate the applications via LLMs
│   ├── js/                        # Prompts used with Bolt
│   ├── python/                    # Prompts used with ChatGPT
│   └── rust/                      # Prompts used with Gemini
└── scripts/                       # Auxiliary scripts
    ├── collect-data/              # Server-side monitoring scripts (PSUTIL-based) run during the 48h workloads
    ├── tests/                     # Functional validation tests derived from BaxBench
    └── resources-analyzer/        # R project: statistical analysis (Mann-Kendall/Sen's slope) and plot generation
```

> **Note:** the `Python_Flask` folder under `code-review-reports/` is not yet described in this README — please confirm whether it corresponds to the human-written open-source baselines (`open-source-projects/`) or to an earlier Python/Flask generation round, so the description above can be corrected if needed.

## 🧪 Applications Tested

1. **Image Converter** – Merges images into a GIF.
2. **Credit Card** – Encrypted credit-card/password manager.
3. **Monitor** – Tracks active system processes.
4. **Uptime** – Checks whether a given service is online.

All applications were generated from standardized prompts derived from the [BaxBench benchmark](https://github.com/eth-sri/baxbench), preserving the same endpoints, route names, input formats, and expected behavior across the three language ecosystems, and validated functionally before being included in the long-duration tests. Implementations that failed validation were discarded and regenerated from scratch, without manual correction.

## 👥 Human-Written Comparison (RQ4)

For the exploratory comparison with human-written systems (`open-source-projects/`), three Python open-source repositories were selected as the closest functional counterparts to three of the four scenarios (Image Converter, Monitor, and Uptime — no human-written counterpart was used for Credit Card):

- **Image Converter:** [gif-creator-python](https://github.com/ParasJagdale/gif-creator-python) (Flask)
- **Monitor:** [System-Monitor](https://github.com/Shaso41/System-Monitor) (FastAPI)
- **Uptime:** [calmmage-service-registry-api](https://github.com/calimage/calmage-service-registry-api) (FastAPI)

These baselines were executed with the same 48-hour workload, monitoring infrastructure, and statistical-analysis pipeline as the LLM-generated applications, using the JMeter plans in `open-source-projects/jmeter_test_plans_open/`.

## 🔍 Static Analysis & Code Review (RQ3)

`code-review-reports/` contains the raw outputs of the static-analysis procedure described in the paper, organized per generation-and-execution environment:

- **CodeQL** — SARIF results from multiple query suites (default, security-quality, security-experimental, community audit packs, depending on language support).
- **SemgrepCE** — SARIF results from default and security-audit rulesets.
- **SlowQL** — performance/slow-query findings (JavaScript and Python/FastAPI only).
- **LeakAudit** — resource-leak findings (Python only).
- **AI_Code_Review** — the two-phase Claude Code-based workflow: the prompts sent to the orchestrating/specialist/reviewer agents (`Claude_Code_prompts/`) and the resulting structured findings (`Claude_Code_Reports/`), one report per application scenario.

## 🗃️ Raw Experimental Data

Due to their size (server-side monitoring CSVs, per-process logs, and raw JMeter response-time/throughput captures for the full 48-hour runs), the raw datasets are **not stored in this Git repository**. They are available here:

- **Raw data (Google Drive):** <https://drive.google.com/drive/folders/1UziizuiuX8eOoAH2dEUgCXPe5aDsJhzr?usp=sharing>

The repository itself only contains the scripts, source code, prompts, and test plans needed to reproduce the experiments; `scripts/resources-analyzer/data` and `results` are populated locally from the raw data above before running the statistical analysis.

## ⚙️ How to Reproduce the Experiments

1. Install [Apache JMeter](https://jmeter.apache.org/).
2. Use the JMX files from the `jmeter/` folder (LLM-generated apps) or `open-source-projects/jmeter_test_plans_open/` (human-written baselines) to run each test (one per application/language combination).
3. Deploy the corresponding application — from `generated-projects/` or `open-source-projects/` — on a server machine accessible by the JMeter client machine.
4. On the server, run the monitoring scripts in `scripts/collect-data/` to collect RAM/CPU/process-level metrics throughout the 48-hour execution.
5. Results (JMeter response-time/throughput logs and server-side monitoring CSVs) are stored as configured in the JMeter test plan and monitoring scripts, or can be downloaded directly from the raw-data link above.
6. Use the R project in `scripts/resources-analyzer/` to run the statistical trend analysis and generate the plots (see `Annex-RQ1.pdf` for the full set of time-series plots discussed in the paper).

## 📊 Analysis Techniques

To assess aging trends, the following statistical methods were applied:

- **Mann-Kendall test** — to detect statistically significant monotonic trends (p < 0.05).
- **Sen's Slope Estimator** — to quantify the magnitude and direction of the trend.
- Confidence intervals were computed for each metric to support result interpretation.
- **Time Series Analysis** — to visualize trends over time.

Additionally, the generated source code was examined with static-analysis tools (CodeQL, Semgrep, LeakAudit, SlowQL) and an LLM-assisted code-review workflow (based on Claude Code) to identify plausible code-level aging mechanisms and relate them to the observed runtime symptoms.

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## 📚 Citation

If you use this repository, please cite the associated paper:

```text
Cézar Santos, Michele Vitagliano, Roberto Natella, and Ermeson Andrade.
"Software Aging in LLM-Generated Applications: Runtime Evidence, Static Analysis,
and Human-Written Comparisons."
```
