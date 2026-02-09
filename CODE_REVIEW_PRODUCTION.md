# Code Review: Production Branch (`master`)
Date: 2026-02-09
Focus: Deployment Structure

## 1. Overview
The `master` branch is configured as a **clean release branch**. It contains only the generated static artifacts, documentation, and assets required for hosting the application (e.g., via GitHub Pages). All source code, data processing scripts, and raw databases are intentionally excluded.

## 2. Architecture & File Structure
*   **`docs/` Directory:** Serves as the web root. Contains the generated HTML maps (`GebaeudebrueterMultiMarkers.html`, `GebaeudebrueterMeldungen.html`).
    *   *Verdict:* Standard practice for GitHub Pages hosting.
*   **Exclusion of Source:** Python scripts (`scripts/`), SQLite databases, and CSV reports are removed.
    *   *Verdict:* Excellent for security and clarity. Reduces the risk of accidentally publishing raw data or WIP scripts.

## 3. Deployment Artifacts
The HTML files are **Self-Contained Static Exports**.
*   **Strengths:**
    *   No backend required (zero maintenance hosting).
    *   Fast load times (served purely as static files).
    *   Robust (maps work offline/locally if map tiles are cached or if internet is available for tiles).
*   **Observations:**
    *   Data is embedded directly into the HTML/JS. This means `git diffs` on these files are large and difficult to read.
    *   Updates require a full regeneration of the HTML files on the development branch (`feature/multi-species-markers-v2`) and a merge/copy to master.

## 4. Recommendations
1.  **Documentation:** Ensure `README.md` explicitly states: *"This branch contains compiled files only. For checking out source code and generator scripts, switch to the `feature/multi-species-markers-v2` branch."*
2.  **Automation:** Consider a GitHub Action in the future that auto-deploys the `docs/` folder from the feature branch to `master` (or a `gh-pages` branch) to automate the manual merge/copy process.

## 5. Summary
The `master` branch is in an optimal state for a static site deployment. It is clean, minimal, and focused solely on delivery.
