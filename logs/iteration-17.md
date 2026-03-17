# Iteration 17 - mlflow-ai-experiment

**Timestamp:** Tue Mar 17 02:47:11 PM EDT 2026
**Task:** Implement text preprocessing pipeline: Create modular preprocessing functions for tokenization, padding, and cleaning; implement different tokenization strategies for classical ML vs. transformers

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
- Iteration: 17 / 64k Token Budget
- Attempt: 1 (previous attempts may have partial progress)
- **Mandate:** Operate efficiently. Use partial edits, not full file rewrites when possible.
- **Output:** Be concise and action-oriented.


## CURRENT PROJECT STATE (Iteration 17)

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
- [x] Establish project structure and baseline: Create organized directory layout (`src/`, `data/`, `models/`, `experiments/`, ` notebooks/`) and implement a simple baseline model (e.g., TF-IDF + Logistic Regression)
  - Deliverable: Complete folder structure with `src/baseline.py`, baseline training script that logs to MLFlow, and initial baseline metrics documented

## Phase 2: Data Management & Preprocessing
- [x] Download and prepare dataset: Download IMDB dataset using HuggingFace `datasets` library, perform initial exploration, and create standardized train/validation/test splits
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
Implement text preprocessing pipeline: Create modular preprocessing functions for tokenization, padding, and cleaning; implement different tokenization strategies for classical ML vs. transformers

**Instructions:** Complete this task. Mark [x] in TASKS.md when done. Create, modify, or delete files as needed. Execute commands as needed. Also update README.md to match this project (name, setup instructions, current progress). No permission needed—just act.
```

## OpenCode Output

```
[0m
> build · stepfun/step-3.5-flash:free
[0m
[0m→ [0mRead .
[0m✱ [0mGlob "**/*.py"[90m 14 matches[0m
[0m✱ [0mGlob "**/TASKS.md"[90m 1 match[0m
I'll implement the text preprocessing pipeline. Let me start by examining the current project structure and understanding what needs to be built.
[0m→ [0mRead src/preprocessing.py
[0m→ [0mRead src/tokenizers.py
[0m→ [0mRead requirements.txt
[0m→ [0mRead tests/test_preprocessing.py
[0m→ [0mRead src/data_loader.py
The preprocessing pipeline is already well-implemented! Let me examine the data loader to ensure compatibility and then run tests to verify everything works correctly.
Now let me run the preprocessing tests to verify everything works correctly:
[0m
[0m$ [0mpython -m pytest tests/test_preprocessing.py -v
============================= test session starts ==============================
platform linux -- Python 3.14.3, pytest-9.0.2, pluggy-1.6.0 -- /home/julien/Desktop/Free-Wiggum-opencode/venv/bin/python
cachedir: .pytest_cache
rootdir: /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment
plugins: langsmith-0.7.16, anyio-4.12.1, asyncio-1.3.0, cov-7.0.0, mock-3.15.1, dash-4.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 26 items

tests/test_preprocessing.py::TestCleanText::test_lowercase PASSED        [  3%]
tests/test_preprocessing.py::TestCleanText::test_remove_html PASSED      [  7%]
tests/test_preprocessing.py::TestCleanText::test_remove_extra_whitespace PASSED [ 11%]
tests/test_preprocessing.py::TestCleanText::test_strip PASSED            [ 15%]
tests/test_preprocessing.py::TestCleanText::test_combined PASSED         [ 19%]
tests/test_preprocessing.py::TestTFIDFFeatures::test_create_tfidf_features FAILED [ 23%]
tests/test_preprocessing.py::TestTFIDFFeatures::test_feature_names_length FAILED [ 26%]
tests/test_preprocessing.py::TestTFIDFFeatures::test_fit_on_train_only FAILED [ 30%]
tests/test_preprocessing.py::TestTFIDFFeatures::test_no_validation FAILED [ 34%]
tests/test_preprocessing.py::TestPreprocessClassical::test_preprocess_classical FAILED [ 38%]
tests/test_preprocessing.py::TestPreprocessClassical::test_cleaned_text_column_added FAILED [ 42%]
tests/test_preprocessing.py::TestPreprocessClassical::test_custom_parameters FAILED [ 46%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenizer_initialization PASSED [ 50%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenize_basic PASSED [ 53%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenize_with_padding PASSED [ 57%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenize_truncation PASSED [ 61%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenize_return_tensors PASSED [ 65%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_decode PASSED [ 69%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_supported_models PASSED [ 73%]
tests/test_preprocessing.py::TestPreprocessTransformer::test_preprocess_transformer_bert FAILED [ 76%]
tests/test_preprocessing.py::TestPreprocessTransformer::test_preprocess_transformer_batch_size PASSED [ 80%]
tests/test_preprocessing.py::TestPreprocessTransformer::test_unsupported_model_fails PASSED [ 84%]
tests/test_preprocessing.py::TestPreprocessDataset::test_preprocess_classical_mode FAILED [ 88%]
tests/test_preprocessing.py::TestPreprocessDataset::test_preprocess_transformer_mode FAILED [ 92%]
tests/test_preprocessing.py::TestPreprocessDataset::test_invalid_mode_raises PASSED [ 96%]
tests/test_preprocessing.py::TestPreprocessDataset::test_mode_parameter_passed FAILED [100%]

=================================== FAILURES ===================================
_________________ TestTFIDFFeatures.test_create_tfidf_features _________________

self = <test_preprocessing.TestTFIDFFeatures object at 0x7f986193e710>
sample_data = (['This is a positive review', 'Negative experience', 'Great movie', 'Good acting and directing', 'I loved this film',...tory', 'Poor character development'], ['Excellent acting', 'Bad direction', 'A compelling narrative', 'Weak dialogue'])

    def test_create_tfidf_features(self, sample_data):
        train_texts, val_texts, test_texts = sample_data
>       result = create_tfidf_features(
            train_texts, val_texts, test_texts, max_features=100, ngram_range=(1, 1)
        )

tests/test_preprocessing.py:89: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/preprocessing.py:54: in create_tfidf_features
    X_train = vectorizer.fit_transform(train_texts)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:2104: in fit_transform
    X = super().fit_transform(raw_documents)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/base.py:1336: in wrapper
    return fit_method(estimator, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1399: in fit_transform
    X = self._limit_features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = TfidfVectorizer(max_df=0.7, max_features=100, min_df=5, stop_words='english')
X = <Compressed Sparse Row sparse matrix of dtype 'float64'
	with 32 stored elements and shape (15, 32)>
vocabulary = {}, high = 10.5, low = 5, limit = 100

    def _limit_features(self, X, vocabulary, high=None, low=None, limit=None):
        """Remove too rare or too common features.
    
        Prune features that are non zero in more samples than high or less
        documents than low, modifying the vocabulary, and restricting it to
        at most the limit most frequent.
    
        This does not prune samples with zero features.
        """
        if high is None and low is None and limit is None:
            return X, set()
    
        # Calculate a mask based on document frequencies
        dfs = _document_frequency(X)
        mask = np.ones(len(dfs), dtype=bool)
        if high is not None:
            mask &= dfs <= high
        if low is not None:
            mask &= dfs >= low
        if limit is not None and mask.sum() > limit:
            tfs = np.asarray(X.sum(axis=0)).ravel()
            mask_inds = (-tfs[mask]).argsort()[:limit]
            new_mask = np.zeros(len(dfs), dtype=bool)
            new_mask[np.where(mask)[0][mask_inds]] = True
            mask = new_mask
    
        new_indices = np.cumsum(mask) - 1  # maps old indices to new
        for term, old_index in list(vocabulary.items()):
            if mask[old_index]:
                vocabulary[term] = new_indices[old_index]
            else:
                del vocabulary[term]
        kept_indices = np.where(mask)[0]
        if len(kept_indices) == 0:
>           raise ValueError(
                "After pruning, no terms remain. Try a lower min_df or a higher max_df."
            )
E           ValueError: After pruning, no terms remain. Try a lower min_df or a higher max_df.

../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1251: ValueError
_________________ TestTFIDFFeatures.test_feature_names_length __________________

self = <test_preprocessing.TestTFIDFFeatures object at 0x7f986193e990>
sample_data = (['This is a positive review', 'Negative experience', 'Great movie', 'Good acting and directing', 'I loved this film',...tory', 'Poor character development'], ['Excellent acting', 'Bad direction', 'A compelling narrative', 'Weak dialogue'])

    def test_feature_names_length(self, sample_data):
        train_texts, _, _ = sample_data
>       result = create_tfidf_features(train_texts, max_features=10)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_preprocessing.py:105: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/preprocessing.py:54: in create_tfidf_features
    X_train = vectorizer.fit_transform(train_texts)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:2104: in fit_transform
    X = super().fit_transform(raw_documents)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/base.py:1336: in wrapper
    return fit_method(estimator, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1399: in fit_transform
    X = self._limit_features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = TfidfVectorizer(max_df=0.7, max_features=10, min_df=5, ngram_range=(1, 2),
                stop_words='english')
X = <Compressed Sparse Row sparse matrix of dtype 'float64'
	with 49 stored elements and shape (15, 49)>
vocabulary = {}, high = 10.5, low = 5, limit = 10

    def _limit_features(self, X, vocabulary, high=None, low=None, limit=None):
        """Remove too rare or too common features.
    
        Prune features that are non zero in more samples than high or less
        documents than low, modifying the vocabulary, and restricting it to
        at most the limit most frequent.
    
        This does not prune samples with zero features.
        """
        if high is None and low is None and limit is None:
            return X, set()
    
        # Calculate a mask based on document frequencies
        dfs = _document_frequency(X)
        mask = np.ones(len(dfs), dtype=bool)
        if high is not None:
            mask &= dfs <= high
        if low is not None:
            mask &= dfs >= low
        if limit is not None and mask.sum() > limit:
            tfs = np.asarray(X.sum(axis=0)).ravel()
            mask_inds = (-tfs[mask]).argsort()[:limit]
            new_mask = np.zeros(len(dfs), dtype=bool)
            new_mask[np.where(mask)[0][mask_inds]] = True
            mask = new_mask
    
        new_indices = np.cumsum(mask) - 1  # maps old indices to new
        for term, old_index in list(vocabulary.items()):
            if mask[old_index]:
                vocabulary[term] = new_indices[old_index]
            else:
                del vocabulary[term]
        kept_indices = np.where(mask)[0]
        if len(kept_indices) == 0:
>           raise ValueError(
                "After pruning, no terms remain. Try a lower min_df or a higher max_df."
            )
E           ValueError: After pruning, no terms remain. Try a lower min_df or a higher max_df.

../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1251: ValueError
___________________ TestTFIDFFeatures.test_fit_on_train_only ___________________

self = <test_preprocessing.TestTFIDFFeatures object at 0x7f98616d90f0>
sample_data = (['This is a positive review', 'Negative experience', 'Great movie', 'Good acting and directing', 'I loved this film',...tory', 'Poor character development'], ['Excellent acting', 'Bad direction', 'A compelling narrative', 'Weak dialogue'])

    def test_fit_on_train_only(self, sample_data):
        """Test that vectorizer is fitted only on training data."""
        train_texts, val_texts, _ = sample_data
>       result = create_tfidf_features(train_texts, val_texts)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_preprocessing.py:111: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/preprocessing.py:54: in create_tfidf_features
    X_train = vectorizer.fit_transform(train_texts)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:2104: in fit_transform
    X = super().fit_transform(raw_documents)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/base.py:1336: in wrapper
    return fit_method(estimator, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1399: in fit_transform
    X = self._limit_features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = TfidfVectorizer(max_df=0.7, max_features=5000, min_df=5, ngram_range=(1, 2),
                stop_words='english')
X = <Compressed Sparse Row sparse matrix of dtype 'float64'
	with 49 stored elements and shape (15, 49)>
vocabulary = {}, high = 10.5, low = 5, limit = 5000

    def _limit_features(self, X, vocabulary, high=None, low=None, limit=None):
        """Remove too rare or too common features.
    
        Prune features that are non zero in more samples than high or less
        documents than low, modifying the vocabulary, and restricting it to
        at most the limit most frequent.
    
        This does not prune samples with zero features.
        """
        if high is None and low is None and limit is None:
            return X, set()
    
        # Calculate a mask based on document frequencies
        dfs = _document_frequency(X)
        mask = np.ones(len(dfs), dtype=bool)
        if high is not None:
            mask &= dfs <= high
        if low is not None:
            mask &= dfs >= low
        if limit is not None and mask.sum() > limit:
            tfs = np.asarray(X.sum(axis=0)).ravel()
            mask_inds = (-tfs[mask]).argsort()[:limit]
            new_mask = np.zeros(len(dfs), dtype=bool)
            new_mask[np.where(mask)[0][mask_inds]] = True
            mask = new_mask
    
        new_indices = np.cumsum(mask) - 1  # maps old indices to new
        for term, old_index in list(vocabulary.items()):
            if mask[old_index]:
                vocabulary[term] = new_indices[old_index]
            else:
                del vocabulary[term]
        kept_indices = np.where(mask)[0]
        if len(kept_indices) == 0:
>           raise ValueError(
                "After pruning, no terms remain. Try a lower min_df or a higher max_df."
            )
E           ValueError: After pruning, no terms remain. Try a lower min_df or a higher max_df.

../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1251: ValueError
_____________________ TestTFIDFFeatures.test_no_validation _____________________

self = <test_preprocessing.TestTFIDFFeatures object at 0x7f98616d9220>
sample_data = (['This is a positive review', 'Negative experience', 'Great movie', 'Good acting and directing', 'I loved this film',...tory', 'Poor character development'], ['Excellent acting', 'Bad direction', 'A compelling narrative', 'Weak dialogue'])

    def test_no_validation(self, sample_data):
        train_texts, _, test_texts = sample_data
>       result = create_tfidf_features(train_texts, test_texts=test_texts)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_preprocessing.py:118: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/preprocessing.py:54: in create_tfidf_features
    X_train = vectorizer.fit_transform(train_texts)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:2104: in fit_transform
    X = super().fit_transform(raw_documents)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/base.py:1336: in wrapper
    return fit_method(estimator, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1399: in fit_transform
    X = self._limit_features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = TfidfVectorizer(max_df=0.7, max_features=5000, min_df=5, ngram_range=(1, 2),
                stop_words='english')
X = <Compressed Sparse Row sparse matrix of dtype 'float64'
	with 49 stored elements and shape (15, 49)>
vocabulary = {}, high = 10.5, low = 5, limit = 5000

    def _limit_features(self, X, vocabulary, high=None, low=None, limit=None):
        """Remove too rare or too common features.
    
        Prune features that are non zero in more samples than high or less
        documents than low, modifying the vocabulary, and restricting it to
        at most the limit most frequent.
    
        This does not prune samples with zero features.
        """
        if high is None and low is None and limit is None:
            return X, set()
    
        # Calculate a mask based on document frequencies
        dfs = _document_frequency(X)
        mask = np.ones(len(dfs), dtype=bool)
        if high is not None:
            mask &= dfs <= high
        if low is not None:
            mask &= dfs >= low
        if limit is not None and mask.sum() > limit:
            tfs = np.asarray(X.sum(axis=0)).ravel()
            mask_inds = (-tfs[mask]).argsort()[:limit]
            new_mask = np.zeros(len(dfs), dtype=bool)
            new_mask[np.where(mask)[0][mask_inds]] = True
            mask = new_mask
    
        new_indices = np.cumsum(mask) - 1  # maps old indices to new
        for term, old_index in list(vocabulary.items()):
            if mask[old_index]:
                vocabulary[term] = new_indices[old_index]
            else:
                del vocabulary[term]
        kept_indices = np.where(mask)[0]
        if len(kept_indices) == 0:
>           raise ValueError(
                "After pruning, no terms remain. Try a lower min_df or a higher max_df."
            )
E           ValueError: After pruning, no terms remain. Try a lower min_df or a higher max_df.

../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1251: ValueError
______________ TestPreprocessClassical.test_preprocess_classical _______________

self = <test_preprocessing.TestPreprocessClassical object at 0x7f986193efd0>
sample_dataframes = (                        text  label              cleaned_text
0                Good movie!      1               good ...d the ending
4        Best film ever      1        best film ever
5           Worst movie      0           worst movie)

    def test_preprocess_classical(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
>       result = preprocess_classical(train_df, val_df, test_df, max_features=100)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_preprocessing.py:194: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/preprocessing.py:151: in preprocess_classical
    features = create_tfidf_features(
src/preprocessing.py:54: in create_tfidf_features
    X_train = vectorizer.fit_transform(train_texts)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:2104: in fit_transform
    X = super().fit_transform(raw_documents)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/base.py:1336: in wrapper
    return fit_method(estimator, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1399: in fit_transform
    X = self._limit_features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = TfidfVectorizer(max_df=0.7, max_features=100, min_df=5, ngram_range=(1, 2),
                stop_words='english')
X = <Compressed Sparse Row sparse matrix of dtype 'float64'
	with 46 stored elements and shape (16, 46)>
vocabulary = {}, high = 11.2, low = 5, limit = 100

    def _limit_features(self, X, vocabulary, high=None, low=None, limit=None):
        """Remove too rare or too common features.
    
        Prune features that are non zero in more samples than high or less
        documents than low, modifying the vocabulary, and restricting it to
        at most the limit most frequent.
    
        This does not prune samples with zero features.
        """
        if high is None and low is None and limit is None:
            return X, set()
    
        # Calculate a mask based on document frequencies
        dfs = _document_frequency(X)
        mask = np.ones(len(dfs), dtype=bool)
        if high is not None:
            mask &= dfs <= high
        if low is not None:
            mask &= dfs >= low
        if limit is not None and mask.sum() > limit:
            tfs = np.asarray(X.sum(axis=0)).ravel()
            mask_inds = (-tfs[mask]).argsort()[:limit]
            new_mask = np.zeros(len(dfs), dtype=bool)
            new_mask[np.where(mask)[0][mask_inds]] = True
            mask = new_mask
    
        new_indices = np.cumsum(mask) - 1  # maps old indices to new
        for term, old_index in list(vocabulary.items()):
            if mask[old_index]:
                vocabulary[term] = new_indices[old_index]
            else:
                del vocabulary[term]
        kept_indices = np.where(mask)[0]
        if len(kept_indices) == 0:
>           raise ValueError(
                "After pruning, no terms remain. Try a lower min_df or a higher max_df."
            )
E           ValueError: After pruning, no terms remain. Try a lower min_df or a higher max_df.

../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1251: ValueError
____________ TestPreprocessClassical.test_cleaned_text_column_added ____________

self = <test_preprocessing.TestPreprocessClassical object at 0x7f986193f110>
sample_dataframes = (                        text  label              cleaned_text
0                Good movie!      1               good ...d the ending
4        Best film ever      1        best film ever
5           Worst movie      0           worst movie)

    def test_cleaned_text_column_added(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
>       result = preprocess_classical(train_df, val_df, test_df)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_preprocessing.py:209: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/preprocessing.py:151: in preprocess_classical
    features = create_tfidf_features(
src/preprocessing.py:54: in create_tfidf_features
    X_train = vectorizer.fit_transform(train_texts)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:2104: in fit_transform
    X = super().fit_transform(raw_documents)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/base.py:1336: in wrapper
    return fit_method(estimator, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1399: in fit_transform
    X = self._limit_features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = TfidfVectorizer(max_df=0.7, max_features=5000, min_df=5, ngram_range=(1, 2),
                stop_words='english')
X = <Compressed Sparse Row sparse matrix of dtype 'float64'
	with 46 stored elements and shape (16, 46)>
vocabulary = {}, high = 11.2, low = 5, limit = 5000

    def _limit_features(self, X, vocabulary, high=None, low=None, limit=None):
        """Remove too rare or too common features.
    
        Prune features that are non zero in more samples than high or less
        documents than low, modifying the vocabulary, and restricting it to
        at most the limit most frequent.
    
        This does not prune samples with zero features.
        """
        if high is None and low is None and limit is None:
            return X, set()
    
        # Calculate a mask based on document frequencies
        dfs = _document_frequency(X)
        mask = np.ones(len(dfs), dtype=bool)
        if high is not None:
            mask &= dfs <= high
        if low is not None:
            mask &= dfs >= low
        if limit is not None and mask.sum() > limit:
            tfs = np.asarray(X.sum(axis=0)).ravel()
            mask_inds = (-tfs[mask]).argsort()[:limit]
            new_mask = np.zeros(len(dfs), dtype=bool)
            new_mask[np.where(mask)[0][mask_inds]] = True
            mask = new_mask
    
        new_indices = np.cumsum(mask) - 1  # maps old indices to new
        for term, old_index in list(vocabulary.items()):
            if mask[old_index]:
                vocabulary[term] = new_indices[old_index]
            else:
                del vocabulary[term]
        kept_indices = np.where(mask)[0]
        if len(kept_indices) == 0:
>           raise ValueError(
                "After pruning, no terms remain. Try a lower min_df or a higher max_df."
            )
E           ValueError: After pruning, no terms remain. Try a lower min_df or a higher max_df.

../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1251: ValueError
________________ TestPreprocessClassical.test_custom_parameters ________________

self = <test_preprocessing.TestPreprocessClassical object at 0x7f98616d9810>
sample_dataframes = (                        text  label              cleaned_text
0                Good movie!      1               good ...d the ending
4        Best film ever      1        best film ever
5           Worst movie      0           worst movie)

    def test_custom_parameters(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
>       result = preprocess_classical(
            train_df, val_df, test_df, max_features=50, ngram_range=(1, 3)
        )

tests/test_preprocessing.py:217: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/preprocessing.py:151: in preprocess_classical
    features = create_tfidf_features(
src/preprocessing.py:54: in create_tfidf_features
    X_train = vectorizer.fit_transform(train_texts)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:2104: in fit_transform
    X = super().fit_transform(raw_documents)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/base.py:1336: in wrapper
    return fit_method(estimator, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1399: in fit_transform
    X = self._limit_features(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = TfidfVectorizer(max_df=0.7, max_features=50, min_df=5, ngram_range=(1, 3),
                stop_words='english')
X = <Compressed Sparse Row sparse matrix of dtype 'float64'
	with 47 stored elements and shape (16, 47)>
vocabulary = {}, high = 11.2, low = 5, limit = 50

    def _limit_features(self, X, vocabulary, high=None, low=None, limit=None):
        """Remove too rare or too common features.
    
        Prune features that are non zero in more samples than high or less
        documents than low, modifying the vocabulary, and restricting it to
        at most the limit most frequent.
    
        This does not prune samples with zero features.
        """
        if high is None and low is None and limit is None:
            return X, set()
    
        # Calculate a mask based on document frequencies
        dfs = _document_frequency(X)
        mask = np.ones(len(dfs), dtype=bool)
        if high is not None:
            mask &= dfs <= high
        if low is not None:
            mask &= dfs >= low
        if limit is not None and mask.sum() > limit:
            tfs = np.asarray(X.sum(axis=0)).ravel()
            mask_inds = (-tfs[mask]).argsort()[:limit]
            new_mask = np.zeros(len(dfs), dtype=bool)
            new_mask[np.where(mask)[0][mask_inds]] = True
            mask = new_mask
    
        new_indices = np.cumsum(mask) - 1  # maps old indices to new
        for term, old_index in list(vocabulary.items()):
            if mask[old_index]:
                vocabulary[term] = new_indices[old_index]
            else:
                del vocabulary[term]
        kept_indices = np.where(mask)[0]
        if len(kept_indices) == 0:
>           raise ValueError(
                "After pruning, no terms remain. Try a lower min_df or a higher max_df."
            )
E           ValueError: After pruning, no terms remain. Try a lower min_df or a higher max_df.

../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1251: ValueError
__________ TestPreprocessTransformer.test_preprocess_transformer_bert __________

self = <test_preprocessing.TestPreprocessTransformer object at 0x7f986193f4d0>
sample_dataframes = (                        text  label
0                Good movie!      1
1                Bad film...      0
2        ...ved the characters      1
3      Hated the ending      0
4        Best film ever      1
5           Worst movie      0)

    def test_preprocess_transformer_bert(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        result = preprocess_transformer(
            train_df, val_df, test_df, model_name="bert", max_length=32
        )
    
        assert "train" in result
        assert "val" in result
        assert "test" in result
        assert "tokenizer" in result
    
        # Check inputs exist
        for split in ["train", "val", "test"]:
            assert "input_ids" in result[split]
            assert "attention_mask" in result[split]
            assert "labels" in result[split]
    
            # Check labels
>           assert torch.equal(
                result[split]["labels"],
                torch.tensor(
                    [1, 0]
                    if split == "train"
                    else ([1, 0] if split == "val" else [1, 0])
                ),
            )
E           assert False
E            +  where False = <built-in method equal of type object at 0x7f9917738a00>(tensor([1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]), tensor([1, 0]))
E            +    where <built-in method equal of type object at 0x7f9917738a00> = torch.equal
E            +    and   tensor([1, 0]) = <built-in method tensor of type object at 0x7f9917738a00>([1, 0])
E            +      where <built-in method tensor of type object at 0x7f9917738a00> = torch.tensor

tests/test_preprocessing.py:365: AssertionError
_____________ TestPreprocessDataset.test_preprocess_classical_mode _____________

self = <test_preprocessing.TestPreprocessDataset object at 0x7f986193f750>
sample_dataframes = (          text  label cleaned_text
0  Good movie!      1  good movie!
1  Bad film...      0  bad film...,            ...      0   poor script,        text  label cleaned_text
0  Loved it      1     loved it
1  Hated it      0     hated it)

    def test_preprocess_classical_mode(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
>       result = preprocess_dataset(train_df, val_df, test_df, mode="classical")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_preprocessing.py:411: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/preprocessing.py:191: in preprocess_dataset
    return preprocess_classical(train_df, val_df, test_df, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/preprocessing.py:151: in preprocess_classical
    features = create_tfidf_features(
src/preprocessing.py:54: in create_tfidf_features
    X_train = vectorizer.fit_transform(train_texts)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:2104: in fit_transform
    X = super().fit_transform(raw_documents)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/base.py:1336: in wrapper
    return fit_method(estimator, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = TfidfVectorizer(max_df=0.7, max_features=5000, min_df=5, ngram_range=(1, 2),
                stop_words='english')
raw_documents = ['good movie!', 'bad film...'], y = None

    @_fit_context(prefer_skip_nested_validation=True)
    def fit_transform(self, raw_documents, y=None):
        """Learn the vocabulary dictionary and return document-term matrix.
    
        This is equivalent to fit followed by transform, but more efficiently
        implemented.
    
        Parameters
        ----------
        raw_documents : iterable
            An iterable which generates either str, unicode or file objects.
    
        y : None
            This parameter is ignored.
    
        Returns
        -------
        X : array of shape (n_samples, n_features)
            Document-term matrix.
        """
        # We intentionally don't call the transform method to make
        # fit_transform overridable without unwanted side effects in
        # TfidfVectorizer.
        if isinstance(raw_documents, str):
            raise ValueError(
                "Iterable over raw text documents expected, string object received."
            )
    
        self._validate_ngram_range()
        self._warn_for_unused_params()
        self._validate_vocabulary()
        max_df = self.max_df
        min_df = self.min_df
        max_features = self.max_features
    
        if self.fixed_vocabulary_ and self.lowercase:
            for term in self.vocabulary:
                if any(map(str.isupper, term)):
                    warnings.warn(
                        "Upper case characters found in"
                        " vocabulary while 'lowercase'"
                        " is True. These entries will not"
                        " be matched with any documents"
                    )
                    break
    
        vocabulary, X = self._count_vocab(raw_documents, self.fixed_vocabulary_)
    
        if self.binary:
            X.data.fill(1)
    
        if not self.fixed_vocabulary_:
            n_doc = X.shape[0]
            max_doc_count = max_df if isinstance(max_df, Integral) else max_df * n_doc
            min_doc_count = min_df if isinstance(min_df, Integral) else min_df * n_doc
            if max_doc_count < min_doc_count:
>               raise ValueError("max_df corresponds to < documents than min_df")
E               ValueError: max_df corresponds to < documents than min_df

../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1396: ValueError
____________ TestPreprocessDataset.test_preprocess_transformer_mode ____________

self = <test_preprocessing.TestPreprocessDataset object at 0x7f986193f890>
sample_dataframes = (          text  label
0  Good movie!      1
1  Bad film...      0,            text  label
0  Great acting      1
1   Poor script      0,        text  label
0  Loved it      1
1  Hated it      0)

    def test_preprocess_transformer_mode(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        result = preprocess_dataset(
            train_df,
            val_df,
            test_df,
            mode="transformer",
            model_name="bert",
            max_length=16,
        )
    
        assert "tokenizer" in result
        assert "train" in result
>       assert isinstance(result["train"], dict)
E       AssertionError: assert False
E        +  where False = isinstance({'input_ids': tensor([[ 101, 2204, 3185,  999,  102,    0,    0],\n        [ 101, 2919, 2143, 1012, 1012, 1012,  102]]), 'token_type_ids': tensor([[0, 0, 0, 0, 0, 0, 0],\n        [0, 0, 0, 0, 0, 0, 0]]), 'attention_mask': tensor([[1, 1, 1, 1, 1, 0, 0],\n        [1, 1, 1, 1, 1, 1, 1]]), 'labels': tensor([1, 0])}, dict)

tests/test_preprocessing.py:430: AssertionError
_______________ TestPreprocessDataset.test_mode_parameter_passed _______________

self = <test_preprocessing.TestPreprocessDataset object at 0x7f98616d9e00>
sample_dataframes = (          text  label cleaned_text
0  Good movie!      1  good movie!
1  Bad film...      0  bad film...,            ...      0   poor script,        text  label cleaned_text
0  Loved it      1     loved it
1  Hated it      0     hated it)

    def test_mode_parameter_passed(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
>       result = preprocess_dataset(
            train_df, val_df, test_df, mode="classical", max_features=100
        )

tests/test_preprocessing.py:440: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/preprocessing.py:191: in preprocess_dataset
    return preprocess_classical(train_df, val_df, test_df, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/preprocessing.py:151: in preprocess_classical
    features = create_tfidf_features(
src/preprocessing.py:54: in create_tfidf_features
    X_train = vectorizer.fit_transform(train_texts)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:2104: in fit_transform
    X = super().fit_transform(raw_documents)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../venv/lib/python3.14/site-packages/sklearn/base.py:1336: in wrapper
    return fit_method(estimator, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = TfidfVectorizer(max_df=0.7, max_features=100, min_df=5, ngram_range=(1, 2),
                stop_words='english')
raw_documents = ['good movie!', 'bad film...'], y = None

    @_fit_context(prefer_skip_nested_validation=True)
    def fit_transform(self, raw_documents, y=None):
        """Learn the vocabulary dictionary and return document-term matrix.
    
        This is equivalent to fit followed by transform, but more efficiently
        implemented.
    
        Parameters
        ----------
        raw_documents : iterable
            An iterable which generates either str, unicode or file objects.
    
        y : None
            This parameter is ignored.
    
        Returns
        -------
        X : array of shape (n_samples, n_features)
            Document-term matrix.
        """
        # We intentionally don't call the transform method to make
        # fit_transform overridable without unwanted side effects in
        # TfidfVectorizer.
        if isinstance(raw_documents, str):
            raise ValueError(
                "Iterable over raw text documents expected, string object received."
            )
    
        self._validate_ngram_range()
        self._warn_for_unused_params()
        self._validate_vocabulary()
        max_df = self.max_df
        min_df = self.min_df
        max_features = self.max_features
    
        if self.fixed_vocabulary_ and self.lowercase:
            for term in self.vocabulary:
                if any(map(str.isupper, term)):
                    warnings.warn(
                        "Upper case characters found in"
                        " vocabulary while 'lowercase'"
                        " is True. These entries will not"
                        " be matched with any documents"
                    )
                    break
    
        vocabulary, X = self._count_vocab(raw_documents, self.fixed_vocabulary_)
    
        if self.binary:
            X.data.fill(1)
    
        if not self.fixed_vocabulary_:
            n_doc = X.shape[0]
            max_doc_count = max_df if isinstance(max_df, Integral) else max_df * n_doc
            min_doc_count = min_df if isinstance(min_df, Integral) else min_df * n_doc
            if max_doc_count < min_doc_count:
>               raise ValueError("max_df corresponds to < documents than min_df")
E               ValueError: max_df corresponds to < documents than min_df

../../venv/lib/python3.14/site-packages/sklearn/feature_extraction/text.py:1396: ValueError
=============================== warnings summary ===============================
<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute

<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_preprocessing.py::TestTFIDFFeatures::test_create_tfidf_features
FAILED tests/test_preprocessing.py::TestTFIDFFeatures::test_feature_names_length
FAILED tests/test_preprocessing.py::TestTFIDFFeatures::test_fit_on_train_only
FAILED tests/test_preprocessing.py::TestTFIDFFeatures::test_no_validation - V...
FAILED tests/test_preprocessing.py::TestPreprocessClassical::test_preprocess_classical
FAILED tests/test_preprocessing.py::TestPreprocessClassical::test_cleaned_text_column_added
FAILED tests/test_preprocessing.py::TestPreprocessClassical::test_custom_parameters
FAILED tests/test_preprocessing.py::TestPreprocessTransformer::test_preprocess_transformer_bert
FAILED tests/test_preprocessing.py::TestPreprocessDataset::test_preprocess_classical_mode
FAILED tests/test_preprocessing.py::TestPreprocessDataset::test_preprocess_transformer_mode
FAILED tests/test_preprocessing.py::TestPreprocessDataset::test_mode_parameter_passed
================== 11 failed, 15 passed, 2 warnings in 12.69s ==================
[0m
The tests reveal two issues:
1. TF-IDF uses `min_df=5` which fails on small test datasets
2. HuggingFace tokenizer returns `BatchEncoding` (not a `dict`) causing type check failures

Let me fix these in the code:
[0m← [0mEdit src/preprocessing.py
Index: /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/src/preprocessing.py
===================================================================
--- /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/src/preprocessing.py
+++ /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/src/preprocessing.py
@@ -26,9 +26,14 @@
     return text
 
 
 def create_tfidf_features(
-    train_texts, val_texts=None, test_texts=None, max_features=5000, ngram_range=(1, 2)
+    train_texts,
+    val_texts=None,
+    test_texts=None,
+    max_features=5000,
+    ngram_range=(1, 2),
+    min_df=1,
 ):
     """
     Create TF-IDF features from text data.
 

[0m
[0m← [0mEdit src/preprocessing.py
Index: /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/src/preprocessing.py
===================================================================
--- /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/src/preprocessing.py
+++ /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/src/preprocessing.py
@@ -50,9 +50,9 @@
 vectorizer = TfidfVectorizer(
     max_features=max_features,
     ngram_range=ngram_range,
     stop_words="english",
-    min_df=5,
+    min_df=min_df,
     max_df=0.7,
 )
 
 # Fit on training data only

[0m
[0m→ [0mRead src/preprocessing.py[90m [limit=30, offset=110][0m
[0m→ [0mRead src/preprocessing.py[90m [limit=100, offset=70][0m
Now I'll fix the code to address test failures:

1. Add `min_df` parameter to `create_tfidf_features` with default 1
2. Convert BatchEncoding to dict in `preprocess_transformer`
3. Fix return type annotation
[0m
[0m← [0mEdit src/preprocessing.py
Index: /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/src/preprocessing.py
===================================================================
--- /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/src/preprocessing.py
+++ /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/src/preprocessing.py
@@ -82,9 +82,9 @@
     model_name: str = "bert",
     max_length: int = 512,
     padding: bool = True,
     truncation: bool = True,
-) -> Dict[str, Dict[str, torch.Tensor]]:
+) -> Dict[str, any]:
     """
     Preprocess datasets for transformer models: tokenize text.
 
     Args:

[0m
Now convert BatchEncoding to dict:
[0m← [0mEdit src/preprocessing.py
Index: /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/src/preprocessing.py
===================================================================
--- /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/src/preprocessing.py
+++ /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/src/preprocessing.py
@@ -113,12 +113,18 @@
     val_texts=val_df["text"].tolist(),
     test_texts=test_df["text"].tolist(),
 )
 
-# Add labels to each split
-tokenized["train"]["labels"] = torch.tensor(train_df["label"].values)
-tokenized["val"]["labels"] = torch.tensor(val_df["label"].values)
-tokenized["test"]["labels"] = torch.tensor(test_df["label"].values)
+# Convert BatchEncoding to plain dict and add labels to each split
+for split in ["train", "val", "test"]:
+    tokenized[split] = dict(tokenized[split])
+    tokenized[split]["labels"] = torch.tensor(
+        train_df["label"].values
+        if split == "train"
+        else val_df["label"].values
+        if split == "val"
+        else test_df["label"].values
+    )
 
 return {
     "train": tokenized["train"],
     "val": tokenized["val"],

[0m
Now let's fix the test label checks. I'll update the test file:
[0m← [0mEdit tests/test_preprocessing.py
Index: /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/tests/test_preprocessing.py
===================================================================
--- /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/tests/test_preprocessing.py
+++ /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/tests/test_preprocessing.py
@@ -360,17 +360,16 @@
         assert "input_ids" in result[split]
         assert "attention_mask" in result[split]
         assert "labels" in result[split]
 
-        # Check labels
-        assert torch.equal(
-            result[split]["labels"],
-            torch.tensor(
-                [1, 0]
-                if split == "train"
-                else ([1, 0] if split == "val" else [1, 0])
-            ),
-        )
+        # Check labels match original dataframes
+        if split == "train":
+            expected_labels = torch.tensor(train_df["label"].values)
+        elif split == "val":
+            expected_labels = torch.tensor(val_df["label"].values)
+        else:
+            expected_labels = torch.tensor(test_df["label"].values)
+        assert torch.equal(result[split]["labels"], expected_labels)
 
 def test_preprocess_transformer_batch_size(self, sample_dataframes):
     train_df, val_df, test_df = sample_dataframes
     result = preprocess_transformer(train_df, val_df, test_df, model_name="bert")

[0m
Now let's run the tests again to see if our fixes resolve the failures:
[0m$ [0mpython -m pytest tests/test_preprocessing.py -v
============================= test session starts ==============================
platform linux -- Python 3.14.3, pytest-9.0.2, pluggy-1.6.0 -- /home/julien/Desktop/Free-Wiggum-opencode/venv/bin/python
cachedir: .pytest_cache
rootdir: /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment
plugins: langsmith-0.7.16, anyio-4.12.1, asyncio-1.3.0, cov-7.0.0, mock-3.15.1, dash-4.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 26 items

tests/test_preprocessing.py::TestCleanText::test_lowercase PASSED        [  3%]
tests/test_preprocessing.py::TestCleanText::test_remove_html PASSED      [  7%]
tests/test_preprocessing.py::TestCleanText::test_remove_extra_whitespace PASSED [ 11%]
tests/test_preprocessing.py::TestCleanText::test_strip PASSED            [ 15%]
tests/test_preprocessing.py::TestCleanText::test_combined PASSED         [ 19%]
tests/test_preprocessing.py::TestTFIDFFeatures::test_create_tfidf_features PASSED [ 23%]
tests/test_preprocessing.py::TestTFIDFFeatures::test_feature_names_length PASSED [ 26%]
tests/test_preprocessing.py::TestTFIDFFeatures::test_fit_on_train_only PASSED [ 30%]
tests/test_preprocessing.py::TestTFIDFFeatures::test_no_validation PASSED [ 34%]
tests/test_preprocessing.py::TestPreprocessClassical::test_preprocess_classical FAILED [ 38%]
tests/test_preprocessing.py::TestPreprocessClassical::test_cleaned_text_column_added PASSED [ 42%]
tests/test_preprocessing.py::TestPreprocessClassical::test_custom_parameters PASSED [ 46%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenizer_initialization PASSED [ 50%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenize_basic PASSED [ 53%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenize_with_padding PASSED [ 57%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenize_truncation PASSED [ 61%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenize_return_tensors PASSED [ 65%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_decode PASSED [ 69%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_supported_models PASSED [ 73%]
tests/test_preprocessing.py::TestPreprocessTransformer::test_preprocess_transformer_bert PASSED [ 76%]
tests/test_preprocessing.py::TestPreprocessTransformer::test_preprocess_transformer_batch_size PASSED [ 80%]
tests/test_preprocessing.py::TestPreprocessTransformer::test_unsupported_model_fails PASSED [ 84%]
tests/test_preprocessing.py::TestPreprocessDataset::test_preprocess_classical_mode PASSED [ 88%]
tests/test_preprocessing.py::TestPreprocessDataset::test_preprocess_transformer_mode PASSED [ 92%]
tests/test_preprocessing.py::TestPreprocessDataset::test_invalid_mode_raises PASSED [ 96%]
tests/test_preprocessing.py::TestPreprocessDataset::test_mode_parameter_passed PASSED [100%]

=================================== FAILURES ===================================
______________ TestPreprocessClassical.test_preprocess_classical _______________

self = <test_preprocessing.TestPreprocessClassical object at 0x7faaa44fefd0>
sample_dataframes = (                        text  label              cleaned_text
0                Good movie!      1               good ...d the ending
4        Best film ever      1        best film ever
5           Worst movie      0           worst movie)

    def test_preprocess_classical(self, sample_dataframes):
        train_df, val_df, test_df = sample_dataframes
        result = preprocess_classical(train_df, val_df, test_df, max_features=100)
    
        assert "train" in result
        assert "val" in result
        assert "test" in result
        assert "vectorizer" in result
        assert "feature_names" in result
    
        # Check that labels are preserved
>       assert result["train"][1].tolist() == [1, 0]
E       AssertionError: assert [1, 0, 1, 0, 1, 0, ...] == [1, 0]
E         
E         Left contains 14 more items, first extra item: 1
E         
E         Full diff:
E           [
E               1,
E               0,...
E         
E         ...Full output truncated (15 lines hidden), use '-vv' to show

tests/test_preprocessing.py:203: AssertionError
=============================== warnings summary ===============================
<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute

<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_preprocessing.py::TestPreprocessClassical::test_preprocess_classical
================== 1 failed, 25 passed, 2 warnings in 10.96s ===================
[0m
One more test to fix - it also expects `[1, 0]` but the fixture has many samples:
[0m← [0mEdit tests/test_preprocessing.py
Index: /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/tests/test_preprocessing.py
===================================================================
--- /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/tests/test_preprocessing.py
+++ /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/tests/test_preprocessing.py
@@ -199,11 +199,11 @@
     assert "vectorizer" in result
     assert "feature_names" in result
 
     # Check that labels are preserved
-    assert result["train"][1].tolist() == [1, 0]
-    assert result["val"][1].tolist() == [1, 0]
-    assert result["test"][1].tolist() == [1, 0]
+    assert result["train"][1].tolist() == train_df["label"].tolist()
+    assert result["val"][1].tolist() == val_df["label"].tolist()
+    assert result["test"][1].tolist() == test_df["label"].tolist()
 
 def test_cleaned_text_column_added(self, sample_dataframes):
     train_df, val_df, test_df = sample_dataframes
     result = preprocess_classical(train_df, val_df, test_df)

[0m
Run tests again:
[0m$ [0mpython -m pytest tests/test_preprocessing.py -v
============================= test session starts ==============================
platform linux -- Python 3.14.3, pytest-9.0.2, pluggy-1.6.0 -- /home/julien/Desktop/Free-Wiggum-opencode/venv/bin/python
cachedir: .pytest_cache
rootdir: /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment
plugins: langsmith-0.7.16, anyio-4.12.1, asyncio-1.3.0, cov-7.0.0, mock-3.15.1, dash-4.0.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 26 items

tests/test_preprocessing.py::TestCleanText::test_lowercase PASSED        [  3%]
tests/test_preprocessing.py::TestCleanText::test_remove_html PASSED      [  7%]
tests/test_preprocessing.py::TestCleanText::test_remove_extra_whitespace PASSED [ 11%]
tests/test_preprocessing.py::TestCleanText::test_strip PASSED            [ 15%]
tests/test_preprocessing.py::TestCleanText::test_combined PASSED         [ 19%]
tests/test_preprocessing.py::TestTFIDFFeatures::test_create_tfidf_features PASSED [ 23%]
tests/test_preprocessing.py::TestTFIDFFeatures::test_feature_names_length PASSED [ 26%]
tests/test_preprocessing.py::TestTFIDFFeatures::test_fit_on_train_only PASSED [ 30%]
tests/test_preprocessing.py::TestTFIDFFeatures::test_no_validation PASSED [ 34%]
tests/test_preprocessing.py::TestPreprocessClassical::test_preprocess_classical PASSED [ 38%]
tests/test_preprocessing.py::TestPreprocessClassical::test_cleaned_text_column_added PASSED [ 42%]
tests/test_preprocessing.py::TestPreprocessClassical::test_custom_parameters PASSED [ 46%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenizer_initialization PASSED [ 50%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenize_basic PASSED [ 53%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenize_with_padding PASSED [ 57%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenize_truncation PASSED [ 61%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_tokenize_return_tensors PASSED [ 65%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_decode PASSED [ 69%]
tests/test_preprocessing.py::TestTransformerTokenizer::test_supported_models PASSED [ 73%]
tests/test_preprocessing.py::TestPreprocessTransformer::test_preprocess_transformer_bert PASSED [ 76%]
tests/test_preprocessing.py::TestPreprocessTransformer::test_preprocess_transformer_batch_size PASSED [ 80%]
tests/test_preprocessing.py::TestPreprocessTransformer::test_unsupported_model_fails PASSED [ 84%]
tests/test_preprocessing.py::TestPreprocessDataset::test_preprocess_classical_mode PASSED [ 88%]
tests/test_preprocessing.py::TestPreprocessDataset::test_preprocess_transformer_mode PASSED [ 92%]
tests/test_preprocessing.py::TestPreprocessDataset::test_invalid_mode_raises PASSED [ 96%]
tests/test_preprocessing.py::TestPreprocessDataset::test_mode_parameter_passed PASSED [100%]

=============================== warnings summary ===============================
<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyPacked has no __module__ attribute

<frozen importlib._bootstrap>:491
  <frozen importlib._bootstrap>:491: DeprecationWarning: builtin type SwigPyObject has no __module__ attribute

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 26 passed, 2 warnings in 10.97s ========================
[0m
[0m→ [0mRead README.md
Excellent! All tests pass. Now update README.md with current progress:
I'll update README.md to mark the preprocessing pipeline as completed:
[0m
[0m← [0mEdit README.md
Index: /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/README.md
===================================================================
--- /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/README.md
+++ /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/README.md
@@ -154,18 +154,22 @@
 - [x] Baseline model implementation
   - `src/baseline.py` with TF-IDF + Logistic Regression
   - Project structure complete with `src/`, `data/`, `models/`, `experiments/`, `notebooks/`
 
-**Phase 2: Data Management & Preprocessing** - In Progress
-- [x] Dataset download and preparation
-  - IMDB dataset downloaded using HuggingFace `datasets` library
-  - Train/validation/test splits created (22,501 / 2,501 / 25,001 samples)
-  - Processed files saved in `data/` as CSV
-  - Data exploration notebook: `notebooks/01_data_exploration.ipynb`
-  - Dataset loading utility: `src/data_loader.py`
-- [ ] Text preprocessing pipeline
-- [ ] Data utilities for MLFlow logging
-- [ ] Data pipeline performance benchmarking
+ **Phase 2: Data Management & Preprocessing** - In Progress
+ - [x] Dataset download and preparation
+   - IMDB dataset downloaded using HuggingFace `datasets` library
+   - Train/validation/test splits created (22,501 / 2,501 / 25,001 samples)
+   - Processed files saved in `data/` as CSV
+   - Data exploration notebook: `notebooks/01_data_exploration.ipynb`
+   - Dataset loading utility: `src/data_loader.py`
+ - [x] Text preprocessing pipeline
+   - Modular preprocessing functions: `src/preprocessing.py`
+   - Tokenization strategies for classical ML (TF-IDF) and transformers (BERT, RoBERTa, DistilBERT, etc.)
+   - Unified interface: `preprocess_dataset()` supporting both modes
+   - Comprehensive test suite: `tests/test_preprocessing.py` (26 tests passing)
+ - [ ] Data utilities for MLFlow logging
+ - [ ] Data pipeline performance benchmarking
 
 See [TASKS.md](TASKS.md) for full task list.
 
 ## Dependencies

[0m
[0m→ [0mRead TASKS.md[90m [limit=50][0m
Now let's update TASKS.md to mark the task as completed:
[0m
[0m← [0mEdit TASKS.md
Index: /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/TASKS.md
===================================================================
--- /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/TASKS.md
+++ /home/julien/Desktop/Free-Wiggum-opencode/projects/mlflow-ai-experiment/TASKS.md
@@ -13,10 +13,10 @@
 
 ## Phase 2: Data Management & Preprocessing
 - [x] Download and prepare dataset: Download IMDB dataset using HuggingFace `datasets` library, perform initial exploration, and create standardized train/validation/test splits
   - Deliverable: `data/` folder with processed splits (`train.csv`, `validation.csv`, `test.csv`), `src/data_loader.py` with dataset handling, and data exploration notebook `notebooks/01_data_exploration.ipynb`
-- [ ] Implement text preprocessing pipeline: Create modular preprocessing functions for tokenization, padding, and cleaning; implement different tokenization strategies for classical ML vs. transformers
-  - Deliverable: `src/preprocessing.py` with configurable pipelines, `src/tokenizers.py` for BERT/RoBERTa/DistilBERT tokenizers, and tests in `tests/test_preprocessing.py`
+ - [x] Implement text preprocessing pipeline: Create modular preprocessing functions for tokenization, padding, and cleaning; implement different tokenization strategies for classical ML vs. transformers
+   - Deliverable: `src/preprocessing.py` with configurable pipelines, `src/tokenizers.py` for BERT/RoBERTa/DistilBERT tokenizers, and tests in `tests/test_preprocessing.py`
 - [ ] Create data utilities for MLFlow logging: Implement data versioning approach and utilities to log dataset statistics, splits, and preprocessing parameters to MLFlow
   - Deliverable: `src/data_utils.py` with functions to log data artifacts and metrics, `src/data_versioning.py` with checksum-based versioning, and updated data loading scripts
 - [ ] Benchmark data pipeline performance: Measure and log data loading times, preprocessing throughput, and memory usage for different batch sizes
   - Deliverable: Performance benchmark script `scripts/benchmark_data.py`, performance results logged to MLFlow, and optimization recommendations in `docs/data_performance.md`

[0m
Now commit and push the changes:
[0m$ [0mgit add .
[0m
[0m$ [0mgit commit -m "feat: implement modular text preprocessing pipeline with tokenization strategies for classical ML and transformers"
[main a1e8b50] feat: implement modular text preprocessing pipeline with tokenization strategies for classical ML and transformers
 8 files changed, 4052 insertions(+), 20 deletions(-)
 create mode 100644 logs/iteration-16.md
 create mode 100644 logs/iteration-17.md
 create mode 100644 src/tokenizers.py
 create mode 100644 tests/test_preprocessing.py
[0m
[0m→ [0mRead .gitignore
Let's check if logs should be ignored:
[0m
[0m$ [0mgit push origin main
To https://github.com/Julien-ser/mlflow-ai-experiment.git
   de9cc02..a1e8b50  main -> main
[0m
Task completed: text preprocessing pipeline implemented with modular functions, tokenization strategies for classical ML and transformers, comprehensive tests (26/26 passing), and documentation updated in README.md and TASKS.md.
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
- [x] Establish project structure and baseline: Create organized directory layout (`src/`, `data/`, `models/`, `experiments/`, ` notebooks/`) and implement a simple baseline model (e.g., TF-IDF + Logistic Regression)
  - Deliverable: Complete folder structure with `src/baseline.py`, baseline training script that logs to MLFlow, and initial baseline metrics documented

## Phase 2: Data Management & Preprocessing
- [x] Download and prepare dataset: Download IMDB dataset using HuggingFace `datasets` library, perform initial exploration, and create standardized train/validation/test splits
  - Deliverable: `data/` folder with processed splits (`train.csv`, `validation.csv`, `test.csv`), `src/data_loader.py` with dataset handling, and data exploration notebook `notebooks/01_data_exploration.ipynb`
 - [x] Implement text preprocessing pipeline: Create modular preprocessing functions for tokenization, padding, and cleaning; implement different tokenization strategies for classical ML vs. transformers
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

**Completed at:** Tue Mar 17 02:51:24 PM EDT 2026
