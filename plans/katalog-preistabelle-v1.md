# Price table (Hausart × Zimmer × Budget) on the Grundriss-Katalog

Status: DONE, LIVE 2026-11-07 (Snippet 12)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07, on the price page table (preislogik-konfigurator): "that one i need" … "on the grundrisskatalog site".

## Proposal

- New generator `scripts/katalog-preistabelle-snippet.py` writes `wordpress/katalog-preistabelle.php` (a new Code Snippet).
- On the Grundriss-Katalog, below the countdown, a folding box „Preislogik: Häuser je Hausart, Zimmer und Budget“ holds:
  - the factor slider (1,0–1,6, default 1,3) with the buttons 1,0 / 1,2 / 1,3 / 1,4 / „heute“;
  - the table Hausart × Zimmer × three budget columns; red = 0.
- Same calculation as the boss page:
  - market price = m² × 0.8 × rate (Bungalow 2700, 1,5-Geschosser 2500, 2-Geschosser 2650) × factor;
  - „heute“ = matrix price (3000 €/m²).
- Data: konfigurator-matrix.csv, snapshot taken when the generator runs.
- **Only for logged-in editors** (`edit_posts`); internal price logic, not for customers.
- Snippets 9, 10 and 11 stay untouched.

## Tests (first)

`scripts/katalog_preistabelle_snippet.test.py`:
- Hausart mapping incl. Zweifamilienhaus;
- rate type B/A/Z;
- the admin check is in the PHP;
- no backslash, backtick or `${` in the output.

## Rollback

Deactivate or delete the snippet.

## Live

- Snippet 12 „Katalog-Preistabelle (nur Bearbeiter)“, SHA 6db114dbf598 = local file; code read in via a file input, not typed by hand.
- Live, logged in: folding box below the countdown, factor 1,30. Zweifamilienhaus: 3 Zi 0/0/0, 4 Zi 0/1/0, 5 Zi 0/1/2. Logged out: no table in the HTML.
- Refresh: `python scripts/katalog-preistabelle-snippet.py`, then replace the code in Snippet 12.
- 2026-11-07 Rainer "put a price behind that": the factor line shows €/m² Wohnfläche per type. Snippet 12 6db114dbf598 → fa175445631e (live check OK); boss page v3 republished.
