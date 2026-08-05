# Recovery-Safe Baseline and Persistent Follow-Up Plan

Status: APPROVED - approved by the user on 2026-07-31.

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Fix two related failures:

1. Make unfinished and out-of-scope follow-up work persist in a repository roadmap instead of disappearing when a task is closed.
2. Create a tested, recovery-safe baseline for the current Born2Thrill, Workbench, Simplifier, and WordPress source without mixing private floorplan data into source backups.

No backup, Git initialization, commit, push, cleanup, deletion, encryption change, or external action is approved by this Phase 1 plan.

## Current evidence

Inspection date: 2026-07-31 (Europe/Berlin).

### Existing backup

C:\dev\backups\2026-07-30-zuhausefinder contains:

- born2thrill-app-1261604.bundle - valid complete Git bundle;
- zuhausefinder-wordpress-1fc4225.bundle - valid complete Git bundle;
- floorplan-simplifier-structured.zip - 1,940 entries.

The Workbench bundle is four commits behind the current Workbench HEAD.
The WordPress bundle is one commit behind the current WordPress HEAD.

The Simplifier ZIP contains:

- 1,807 entries under projects/;
- 11 entries under exports/;
- 91 entries under .codex/;
- source files, tests, and static assets;
- no PDF entries, image entries, or .env entries detected.

Windows reports this ZIP as unencrypted. No 7z, age, or GPG executable is currently installed. BitLocker status could not be verified without administrator access.

Conclusion: the backup is useful and must not be deleted, but it is outdated and mixes source with private structured corpus and local Codex state.

### Repository baselines

Deployable Born2Thrill:
- C:\dev\born2thrill-app-repo
- branch fix/customer-floorplan-output
- HEAD a595ae37d3d6a2e01a35468cb66e4eb6bc756ee5
- origin https://github.com/raineryeary-lab/born2thrill-app.git
- existing untracked Next server logs and governance Markdown.

Local Workbench:
- C:\dev\born2thrill-local-workbench
- branch agent/zuhausefinder-generator
- HEAD 0c3255fa3f4d4d9c53dd5a5735078dc07e89c633
- origin https://github.com/raineryeary-lab/born2thrill-app.git
- substantial existing tracked and untracked application, dataset, and correction-workbench changes.

Floorplan Simplifier:
- C:\dev\floorplan-simplifier
- not a Git repository;
- source and private local corpus currently share one directory;
- .gitignore already excludes .codex, projects, packages, exports, failed uploads, environments, and secrets;
- reports, logs, and .bak files need explicit exclusion before Git initialization.

ZuhauseFinder WordPress:
- C:\dev\zuhausefinder-wordpress
- branch agent/restore-hausprofil-wohnharmonie
- HEAD d9df2b3ab3b70324d3bbe1b08e10a6ed6a296d84
- origin https://github.com/raineryeary-lab/zuhausefinder-wordpress.git
- existing untracked artifacts and governance Markdown.

## Exact implementation scope after approval

### A. Persistent task tracking

1. Create the canonical suite roadmap at:
   C:\dev\born2thrill-app-repo\plans\ROADMAP.md
2. Add the recovery baseline as P0 and record known follow-ups without changing their implementation state.
3. Add a completion rule to the four root AGENTS.md files and the canonical agent workflow:
   - before a task is marked complete, every unfinished in-scope item and known out-of-scope follow-up must be recorded in the roadmap;
   - excluding work from one plan never removes it from the roadmap;
   - the final report must name the next pending task or explicitly state that none remains.
4. Do not create competing roadmap files in every repository.

### B. New dated source-only recovery set

Create a new explicit directory under C:\dev\backups with a timestamp and a manifest. It may contain only:

- verified Git bundles for committed history from the three Git repositories;
- source-working-tree snapshots that preserve current uncommitted and untracked source changes;
- a source-only Simplifier snapshot;
- SHA-256 checksums;
- an inventory and restore instructions.

Every source snapshot must exclude:

- .git directories from ZIP snapshots;
- node_modules, .next, caches, tmp, logs, build output, dependencies, and virtual environments;
- .env files, credentials, keys, tokens, connection strings, and local Codex state;
- raw floorplans, previews, customer information, private annotations, projects, packages, exports, failed uploads, reports, generated artifacts, and WordPress artifacts;
- existing backup and rollback directories.

Git bundles may contain committed repository history only. They may not silently substitute for the dirty working-tree snapshots.

### C. Simplifier source-only Git baseline

1. Extend C:\dev\floorplan-simplifier\.gitignore to exclude:
   - reports/;
   - server logs and other *.log files;
   - *.bak;
   - generated backup output.
2. Inspect the candidate allowlist before staging.
3. Initialize Git locally in C:\dev\floorplan-simplifier only after the source-only ZIP has passed verification.
4. Stage source through an explicit allowlist. Never use git add . or a recursive broad add.
5. Candidate tracked source:
   - app.py;
   - static/;
   - scripts/;
   - tests/;
   - architectural-rules.json;
   - README.md, REFERENCE_STYLE.md, SHARED_WORKSPACE.md;
   - AGENTS.md, CLAUDE.md, plans/TEMPLATE.md;
   - requirements.txt, run.sh, Start-Floorplan-Simplifier.ps1;
   - .gitignore.
6. Show the staged file list and exclusion proof before any commit.
7. An initial local commit requires the user's separate explicit commit authorization.
8. Creating or pushing a remote repository is not authorized by this plan.

### D. Recovery verification

Restore each source snapshot and Git bundle into a newly created temporary directory under C:\dev\backups\restore-tests, never over an active project.

Verify:

- every Git bundle with git bundle verify;
- every archive against its SHA-256 manifest;
- no forbidden path or extension appears in source snapshots;
- the Simplifier source restore contains app.py, static, scripts, and tests but no protected corpus directories;
- the restored Simplifier source passes the existing 64-test suite using the documented Windows Python runtime;
- the Workbench source restore can install no new dependency during this task, but its package and required source files are present;
- WordPress restored PHP files pass the available syntax check if PHP is already installed;
- restore tests do not connect to external services or use secrets.

Delete restore-test copies only if their exact paths are validated and the plan execution explicitly reaches the cleanup step. Backup artifacts themselves remain.

### E. Private corpus decision

Do not create another private-corpus archive until an at-rest protection method is confirmed.

Allowed later choices require explicit user selection:

- confirmed BitLocker-protected local or external drive;
- an encrypted archive with a user-controlled recovery key;
- another user-approved encrypted offline destination.

Do not install encryption software, enable EFS, alter BitLocker, upload the corpus, move the existing ZIP, or delete the existing ZIP under this plan.

## Files and paths likely to change

Governance and tracking:
- C:\dev\born2thrill-app-repo\AGENTS.md
- C:\dev\born2thrill-app-repo\docs\agent-workflow.md
- C:\dev\born2thrill-app-repo\plans\ROADMAP.md
- C:\dev\born2thrill-local-workbench\AGENTS.md
- C:\dev\floorplan-simplifier\AGENTS.md
- C:\dev\zuhausefinder-wordpress\AGENTS.md
- this plan file only for approval/status records.

Simplifier baseline:
- C:\dev\floorplan-simplifier\.gitignore
- C:\dev\floorplan-simplifier\.git metadata only after source snapshot verification and explicit authorization.
- No Simplifier application source content is changed.

Backup output:
- one new dated directory under C:\dev\backups.
- one optional restore-tests directory with exact validated child paths.

If another repository file is needed, stop and revise this plan.

## Explicitly out of scope

- Application behavior, schemas, geometry, generators, rendering, matching, UI, WordPress workflow, email, database, deployment, DNS, Railway, and OpenAI configuration.
- Editing any test or application source file.
- Committing Workbench, app, or WordPress dirty changes.
- Pushing any branch or creating a GitHub repository.
- Copying any backup to Google Drive.
- Deleting, replacing, moving, or encrypting the existing 30 July backup.
- Backing up private corpus data before the encryption destination is explicitly selected.
- Installing dependencies or encryption utilities.
- Git clean, git reset --hard, broad git restore, stash, checkout of another branch, or destructive cleanup.

## Acceptance criteria

1. ROADMAP.md exists and lists this recovery baseline as P0 until every approved recovery criterion is complete.
2. All four AGENTS.md files require persistent follow-up recording before task completion.
3. A new dated source-only backup set exists on C: with SHA-256 manifest and restore instructions.
4. Current Git histories are captured at the exact inspected heads.
5. Current source-working-tree changes are captured without secrets, dependencies, logs, build output, raw floorplans, protected annotations, generated artifacts, or private corpus directories.
6. The Simplifier source is separately recoverable and passes its full 64-test suite after restoration.
7. Simplifier Git ignore rules protect every private/local path before Git initialization.
8. The candidate Simplifier staged file list contains only the approved allowlist.
9. No commit occurs without separate commit authorization and no push occurs.
10. The existing backup remains untouched.
11. No active working directory file is overwritten during restore verification.
12. Final reporting identifies every remaining roadmap item; no known follow-up disappears when this task closes.

## Tests and verification commands

Read-only or newly created backup verification only:

- git status --short and git rev-parse HEAD in each Git repository;
- git bundle verify for every bundle;
- Get-FileHash -Algorithm SHA256 for every backup artifact;
- archive-entry policy scan for forbidden paths and extensions;
- restore into exact new temporary child directories;
- documented Simplifier Python unittest command;
- php -l only when PHP is already available;
- git diff --check for governance Markdown;
- git status --short after all work to prove original dirty changes remain.

No production build, deployment, network write, live email, or database test is authorized.

## Protected paths

- C:\dev\floorplan-simplifier\projects
- C:\dev\floorplan-simplifier\packages
- C:\dev\floorplan-simplifier\exports
- C:\dev\floorplan-simplifier\failed-uploads
- C:\dev\floorplan-simplifier\reports
- C:\dev\born2thrill-local-workbench-data
- all .env files, secrets, credentials, active databases, WordPress artifacts, and external systems
- C:\dev\backups\2026-07-30-zuhausefinder

Protected paths may be inventoried by metadata only but not read for content, copied, moved, deleted, uploaded, committed, or repackaged during this plan.

## Failed-hypothesis circuit breaker

Record each distinct failure with command, output, and conclusion. Stop after three distinct root-cause hypotheses. Repeated permission or environment failures count once.

Known environment limitation:
- BitLocker status returned access denied without administrative rights. Do not repeat that check automatically.

## Rollback

- Governance changes: restore only the named AGENTS.md and canonical workflow files; remove only the newly added ROADMAP.md.
- Simplifier: if Git was initialized but no commit was authorized, stop and ask before removing .git because that is destructive.
- Backup output: do not delete a completed verified backup automatically. Mark it superseded in the manifest if a replacement is later approved.
- Never use git clean, git reset --hard, broad restore, recursive deletion of C:\dev\backups, or removal of an active project.

## Unresolved decisions

1. Private corpus at-rest protection. BitLocker could not be verified and no archive encryption tool is installed.
2. Whether the user separately authorizes the first local Simplifier source commit after reviewing the allowlist.
3. Whether a private remote for Simplifier source should be planned later. No remote is created or pushed in this task.

These decisions do not block creation of the source-only backup and roadmap, but they block a fully encrypted private-corpus backup and any Simplifier commit/push.

## Approval record

Approved by the user on 2026-07-31 for source-only backups, persistent roadmap tracking, and local Simplifier Git initialization/staging. No commit or push is authorized.

