# Commit CI Audit Ledger

Persistent repository-specific record of commit-level CI checks and red-cross investigations.

## How to use this ledger

1. Read this file before auditing commit checks.
2. Check only commits newer than the checkpoint, plus older **red**, **pending**, or explicitly unresolved entries.
3. Record exact commit SHAs and observed results; never infer from missing badges or empty API responses.
4. Preserve failures and append diagnosis, fix, rerun, and final-outcome evidence.
5. Advance the checkpoint only after reviewing the range; carry unresolved entries forward.

## Result meanings

| Result | Meaning |
|---|---|
| **green** | Completed successful check/run directly observed. |
| **red** | Completed failing check/run directly observed. |
| **pending** | Check/run exists but is unfinished. |
| **unavailable** | Available evidence did not expose a result; not a pass or failure. |
| **not applicable** | Workflow configuration confirms no relevant check is triggered. |

## Checkpoint

- Repository: `SakibShahariar/material-bibata-cursor`
- Default branch: `master`
- Checkpoint SHA: `9cdf61663ec3c10b4aaa0ed64a56608b86413573`
- Reviewed: 2026-11-05
- Range: `1de2bbb6c7ea2ed234538ff8bf232a1ea7b92742` through `9cdf61663ec3c10b4aaa0ed64a56608b86413573`.
- Summary: all Cursor asset validation runs in this range were observed green. Gallery deployment remains blocked by the repository Pages setting; its workflow is manual-only until the owner enables Pages.
- Next session: review commits after this checkpoint and carry the Pages deployment blocker forward.

## Initial baseline

| Commit SHA | Subject | CI result | Checked | Follow-up |
|---|---|---|---|---|
| `1de2bbb6c7ea2ed234538ff8bf232a1ea7b92742` | Default-branch tip at ledger initialization | unavailable | 2026-11-02 | Combined status lookup returned no entries. Revisit if new run or visible failure evidence appears. |

## Red-cross investigation log

## Reviewed commits (2026-11-05)

| Commit SHA | Subject | CI result | Run | Follow-up |
|---|---|---|---|---|
| `8f5805ac740ccc8c6ee89c131dc755c1a054793f` | docs: surface CI validation in README (#54, #65) | green | [41942972328](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/41942972328) | #54 and #65 completed. |
| `0d1190b362192269a90831c99677d0689498f631` | build: declare Windows Python dependencies (#55) | green | [41943109390](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/41943109390) | Follow-up also updated release.yml. |
| `ed0a4735dd13a8d135f22889b7e75ec5a84f9c1a` | feat: deploy interactive cursor gallery (#25, #66) | red | [41943598469](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/41943598469) | Published tree accidentally omitted the existing repository tree; corrected immediately by eabfaa. No history rewrite was performed. |
| `eabfaa899f628f551270afed505252fab158a2ef` | fix: restore repository tree in gallery deployment commit (#25, #66) | green CI / red deploy | [41943642321](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/41943642321) / [41943642243](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/41943642243) | Full tree restored. Pages deployment failed because the Actions integration cannot create the Pages site; owner must enable Pages. |
| `053a378ac595f205d937f79d472affdcd1aec9a3` | build: use Windows requirements in release workflow (#55) | green | [41943891538](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/41943891538) | Both ci.yml and release.yml now install requirements-win.txt. |
| `442c0a52295f7ba46acde75c3a224111680766a5` | docs(windows): document cursor scheme mapping and smoke checks (#45) | green CI / red deploy | [41944001254](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/41944001254) / [41944001099](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/41944001099) | Pages configuration blocker only; Windows runtime checks remain manual under #5. |
| `9866493290d2707f0357883658cef04e60343334` | test: validate the complete Xcursor size ladder (#57) | green CI / red deploy | [41944381903](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/41944381903) / [41944381965](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/41944381965) | Xcursor parser and tests pass; visual validation remains under #38/#57. |
| `85025259e51bfee7866cc3a65554b32d44872ce2` | ci: pause automatic gallery deploy until Pages is enabled (#66) | green | [41944621947](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/41944621947) | Gallery workflow is manual-only and no longer creates automatic red runs while Pages is disabled. |
| `9cdf61663ec3c10b4aaa0ed64a56608b86413573` | docs: summarize modern cursor theme references (#46) | green | [41944789916](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/41944789916) | Reference audit completed; #46 closed. |

## Historical red-cross investigations

### 2026-10-21 — 24 failed validation runs

The failed-run job summaries were reviewed as a batch: 20 stopped at native-tool installation, two at representative-theme selection, and two during parallel Linux builds. Representative logs were inspected for each failure class.

- Native-tool failures: Ubuntu 24.04 did not provide a standalone `xcursorgen` package. The workflow was corrected to install it from `x11-apps` in `cd3f1cfbca1ba7526a887b66067606327ef0cc5b` and `661784e662533abfcc84c212d11e84a1e3ccb7c4`.
- Representative-theme failures: CI referenced a removed `Coral` key. `f2d8b11e762c1fa40ba479dc25b7bde762e86215` switched validation to existing themes.
- Parallel build failures: concurrent themes shared an upstream renderer temporary path. `2b6288d153895ea6807166d0d947ffb865446be7` isolated those files and `0d5ee6192db51c6b343fef24e4b4ba920e79dca8` added regression coverage. Both corrective commits have successful exact-SHA runs: [39605430316](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/39605430316) and [39605455010](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/39605455010).

### 2026-10-24 — validation and deployment failures

- `6df73bacd46d6ed6be657ea8b06e397747a0ea92` and `cc6e35cf26bceec3911a1268f1623b07e627d976` exposed cursor-name/documentation validation problems. The compatibility mapping was corrected in `2d59f27904c0393fddeaffc03060030794a25f0a`; later expanded tables exposed a parser limitation, fixed by `62c37d7e5085d990a5d64c9cc2ffbfd2ed60a40f` ([green run 40109698823](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/40109698823)).
- `e598a1f19fd9295f9fb7d478459957dd3b110415` failed the 4.5:1 contrast test for Teal/Slate. `081ac0a1d24349796c394782827e6492def825d3` corrected the palette and passed ([run 40098343439](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/40098343439)).
- `8b76f323e6a4ac9abc420eccc972ccc85e0b3f7c` and `a3d8470c7ae0f1ebe003a77da1aef41c7f596ad4` failed because the docs validator treated non-CSS alias tables as CSS cursor names. `62c37d7e5085d990a5d64c9cc2ffbfd2ed60a40f` restricted parsing to the CSS table and passed ([run 40109698823](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/40109698823)).
- Gallery deployment runs [40089861398](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/40089861398), [40090561808](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/40090561808), and [40090741448](https://github.com/SakibShahariar/material-bibata-cursor/actions/runs/40090741448) failed because GitHub Pages was not configured. This remains an owner-setting blocker, not a source-validation regression.

The gallery deployment workflow is currently `workflow_dispatch` only with Pages enablement disabled. Restore automatic `master/docs` deployment only after the owner enables Pages and a manual deployment succeeds.


No red result was confirmed from the status data retrieved during setup.

### Failure record template

- Commit SHA:
- Commit subject:
- First observed (date):
- Workflow / run URL:
- Failed job / step:
- Failure summary:
- Classification: regression / pre-existing / inconclusive
- Fix commit(s):
- Rerun attempt(s) and result:
- Final verified outcome:
- Remaining follow-up:

## Session history

| Date | Reviewed range / checkpoint | Result summary |
|---|---|---|
| 2026-11-02 | Initial checkpoint: `1de2bbb6c7ea2ed234538ff8bf232a1ea7b92742` | Latest commit queried; empty status response recorded as unavailable. Earlier history not retroactively audited. |
| 2026-11-05 | Reviewed through `9cdf61663ec3c10b4aaa0ed64a56608b86413573` | New validation runs green; historical red batches diagnosed and corrective commits verified. Gallery deployment remains blocked by Pages settings. |
