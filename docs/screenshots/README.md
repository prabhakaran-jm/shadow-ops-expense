# Screenshots for submission

Capture these views from the Shadow Ops dashboard for hackathon submission. Place the image files in this directory and reference them in the main [README](../../README.md#screenshots) table.

| # | Description | Suggested filename |
|---|-------------|--------------------|
| 1 | **Dashboard – workflow list** – Home view showing the list of inferred workflows (e.g. "Submit expense (inferred)") and selection. | `01-dashboard-workflow-list.png` |
| 2 | **Workflow detail** – Single workflow view with parameters (amount, date, category, etc.) and steps (navigate, open form, upload receipt, fill fields, submit, confirmation). | `02-workflow-detail.png` |
| 3 | **Run Agent modal** – The "Run Agent" / Execute modal with the parameter form filled (e.g. amount, date, category, description, receipt file) and optional "Simulate UI change" checkbox. | `03-run-agent-modal.png` |
| 4 | **Run result** – After a run completes: confirmation ID (e.g. EXP-2026-000123), run ID, and the full run log. | `04-run-result.png` |
| 5 | **Run log with UI-change adaptation** – Same run result view after a run *with* "Simulate UI change" enabled, with the self-healing lines highlighted (e.g. "Step failed: element not found", "UI changed: Submit renamed to Confirm", "Step retry: Click Confirm"). | `05-run-log-adaptation.png` |

**Tips**

- Use a clean browser window and consistent viewport (e.g. 1280×720 or 1920×1080).
- For #5, run the agent once with "Simulate UI change" checked and capture the result panel so the adaptation lines are visible in the run log.
