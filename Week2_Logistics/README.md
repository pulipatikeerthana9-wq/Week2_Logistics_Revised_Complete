# Week 2 — Logistics Data Collection, Cleaning and Preprocessing

## What you need to run
1. Extract `Week2_Logistics_Complete.zip` first. Do not run files inside the ZIP preview.
2. Open the extracted `Week2_Logistics` folder.
3. Install Python 3.10 or newer if needed (https://www.python.org/downloads/). Enable **Add Python to PATH**. Internet is needed for the first dependency installation.
4. Double-click **RUN_WEEK2.bat**. It creates `.venv`, installs requirements, runs 12 tests, runs `preprocessing.py`, then runs `analysis_summary.py`.
5. Wait for **SUCCESS**. The generated files are in **results**.

**You do not need your old preprocessing.py or analysis_summary.py.** Use the new files in this folder. No extra model, notebook, or dashboard is required for this Week 2 brief.

The package includes results from an actual complete-data run. Rerunning replaces those result files. It does not update the Word report automatically; if you change the input data or methodology, update the report to match your new results.

## Manual alternative (Windows Command Prompt)
Open Command Prompt in this folder and run:
```bat
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe preprocessing.py
.venv\Scripts\python.exe analysis_summary.py
```
If `py` is unavailable but Python is on PATH, use `python -m venv .venv` for the first command.

## Folder contents
- `Week2_Logistics_Report.docx`: Word submission report with dataset findings, code excerpts, methodology and references.
- `preprocessing.py`: complete cleaning, checks, IQR flags, scaling and order KPI pipeline.
- `analysis_summary.py`: displays the generated summary.
- `RUN_WEEK2.bat`: Windows launcher.
- `requirements.txt`: pandas, NumPy and scikit-learn dependencies.
- `tests/test_pipeline.py`: 12 automated tests (small real-data sample plus deliberately altered test cases).
- `data/raw/DataCoSupplyChainDataset.csv`: your supplied original dataset, unchanged.
- `results/DataCoSupplyChain_Cleaned.csv`: 180,519 rows, 58 columns, original units retained.
- `results/DataCoSupplyChain_Normalized.csv`: same records, plus 3 `_minmax` columns (61 columns).
- `results/missing_values.csv`: raw-column before/after missingness and exclusions.
- `results/outlier_summary.csv`: IQR thresholds and counts; flagged records were not deleted.
- `results/order_summary.csv`: 65,752 unique orders for shipping KPIs.
- `results/audit_summary.json`: quality counts, input checksum and environment versions.
- `results/scaler_parameters.json`: descriptive scaling minima and maxima.
- `results/analysis_summary.json`: grain-aware logistics KPIs.
- `results/test_results.txt`: test evidence from the packaged run (launcher prints current test results to the console).

## Submission checklist
1. Read the report and ensure you understand the choices. Add your name/intern ID if the platform requires them; no identity was guessed in the report.
2. Run the folder yourself and check the SUCCESS message. Capture your own console screenshot if the internship accepts evidence; no screenshot is required by the supplied brief.
3. Submit `Week2_Logistics_Report.docx` as the Word deliverable. If the platform strictly requires legacy `.doc` rather than `.docx`, open it in Word and use Save As → Word 97–2003 Document; check formatting afterward.
4. If the platform asks for GitHub, upload the code, README, requirements, tests, report and small audit files. Do not upload `.venv`, `__pycache__` or credentials. Review the dataset's customer-related fields before publishing raw or processed datasets; keep the raw copy private by default and use a source link instead. Nothing has been submitted or published for you.
5. Update any reflection wording to match what you personally learned and disclose assistance if your internship rules require it.

## Important analytical choices
- Rows are order items, not orders. Unique Order Id is used for order-level delivery KPIs.
- Canceled shipments are excluded from the non-canceled shipping KPI denominator.
- Postal codes are strings. Missing values are Unknown with separate indicators; median imputation is inappropriate.
- Source tokens such as `725` are preserved. Lost leading zeros in the original file cannot be reconstructed safely without an authoritative location reference.
- No core numeric values are missing in this file. New missing core values trigger investigation rather than silently changing KPI inputs.
- Valid extreme sales and negative profit ratios are retained and flagged.
- Min–max scaling is descriptive and fitted on the full dataset. For later predictive modeling, split by time with orders kept together; fit transformations only on training data. Exclude actual shipping outcomes and delivery labels from pre-shipment features.
- Direct customer names, email, password and street are excluded from curated outputs, but retained IDs and geography mean the outputs are NOT guaranteed anonymous.

## Data attribution
Constante, F.; Silva, F.; Pereira, A. (2019). *DataCo SMART SUPPLY CHAIN FOR BIG DATA ANALYSIS*. Mendeley Data, V5. DOI: https://doi.org/10.17632/8gx2fvg2k6.5. Public source: https://data.mendeley.com/datasets/8gx2fvg2k6/5. CC BY 4.0. Derived cleaning and feature additions are described in the report. Analysis used the supplied CSV; this is simulated collection, not a claim of extracting live company systems.

## Verification boundary
The Python pipeline and all tests were executed on Linux with Python 3.13.13, pandas 2.2.3, NumPy 2.3.5 and scikit-learn 1.6.1. The Windows launcher was prepared for Command Prompt but not executed on your laptop. Dependency versions installed on your machine may differ within the declared compatible ranges. No score is guaranteed.
