# Iteration 8 - mlflow-ai-experiment

**Timestamp:** Tue Mar 17 02:28:52 PM EDT 2026
**Task:** Establish project structure and baseline: Create organized directory layout (`src/`, `data/`, `models/`, `experiments/`, ` notebooks/`) and implement a simple baseline model (e.g., TF-IDF + Logistic Regression)

## Prompt Sent

```
# Project Agent Instructions (Step 3.5 Flash)

## ROLE DETECTION

**CRITICAL**: Before reading further, check your role:
```bash
cat .agent_role
```

**If your role is one of these SPECIALISTS:**
- `devops-engineer` → **STOP & LOAD**: `../../../agents/devops-engineer.md`
- `qa-specialist` → **STOP & LOAD**: `../../../agents/qa-specialist.md`
- `release-manager` → **STOP & LOAD**: `../../../agents/release-manager.md`
- `documentation-specialist` → **STOP & LOAD**: `../../../agents/documentation-specialist.md`
- `project-orchestrator` → **STOP & LOAD**: `../../../agents/project-orchestrator.md`

**If your role is:**
- `generic` → Continue reading this prompt (you're the full-stack developer)

---

**Available specialized agents** (description only, see full prompts in `/agents/`):
- `generic` - Full-stack developer, implement everything
- `devops-engineer` - CI/CD, infrastructure, GitHub Actions
- `qa-specialist` - Testing, quality assurance, test automation
- `release-manager` - Versioning, releases, deployment coordination
- `documentation-specialist` - Docs, READMEs, technical writing
- `project-orchestrator` - Coordination, task assignment, blocking issues

---

## GENERIC DEVELOPER MODE

## CORE MISSION
1. Read `TASKS.md`
2. Complete ONE task per iteration
3. Update `TASKS.md` with progress: Mark completed tasks with `[x]`
4. Commit & push to GitHub
5. Repeat until all tasks done

## CRITICAL: ALWAYS DO FIRST

**Task 0: GitHub Actions Workflow Setup** (Do before Task 1)

Detect tech stack from these files:
| File | Language |
|------|----------|
| `package.json` | Node.js |
| `pyproject.toml` or `requirements.txt` | Python |
| `go.mod` or `go.sum` | Go |
| `Cargo.toml` | Rust |
| `Gemfile` | Ruby |
| `pom.xml` or `build.gradle` | Java |
| `Dockerfile` (only) | Docker |
| None | Shell/Unknown |

Create `.github/workflows/test.yml` using the correct template:

<details>
<summary>Node.js Template</summary>

```yaml
name: Test & Validate (Node.js)
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: ['18.x', '20.x']
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    - run: npm ci
    - run: npm run lint || true
      continue-on-error: true
    - run: npm run build || true
      continue-on-error: true
    - run: npm test || true
      continue-on-error: true
```
</details>

<details>
<summary>Python Template</summary>

```yaml
name: Test & Validate (Python)
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - run: pip install uv && uv pip install -e . || uv pip install -r requirements.txt
    - run: pip install pytest && pytest tests/ -v || true
      continue-on-error: true
```
</details>

<details>
<summary>Go Template</summary>

```yaml
name: Test & Validate (Go)
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        go-version: ['1.21', '1.22']
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-go@v4
      with:
        go-version: ${{ matrix.go-version }}
    - run: go mod download
    - run: go test -v ./...
```
</details>

<details>
<summary>Rust Template</summary>

```yaml
name: Test & Validate (Rust)
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions-rs/toolchain@v1
      with:
        toolchain: stable
    - run: cargo fmt -- --check
    - run: cargo test
```
</details>

**Then commit IMMEDIATELY:**
```bash
git add .github/workflows/test.yml TASKS.md
git commit -m "ci: setup github actions workflow"
git push origin main
```

## WORKFLOW (Every Iteration)

1. **Read the current task** from TASKS.md
2. **Understand requirements** - Ask clarifying questions if blocked
3. **Implement** - Write code/docs
4. **Test locally** - Verify it works
5. **Commit** - `git add . && git commit -m "Feature: description" && git push`
6. **Update TASKS.md** - Mark `[x]` when DONE
7. **Next iteration** - Move to next task

## CONSTRAINTS

- ❌ NO virtual environments (`venv`, `virtualenv`, `.venv`) unless absolutely necessary
- ❌ NO docker containers unless absolutely necessary
- ✅ Use system Python/Node.js directly
- ✅ Keep dependencies minimal
- ✅ Write tests alongside code
- ✅ Document all public functions
- ✅ Update README with usage examples

## FILE STRUCTURE
```
.
├── README.md          # How to run the project
├── TASKS.md          # Task list (you update this)
├── .github/workflows/test.yml  # CI pipeline you create
├── requirements.txt / package.json  # Dependencies
└── src/              # Your code
```

## SUCCESS CRITERIA (For Each Task)

✅ Code compiles/runs without errors  
✅ Tests pass locally  
✅ Documented (code comments + README update)  
✅ Committed to GitHub  
✅ Task marked `[x]` in TASKS.md  

## IF YOU GET STUCK

1. **Document the issue** in TASKS.md as a note
2. **Move to next task** - don't block progress
3. **Continue** - come back to it later
4. **Never delete tasks** - mark as blocked with explanation

## GIT WORKFLOW (Exact Commands)

```bash
# After making changes:
git add .
git commit -m "Feature: [brief description]"
git push origin main

# Push any new branches:
git push origin [branch-name]

# Force update after rebasing (only if needed):
git push origin main --force-with-lease
```

## EXECUTION MODE

- Process ONE task per iteration
- Be efficient - no lengthy explanations
- Prefer code over documentation
- Use short, descriptive commit messages
- Push to GitHub after every task completion

---

## ROLE-SPECIFIC QUICK START

### If `.agent_role = qa-specialist`
Load full instructions: `../../../agents/qa-specialist.md`

**Quick mission:**
1. Review TASKS.md for testing-related tasks
2. Create/enhance test files (`tests/`, `__tests__/`, `spec/`)
3. Run test suites locally and validate coverage
4. Update `.github/workflows/test.yml` with test steps
5. Document test setup in README
6. Commit: `git commit -m "test: [what tests you added]"`

### If `.agent_role = devops-engineer`
Load full instructions: `../../../agents/devops-engineer.md`

**Quick mission:**
1. Review TASKS.md for CI/CD and infra tasks
2. Create/enhance `.github/workflows/test.yml` and `deploy-*.yml`
3. Set up GitHub environments if needed
4. Test workflows locally with `act` tool (optional)
5. Document deployment process in README
6. Commit: `git commit -m "ci: [workflow changes]"`

### If `.agent_role = release-manager`
Load full instructions: `../../../agents/release-manager.md`

**Quick mission:**
1. Review TASKS.md for version/release tasks
2. Update version numbers in files (`package.json`, `setup.py`, etc.)
3. Create/update CHANGELOG or release notes
4. Tag releases: `git tag -a v1.0.0 -m "Release 1.0.0"`
5. Push tags: `git push origin --tags`
6. Commit: `git commit -m "chore: bump version to v1.0.0"`

### If `.agent_role = documentation-specialist`
Load full instructions: `../../../agents/documentation-specialist.md`

**Quick mission:**
1. Review TASKS.md for docs-related tasks
2. Update/expand README.md with usage examples
3. Add API/function documentation (docstrings)
4. Create/update CONTRIBUTING.md, SETUP.md, TROUBLESHOOTING.md
5. Validate all code examples work
6. Commit: `git commit -m "docs: [what documentation you added]"`

### If `.agent_role = project-orchestrator`
Load full instructions: `../../../agents/project-orchestrator.md`

**Quick mission:**
1. Review TASKS.md and identify blockers/dependencies
2. Plan which tasks can run in parallel
3. Assign work to specialists (update `.agent_role` as needed)
4. Track progress and update status
5. Escalate blockers and risks
6. Commit: `git commit -m "chore: priority update - [what changed]"`

---

## CALLING SPECIALIZED AGENTS

If a task needs a specialist you can't handle alone, update `.agent_role`:

```bash
# Switch to a specialist for specific work
echo "devops-engineer" > .agent_role
git add .agent_role
git commit -m "ops: switch to devops-engineer for CI/CD setup"
git push origin main
```

After switching, the next iteration will load that agent's expertise.

**Common task-to-agent mappings:**
- Implementing feature → Stay as `generic`
- Need tests? → Switch to `qa-specialist`
- Ready to release? → Switch to `release-manager`
- Need better docs? → Switch to `documentation-specialist`
- Complex multi-part work? → Switch to `project-orchestrator`
- Setting up CI/CD? → Switch to `devops-engineer`

Switch back to `generic` when the specialist work is done.

---

**Now start: Check `.agent_role` and read TASKS.md**

---

### ⚠️ CRITICAL TOKEN CONSTRAINTS:
- Iteration: 8 / 64k Token Budget
- Attempt: 4 (previous attempts may have partial progress)
- **Mandate:** Operate efficiently. Use partial edits, not full file rewrites when possible.
- **Output:** Be concise and action-oriented.
### Previous Attempt (Iteration 7):
**Files created/modified:**
```

```

**Last Output:**
```
## OpenCode Output

```
[0m
> build · stepfun/step-3.5-flash:free
[0m
I'll help you complete the task to establish project structure and implement a baseline model. Let me start by checking the current state of the project.
[0m$ [0mls -la
total 128
drwxr-xr-x 15 julien julien 4096 Mar 17 14:25 .
drwxr-xr-x 26 julien julien 4096 Mar 17 14:20 ..
-rw-r--r--  1 julien julien    8 Mar 17 14:20 .agent_role
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 config
-rw-r--r--  1 julien julien  977 Mar 17 14:23 config.yaml
drwxr-xr-x  5 julien julien 4096 Mar 17 14:23 data
drwxr-xr-x  2 julien julien 4096 Mar 17 14:21 docs
-rw-r--r--  1 julien julien  727 Mar 17 14:25 environment.yml
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 experiments
drwxr-xr-x  7 julien julien 4096 Mar 17 14:25 .git
drwxr-xr-x  3 julien julien 4096 Mar 17 14:20 .github
-rw-r--r--  1 julien julien    4 Mar 17 14:20 .gitignore
--
## OpenCode Output

```
[0m
> build · stepfun/step-3.5-flash:free
[0m
I'll complete the task of establishing project structure and implementing the baseline model. Let me start by exploring the current state and then creating what's needed.
[0m$ [0mfind . -type f -name "*.py" -o -name "*.md" -o -name "*.txt" -o -name "*.yaml" -o -name "*.yml" | head -30
```

**Guidance:** Continue from where we left off. Don't re-do work already done. Focus on the next incomplete piece.


## CURRENT PROJECT STATE (Iteration 8)

```
# mlflow-ai-experiment
**Mission:** Use MLFlow to compare all state of the art ML models on some domain of your choice

## Phase 1: Planning & Setup
- [x] Define specific domain and problem: Select text classification domain using IMDB movie reviews dataset for sentiment analysis, document requirements and success criteria
  - Deliverable: `docs/problem-statement.md` with dataset choice, evaluation metrics (accuracy, F1, inference time), and baseline expectations
- [x] Set up MLFlow tracking infrastructure: Configure MLFlow tracking URI (local directory or Docker), initialize experiments, create project structure
  - Deliverable: `mlruns/` directory with tracking configured, `setup_mlflow.py` script, and `config.yaml` for experiment parameters
- [x] Create development environment: Create `requirements.txt` with core dependencies (mlflow, transformers, datasets, torch/tensorflow, scikit-learn, pandas, numpy) and set up virtual environment
  - Deliverable: `requirements.txt` file, `environment.yml` (conda) or `pyproject.toml`, and verified working environment with all packages installed
- [ ] Establish project structure and baseline: Create organized directory layout (`src/`, `data/`, `models/`, `experiments/`, ` notebooks/`) and implement a simple baseline model (e.g., TF-IDF + Logistic Regression)
  - Deliverable: Complete folder structure with `src/baseline.py`, baseline training script that logs to MLFlow, and initial baseline metrics documented

## Phase 2: Data Management & Preprocessing
- [ ] Download and prepare dataset: Download IMDB dataset using HuggingFace `datasets` library, perform initial exploration, and create standardized train/validation/test splits
  - Deliverable: `data/` folder with processed splits (`train.csv`, `validation.csv`, `test.csv`), `src/data_loader.py` with dataset handling, and data exploration notebook `notebooks/01_data_exploration.ipynb`
- [ ] Implement text preprocessing pipeline: Create modular preprocessing functions for tokenization, padding, and cleaning; implement different tokenization strategies for classical ML vs. transformers
  - Deliverable: `src/preprocessing.py` with configurable pipelines, `src/tokenizers.py` for BERT/RoBERTa/DistilBERT tokenizers, and tests in `tests/test_preprocessing.py`
- [ ] Create data utilities for MLFlow logging: Implement data versioning approach and utilities to log dataset statistics, splits, and preprocessing parameters to MLFlow
  - Deliverable: `src/data_utils.py` with functions to log data artifacts and metrics, `src/data_versioning.py` with checksum-based versioning, and updated data loading scripts
- [ ] Benchmark data pipeline performance: Measure and log data loading times, preprocessing throughput, and memory usage for different batch sizes
  - Deliverable: Performance benchmark script `scripts/benchmark_data.py`, performance results logged to MLFlow, and optimization recommendations in `docs/data_performance.md`

## Phase 3: Model Implementation & Training
- [ ] Implement HuggingFace transformer integration: Create wrapper classes for transformer models (BERT, RoBERTa, DeBERTa, XLNet) with unified interface, supporting custom heads for classification
  - Deliverable: `src/models/transformers.py` with model factory pattern, individual model classes for each architecture, and configuration handling
- [ ] Build classical ML model implementations: Implement traditional models (Logistic Regression, SVM, Random Forest, XGBoost) using scikit-learn and compare against transformers
  - Deliverable: `src/models/classical.py` with all classical model implementations, hyperparameter tuning configurations, and comparison baseline script
- [ ] Implement state-of-the-art models beyond transformers: Add cutting-edge models like ELECTRA, ALBERT, DistilBERT, and potentially GPT-based classifiers to ensure comprehensive coverage
  - Deliverable: Extended `src/models/transformers.py` with additional models, model zoo configuration in `config/models.yaml`, and training scripts for each model family
- [ ] Create unified training pipeline: Implement modular training loop with logging, checkpointing, early stopping, mixed precision training, and support for both PyTorch and TensorFlow backends
  - Deliverable: `src/training.py` with complete training pipeline, `src/train.py` CLI, configuration schema in `config/training_schema.yaml`, and comprehensive documentation

## Phase 4: Experimentation, Logging & Analysis
- [ ] Set up comprehensive MLFlow experiment tracking: Create separate experiments for each model family, implement custom MLFlow tags (model_type, dataset_version, preprocessing_config), and enable artifact logging for models and predictions
  - Deliverable: `src/experiment_tracker.py` with experiment management functions, automated tagging system, and artifact storage structure in `artifacts/`
- [ ] Design hyperparameter optimization framework: Integrate Optuna or Ray Tune with MLFlow for automated hyperparameter search across all models, define search spaces for each model architecture
  - Deliverable: `src/hyperopt.py` with optimization loops, search space definitions in `config/hyperparams/`, script `scripts/run_hyperopt.py`, and example results
- [ ] Implement automated model evaluation suite: Create evaluation script that computes all metrics (accuracy, precision, recall, F1, confusion matrix, inference latency, memory footprint) and logs them consistently
  - Deliverable: `src/evaluation.py` with comprehensive metrics calculation, `scripts/evaluate_all.py` for batch evaluation, standardized MLFlow metrics naming, and comparison tables generation
- [ ] Build analysis and visualization dashboards: Create Jupyter notebooks and Streamlit/Plotly Dash app for interactive comparison of all models, metric correlation analysis, and statistical significance testing
  - Deliverable: Interactive dashboard `app/dashboard.py` or `notebooks/analysis.ipynb`, comparison visualizations (bar charts, ROC curves, latency vs accuracy plots), statistical test results in `docs/model_comparison.md`
- [ ] Generate final report and recommendations: Compile comprehensive comparison report with best-performing models per metric, computational cost analysis, and deployment recommendations
  - Deliverable: Final report `docs/FINAL_REPORT.md` with executive summary, detailed model comparison tables, deployment guidelines, `models/best_models/` directory with top 3 models saved, and reproducibility checklist

## Additional Considerations
- [ ] Ensure reproducibility: Implement deterministic training where possible, log all random seeds, dependency versions, and hardware specifications
  - Deliverable: `src/reproducibility.py` with seed management, complete environment logging to MLFlow, and reproducibility documentation
- [ ] Implement model artifact management: Create standardized model packaging (ONNX conversion where applicable), versioning scheme, and export formats for deployment
  - Deliverable: Model export utilities in `src/export.py`, standardized artifact structure, and deployment instructions in `docs/deployment.md`
```
```

## NEXT TASK TO COMPLETE:
Establish project structure and baseline: Create organized directory layout (`src/`, `data/`, `models/`, `experiments/`, ` notebooks/`) and implement a simple baseline model (e.g., TF-IDF + Logistic Regression)

**Instructions:** Complete this task. Mark [x] in TASKS.md when done. Create, modify, or delete files as needed. Execute commands as needed. Also update README.md to match this project (name, setup instructions, current progress). No permission needed—just act.
```

## OpenCode Output

```
[0m
> build · stepfun/step-3.5-flash:free
[0m
I'll complete the task of establishing project structure and implementing the baseline model. Let me first explore what exists and then create the necessary components.
[0m→ [0mRead TASKS.md
[0m
[0m$ [0mls -la
total 128
drwxr-xr-x 15 julien julien 4096 Mar 17 14:25 .
drwxr-xr-x 26 julien julien 4096 Mar 17 14:20 ..
-rw-r--r--  1 julien julien    8 Mar 17 14:20 .agent_role
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 config
-rw-r--r--  1 julien julien  977 Mar 17 14:23 config.yaml
drwxr-xr-x  5 julien julien 4096 Mar 17 14:23 data
drwxr-xr-x  2 julien julien 4096 Mar 17 14:21 docs
-rw-r--r--  1 julien julien  727 Mar 17 14:25 environment.yml
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 experiments
drwxr-xr-x  7 julien julien 4096 Mar 17 14:28 .git
drwxr-xr-x  3 julien julien 4096 Mar 17 14:20 .github
-rw-r--r--  1 julien julien    4 Mar 17 14:20 .gitignore
drwxr-xr-x  2 julien julien 4096 Mar 17 14:28 logs
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 mlruns
drwxr-xr-x  4 julien julien 4096 Mar 17 14:23 models
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 notebooks
-rw-r--r--  1 julien julien 9218 Mar 17 14:20 prompt.txt
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 __pycache__
-rw-r--r--  1 julien julien 4692 Mar 17 14:25 README.md
-rw-r--r--  1 julien julien  792 Mar 17 14:21 requirements.txt
drwxr-xr-x  3 julien julien 4096 Mar 17 14:23 .ruff_cache
-rw-r--r--  1 julien julien 2484 Mar 17 14:23 setup_mlflow.py
drwxr-xr-x  6 julien julien 4096 Mar 17 14:26 src
-rw-r--r--  1 julien julien 7114 Mar 17 14:25 TASKS.md
-rw-r--r--  1 julien julien 7114 Mar 17 14:20 TASKS_original.md
-rw-r--r--  1 julien julien 2157 Mar 17 14:25 verify_environment.py
-rw-r--r--  1 julien julien    6 Mar 17 14:20 .worker_persistent_mode
[0m
[0m$ [0mfind . -type d | sort
.
./config
./data
./data/external
./data/processed
./data/raw
./docs
./experiments
./.git
./.git/hooks
./.github
./.github/workflows
./.git/info
./.git/logs
./.git/logs/refs
./.git/logs/refs/heads
./.git/logs/refs/remotes
./.git/logs/refs/remotes/origin
./.git/objects
./.git/objects/00
./.git/objects/01
./.git/objects/08
./.git/objects/0a
./.git/objects/0f
./.git/objects/10
./.git/objects/16
./.git/objects/17
./.git/objects/1b
./.git/objects/1e
./.git/objects/1f
./.git/objects/22
./.git/objects/25
./.git/objects/2e
./.git/objects/35
./.git/objects/39
./.git/objects/3d
./.git/objects/3e
./.git/objects/43
./.git/objects/44
./.git/objects/46
./.git/objects/48
./.git/objects/60
./.git/objects/67
./.git/objects/6a
./.git/objects/6b
./.git/objects/71
./.git/objects/74
./.git/objects/76
./.git/objects/77
./.git/objects/79
./.git/objects/7a
./.git/objects/87
./.git/objects/8c
./.git/objects/8d
./.git/objects/8e
./.git/objects/90
./.git/objects/91
./.git/objects/92
./.git/objects/93
./.git/objects/99
./.git/objects/9e
./.git/objects/a0
./.git/objects/a3
./.git/objects/a4
./.git/objects/a6
./.git/objects/a7
./.git/objects/a8
./.git/objects/aa
./.git/objects/ac
./.git/objects/b6
./.git/objects/bf
./.git/objects/c5
./.git/objects/cc
./.git/objects/cd
./.git/objects/ce
./.git/objects/d3
./.git/objects/d9
./.git/objects/df
./.git/objects/e1
./.git/objects/e2
./.git/objects/e3
./.git/objects/e4
./.git/objects/e5
./.git/objects/e8
./.git/objects/ec
./.git/objects/f2
./.git/objects/f8
./.git/objects/fb
./.git/objects/fc
./.git/objects/info
./.git/objects/pack
./.git/refs
./.git/refs/heads
./.git/refs/remotes
./.git/refs/remotes/origin
./.git/refs/tags
./logs
./mlruns
./models
./models/classical
./models/transformers
./notebooks
./__pycache__
./.ruff_cache
./.ruff_cache/0.15.6
./src
./src/evaluation
./src/models
./src/training
./src/utils
[0m
[0m$ [0mfind src -type f -name "*.py" | head -20
src/baseline.py
[0m
[0m→ [0mRead requirements.txt
[0m→ [0mRead config.yaml
Let me check what's already in the src/ directory and read key configuration files:
[0m→ [0mRead README.md
[0m→ [0mRead src/baseline.py
[0m→ [0mRead docs/problem-statement.md
[0m
[0m$ [0mfind src -type f
src/baseline.py
[0m
Let me check the existing baseline.py and explore the src directory structure more thoroughly:
[0m$ [0mls -la data/
total 20
drwxr-xr-x  5 julien julien 4096 Mar 17 14:23 .
drwxr-xr-x 15 julien julien 4096 Mar 17 14:25 ..
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 external
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 processed
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 raw
[0m
[0m$ [0mls -la src/
total 32
drwxr-xr-x  6 julien julien 4096 Mar 17 14:26 .
drwxr-xr-x 15 julien julien 4096 Mar 17 14:25 ..
-rw-r--r--  1 julien julien 6249 Mar 17 14:26 baseline.py
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 evaluation
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 models
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 training
drwxr-xr-x  2 julien julien 4096 Mar 17 14:23 utils
[0m
[0m$ [0mfind . -maxdepth 2 -type f -name "*.py" | grep -v __pycache__ | sort
./setup_mlflow.py
./src/baseline.py
./verify_environment.py
[0m
Let me explore the data directory and check for existing training scripts or data loaders:
```

## TASKS.md After Iteration

```markdown
# mlflow-ai-experiment
**Mission:** Use MLFlow to compare all state of the art ML models on some domain of your choice

## Phase 1: Planning & Setup
- [x] Define specific domain and problem: Select text classification domain using IMDB movie reviews dataset for sentiment analysis, document requirements and success criteria
  - Deliverable: `docs/problem-statement.md` with dataset choice, evaluation metrics (accuracy, F1, inference time), and baseline expectations
- [x] Set up MLFlow tracking infrastructure: Configure MLFlow tracking URI (local directory or Docker), initialize experiments, create project structure
  - Deliverable: `mlruns/` directory with tracking configured, `setup_mlflow.py` script, and `config.yaml` for experiment parameters
- [x] Create development environment: Create `requirements.txt` with core dependencies (mlflow, transformers, datasets, torch/tensorflow, scikit-learn, pandas, numpy) and set up virtual environment
  - Deliverable: `requirements.txt` file, `environment.yml` (conda) or `pyproject.toml`, and verified working environment with all packages installed
- [ ] Establish project structure and baseline: Create organized directory layout (`src/`, `data/`, `models/`, `experiments/`, ` notebooks/`) and implement a simple baseline model (e.g., TF-IDF + Logistic Regression)
  - Deliverable: Complete folder structure with `src/baseline.py`, baseline training script that logs to MLFlow, and initial baseline metrics documented

## Phase 2: Data Management & Preprocessing
- [ ] Download and prepare dataset: Download IMDB dataset using HuggingFace `datasets` library, perform initial exploration, and create standardized train/validation/test splits
  - Deliverable: `data/` folder with processed splits (`train.csv`, `validation.csv`, `test.csv`), `src/data_loader.py` with dataset handling, and data exploration notebook `notebooks/01_data_exploration.ipynb`
- [ ] Implement text preprocessing pipeline: Create modular preprocessing functions for tokenization, padding, and cleaning; implement different tokenization strategies for classical ML vs. transformers
  - Deliverable: `src/preprocessing.py` with configurable pipelines, `src/tokenizers.py` for BERT/RoBERTa/DistilBERT tokenizers, and tests in `tests/test_preprocessing.py`
- [ ] Create data utilities for MLFlow logging: Implement data versioning approach and utilities to log dataset statistics, splits, and preprocessing parameters to MLFlow
  - Deliverable: `src/data_utils.py` with functions to log data artifacts and metrics, `src/data_versioning.py` with checksum-based versioning, and updated data loading scripts
- [ ] Benchmark data pipeline performance: Measure and log data loading times, preprocessing throughput, and memory usage for different batch sizes
  - Deliverable: Performance benchmark script `scripts/benchmark_data.py`, performance results logged to MLFlow, and optimization recommendations in `docs/data_performance.md`

## Phase 3: Model Implementation & Training
- [ ] Implement HuggingFace transformer integration: Create wrapper classes for transformer models (BERT, RoBERTa, DeBERTa, XLNet) with unified interface, supporting custom heads for classification
  - Deliverable: `src/models/transformers.py` with model factory pattern, individual model classes for each architecture, and configuration handling
- [ ] Build classical ML model implementations: Implement traditional models (Logistic Regression, SVM, Random Forest, XGBoost) using scikit-learn and compare against transformers
  - Deliverable: `src/models/classical.py` with all classical model implementations, hyperparameter tuning configurations, and comparison baseline script
- [ ] Implement state-of-the-art models beyond transformers: Add cutting-edge models like ELECTRA, ALBERT, DistilBERT, and potentially GPT-based classifiers to ensure comprehensive coverage
  - Deliverable: Extended `src/models/transformers.py` with additional models, model zoo configuration in `config/models.yaml`, and training scripts for each model family
- [ ] Create unified training pipeline: Implement modular training loop with logging, checkpointing, early stopping, mixed precision training, and support for both PyTorch and TensorFlow backends
  - Deliverable: `src/training.py` with complete training pipeline, `src/train.py` CLI, configuration schema in `config/training_schema.yaml`, and comprehensive documentation

## Phase 4: Experimentation, Logging & Analysis
- [ ] Set up comprehensive MLFlow experiment tracking: Create separate experiments for each model family, implement custom MLFlow tags (model_type, dataset_version, preprocessing_config), and enable artifact logging for models and predictions
  - Deliverable: `src/experiment_tracker.py` with experiment management functions, automated tagging system, and artifact storage structure in `artifacts/`
- [ ] Design hyperparameter optimization framework: Integrate Optuna or Ray Tune with MLFlow for automated hyperparameter search across all models, define search spaces for each model architecture
  - Deliverable: `src/hyperopt.py` with optimization loops, search space definitions in `config/hyperparams/`, script `scripts/run_hyperopt.py`, and example results
- [ ] Implement automated model evaluation suite: Create evaluation script that computes all metrics (accuracy, precision, recall, F1, confusion matrix, inference latency, memory footprint) and logs them consistently
  - Deliverable: `src/evaluation.py` with comprehensive metrics calculation, `scripts/evaluate_all.py` for batch evaluation, standardized MLFlow metrics naming, and comparison tables generation
- [ ] Build analysis and visualization dashboards: Create Jupyter notebooks and Streamlit/Plotly Dash app for interactive comparison of all models, metric correlation analysis, and statistical significance testing
  - Deliverable: Interactive dashboard `app/dashboard.py` or `notebooks/analysis.ipynb`, comparison visualizations (bar charts, ROC curves, latency vs accuracy plots), statistical test results in `docs/model_comparison.md`
- [ ] Generate final report and recommendations: Compile comprehensive comparison report with best-performing models per metric, computational cost analysis, and deployment recommendations
  - Deliverable: Final report `docs/FINAL_REPORT.md` with executive summary, detailed model comparison tables, deployment guidelines, `models/best_models/` directory with top 3 models saved, and reproducibility checklist

## Additional Considerations
- [ ] Ensure reproducibility: Implement deterministic training where possible, log all random seeds, dependency versions, and hardware specifications
  - Deliverable: `src/reproducibility.py` with seed management, complete environment logging to MLFlow, and reproducibility documentation
- [ ] Implement model artifact management: Create standardized model packaging (ONNX conversion where applicable), versioning scheme, and export formats for deployment
  - Deliverable: Model export utilities in `src/export.py`, standardized artifact structure, and deployment instructions in `docs/deployment.md`
```
```

**Completed at:** Tue Mar 17 02:29:46 PM EDT 2026
