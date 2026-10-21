# Contractor Intelligence V5 — local prototype

A clean, light-themed management dashboard built for **job-type and client comparisons**, recorded job loss investigations, statistical screening, and source-backed reporting.

## Install on Mac

1. Download and unzip the package into Downloads.
2. Open Terminal and run:

```bash
cd "$HOME/Downloads/contractor_intelligence_v5"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Open the local address printed by Streamlit, normally http://localhost:8501. Stop a previous Streamlit app with Control+C first.

## Where to start

- **Overview:** key job figures and management warnings.
- **Compare job types:** turnover, contribution, margins, labour overruns, and drill-down job lists.
- **Compare clients:** profitability, losses, overruns, outstanding and overdue invoices, and client-specific job records.
- **Investigate jobs:** cost breakdown, recorded overrun flags, timesheets.
- **Find patterns:** minimum sample-size screening and Benjamini–Hochberg correction. This is exploratory, not causal.
- **Ask a question:** limited supported question menu with deterministic answers, **not free-form AI chat**.
- **Data & connections:** inspect/export raw tables and identify gaps.

## Important limitations

**All included example data is fictional.** This is not a verified business report. The import option accepts ten **standardised** CSVs matching the bundled demo schemas; it does not yet parse arbitrary simPRO or Xero exports. No simPRO, Joblogic, Xero or other live API integration exists. No automatic cross-system matching approval workflow, persistent database, user authentication, production security, or free-form AI chat is implemented. These remain outstanding V5 acceptance criteria.

Job contribution is quoted revenue plus approved variations minus imported hourly-rate labour, materials, subcontractors and other direct job costs. Imported hourly rates may omit employment on-costs. It is **not** accounting revenue recognition, company operating profit, net profit or taxable profit. The app does not fabricate missing data, overhead allocations or tax liabilities. Demo overhead entries are synthetic source rows, not invented during calculations.

The client invoice table includes all source invoices for each client, while job profitability comparisons are filtered to completed jobs with required direct records. These are different scopes and should not be interpreted as a reconciled profit-and-loss statement. Provider exports may contain errors and require independent verification.

The statistical screen uses two-proportion z-tests on groups of at least 12 jobs against the rest, followed by Benjamini–Hochberg false discovery rate correction. Group differences can reflect job mix, scope, timing and other confounding factors; no cause is established.

## Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## V5 remaining milestones before a client pilot

- Actual simPRO and Xero export parsers, field mapping and staging tables
- Explicit duplicate checks and reviewed cross-system matching
- Audit trail and durable, client-separated data storage
- Tested accounting reconciliation and data completeness rules
- Free-form question answering grounded in source records (if deployed)
- Secure authentication, permissions and API authorisation
- User testing and source-to-dashboard reconciliation with consented real data
