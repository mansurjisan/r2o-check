# r2o-check Rules Reference

All rules cite specific sections of the
[NCO WCOSS Implementation Standards v11.0.0](https://www.nco.ncep.noaa.gov/idsb/implementation_standards/).

Rules declare which `repo_type` values they apply to. If a rule's `applies_to`
does not include the current repo's type, the rule is silently skipped.

---

## Structure Rules (R2OSTR)

These rules verify the required package subdirectories defined in NCO v11.0
Section VI.B, Table 3. R2OSTR001–008 are always required (FAIL if missing).
R2OSTR009–014 are conditionally required (WARN if missing, with documented
escalation conditions).

**Applies to:** `operational_model`, `workflow`

---

### R2OSTR001 — ecf/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | ecFlow scripts and definition files must reside in `ecf/`. |

**Example failure:**
```
✘ FAIL  R2OSTR001  Missing directory 'ecf/'
```

**Fix:** Create `ecf/` and add ecFlow scripts (`.ecf` files) and definition files.

---

### R2OSTR002 — jobs/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | J-jobs must be in `jobs/`. Each job has a single J-job (§IV.C). |

**Example failure:**
```
✘ FAIL  R2OSTR002  Missing directory 'jobs/'
```

**Fix:** Create `jobs/` with J-job scripts using `JMODEL_TASK` naming (all caps,
starts with J, no extension).

---

### R2OSTR003 — scripts/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Ex-scripts must be in `scripts/`. They drive application processing (§IV.C). |

**Example failure:**
```
✘ FAIL  R2OSTR003  Missing directory 'scripts/'
```

**Fix:** Create `scripts/` with ex-scripts using `exmodel_task.sh` naming.

---

### R2OSTR004 — ush/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Utility scripts called by ex-scripts must be in `ush/`. |

**Example failure:**
```
✘ FAIL  R2OSTR004  Missing directory 'ush/'
```

**Fix:** Create `ush/` for utility scripts (all lowercase, not starting with `ex`).

---

### R2OSTR005 — sorc/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Compilable source code must be in `sorc/`, organized into subdirectories per executable (§VI.A). |

**Example failure:**
```
✘ FAIL  R2OSTR005  Missing directory 'sorc/'
```

**Fix:** Create `sorc/` with source code in subdirectories (e.g., `sorc/model.fd/`).

---

### R2OSTR006 — parm/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Parameter files must be in `parm/`. WMO GRIB headers go in `parm/wmo/`. |

**Example failure:**
```
✘ FAIL  R2OSTR006  Missing directory 'parm/'
```

**Fix:** Create `parm/` for parameter and configuration files.

---

### R2OSTR007 — versions/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Must contain `run.ver` and `build.ver` for version tracking. |

**Example failure:**
```
✘ FAIL  R2OSTR007  Missing directory 'versions/'
```

**Fix:** Create `versions/` with `run.ver` and `build.ver` files
(format: `export var=value`).

---

### R2OSTR008 — modulefiles/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | WCOSS uses Lmod; module files must be Lua format in `modulefiles/` (§VI.A.5). |

**Example failure:**
```
✘ FAIL  R2OSTR008  Missing directory 'modulefiles/'
```

**Fix:** Create `modulefiles/` with Lmod/Lua `.lua` module files.

---

### R2OSTR009 — doc/ directory (conditional)

| Field | Value |
|---|---|
| **Default severity** | WARN |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Release notes or other documentation. |
| **Escalation** | None — always WARN. |

> **Why WARN-only:** No static condition reliably indicates that documentation is
> mandatory vs. optional. Escalation to FAIL would require inspecting package
> metadata or release process, which is outside r2o-check's static analysis scope.

---

### R2OSTR010 — exec/ directory (conditional)

| Field | Value |
|---|---|
| **Default severity** | WARN |
| **Escalation** | **FAIL** if `sorc/` contains Fortran or C/C++ sources |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Binary executables directory. Required when the package builds compiled code. |

---

### R2OSTR011 — fix/ directory (conditional)

| Field | Value |
|---|---|
| **Default severity** | WARN |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Fixed fields, tables, or other static input data. |
| **Escalation** | None — always WARN. |

> **Why WARN-only:** Whether a model uses fixed fields depends on the model's
> physics/data requirements, which cannot be determined from directory structure alone.

---

### R2OSTR012 — lib/ directory (conditional)

| Field | Value |
|---|---|
| **Default severity** | WARN |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Model-specific libraries. |
| **Escalation** | None — always WARN. |

> **Why WARN-only:** Determining whether a package builds model-specific libraries
> would require parsing build system output, which is runtime behavior.

---

### R2OSTR013 — gempak/ directory (conditional)

| Field | Value |
|---|---|
| **Default severity** | WARN |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | All GEMPAK-related files. |
| **Escalation** | None — always WARN. |

> **Why WARN-only:** GEMPAK output is model-specific and would require inspecting
> product generation configs or com/ output patterns to determine applicability.

---

### R2OSTR014 — parm/wmo/ subdirectory (conditional)

| Field | Value |
|---|---|
| **Default severity** | WARN |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | WMO GRIB headers must be in `parm/wmo/`. |
| **Escalation** | None — always WARN. |

> **Why WARN-only:** WMO product generation depends on the model's dissemination
> configuration, which is not statically determinable from package structure.

---

## Naming Rules (R2ONAM)

These rules validate file naming conventions for J-jobs, ex-scripts,
module files, and version files.

**Applies to:** `operational_model`, `workflow`

---

### R2ONAM001 — J-job file naming

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | IV.C |
| **Rationale** | J-jobs must follow `JAAAAA` — all caps, beginning with J, no extension. Underscores permitted. |

**Example failure:**
```
✘ FAIL  R2ONAM001  J-job 'jmodel_forecast' violates naming convention
```

**Fix:** Rename to `JMODEL_FORECAST` (all uppercase, starts with J, no extension).

**Validated patterns:** `JRRFS_FORECAST`, `JSTOFS_2D_GLO_POST`

---

### R2ONAM002 — Ex-script file naming

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | IV.C |
| **Rationale** | Ex-scripts must follow `exaaaaa.sh` — all lowercase, beginning with `ex`, ending with `.sh`/`.pl`/`.py`. |

**Example failure:**
```
✘ FAIL  R2ONAM002  Ex-script 'model_task.sh' violates naming
```

**Fix:** Rename to `exmodel_task.sh` (all lowercase, starts with `ex`).

**Validated patterns:** `exrrfs_forecast.sh`, `exstofs_2d_glo_post.sh`

---

### R2ONAM003 — Modulefile format (.lua)

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.A.5 |
| **Rationale** | WCOSS uses Lmod; all module files must be Lua format with `.lua` extension. |

**Example failure:**
```
✘ FAIL  R2ONAM003  Modulefile 'model.tcl' is not .lua format
```

**Fix:** Convert to Lua format with `.lua` extension.

---

### R2ONAM004 — Version file naming and format

| Field | Value |
|---|---|
| **Severity** | FAIL (missing file) / WARN (bad format) |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | `versions/` must contain `run.ver` and `build.ver`. Each line must be `export var=value` or a comment. |

**Example failure:**
```
✘ FAIL  R2ONAM004  Missing version file 'build.ver'
⚠ WARN  R2ONAM004  run.ver:1: line does not match 'export var=value'
```

**Fix:** Create missing files. Ensure all lines use `export var=value` format.

---

### R2ONAM005 — Ush script naming (WARN)

| Field | Value |
|---|---|
| **Severity** | WARN |
| **NCO Section** | IV.C |
| **Rationale** | Ush scripts should be all lowercase, must not start with `ex`, must end with `.sh`/`.pl`/`.py`. |

**Applies to:** `operational_model`, `workflow`

**Example warning:**
```
⚠ WARN  R2ONAM005  Ush script 'ExBadUtil.sh': must be lowercase
```

**Fix:** Rename to all lowercase, ensure it doesn't start with `ex`, and has
`.sh`/`.pl`/`.py` extension.

---

## Environment Rules (R2OENV)

These rules validate that J-jobs set the required environment variables from
NCO v11.0 Section III.A, Table 1.

**Applies to:** `operational_model`, `workflow`

---

### R2OENV001 — J-job environment variables

| Field | Value |
|---|---|
| **Severity** | WARN |
| **NCO Section** | III.A, Table 1 |
| **Rationale** | J-jobs must set NET, RUN, PDY, cycle, DATA, COMIN, COMOUT and model-specific location vars (USH*, EXEC*, PARM*, FIX*). |

**Example warning:**
```
⚠ WARN  R2OENV001  JMODEL_TASK: missing $NET (Model name)
```

**Fix:** Add `export NET="model"` or `NET=${NET:-"model"}` to the J-job.

---

## Build Rules (R2OBLD)

These rules validate build system compliance with NCO v11.0 Section VI.A.

**Applies to:** `operational_model`, `workflow`, `model_source`, `library`

---

### R2OBLD001 — Makefile required targets

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.A.8 |
| **Rationale** | Four critical targets must be defined in every Makefile: `all`, `debug`, `install`, `clean`. |

**Example failure:**
```
✘ FAIL  R2OBLD001  sorc/model.fd/Makefile: missing 'debug' target
```

**Fix:** Add the missing target to the Makefile.

---

## Module Rules (R2OMOD)

These rules validate modulefile content per NCO v11.0 Section VI.A.4-5.

**Applies to:** `operational_model`, `workflow`, `model_source`

---

### R2OMOD001 — Modulefile dependency declarations

| Field | Value |
|---|---|
| **Severity** | WARN |
| **NCO Section** | VI.A.4-5 |
| **Rationale** | Build modulefiles must load a compiler module. All modulefiles should declare their dependencies via `load()` or `depends_on()`. |

**Example warning:**
```
⚠ WARN  R2OMOD001  Build modulefile 'build_model.lua' does not load a compiler
```

**Fix:** Add `load("intel/...")` or equivalent compiler module load call.

---

## Versions Rules (R2OVER)

These rules validate the content and format of version files beyond
the presence check in R2ONAM004.

**Applies to:** `operational_model`, `workflow`

---

### R2OVER001 — run.ver content validation

| Field | Value |
|---|---|
| **Severity** | WARN |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | `run.ver` tracks runtime versions. Variables should use `*_ver` suffix. |

**Example warning:**
```
⚠ WARN  R2OVER001  run.ver:3: 'MY_VAR' does not end with '_ver' suffix
```

**Fix:** Rename variables to use `*_ver` convention (e.g., `export model_ver=v1.0.0`).

---

### R2OVER002 — build.ver content validation

| Field | Value |
|---|---|
| **Severity** | WARN |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | `build.ver` tracks compile-time versions. Same format rules as `run.ver`. |

**Fix:** Ensure all lines use `export var_ver=value` format.

---

## ecFlow Rules (R2OECF)

These rules validate ecFlow `.ecf` script files using text parsing only
(no ecflow Python library required). Per NCO v11.0 Section II.

**Applies to:** `operational_model`, `workflow`

---

### R2OECF001 — head.h / tail.h includes

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | II |
| **Rationale** | ecFlow scripts must include `%include <head.h>` and `%include <tail.h>` to set up and tear down the job environment. |

**Example failure:**
```
✘ FAIL  R2OECF001  jmodel_bad.ecf: missing %include <head.h>, %include <tail.h>
```

**Fix:** Add `%include <head.h>` at the top and `%include <tail.h>` at the bottom.

---

### R2OECF002 — Paired ecflow_client init/complete

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | II |
| **Rationale** | ecFlow scripts must call `ecflow_client --init` and `--complete`, typically via head.h/tail.h includes. |

**Example failure:**
```
✘ FAIL  R2OECF002  jmodel_bad.ecf: missing ecflow_client --complete
```

**Fix:** Add `%include <head.h>/<tail.h>` or explicit ecflow_client calls.

---

### R2OECF003 — Trap handler

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | II, IV.A |
| **Rationale** | ecFlow scripts must set a trap handler (`trap ... EXIT`) to ensure cleanup on failure. head.h typically sets this. |

**Example failure:**
```
✘ FAIL  R2OECF003  jmodel_bad.ecf: no trap handler found
```

**Fix:** Add `trap ... EXIT` or use `%include <head.h>` which sets traps.

---

### R2OECF004 — PBS/Slurm directive format

| Field | Value |
|---|---|
| **Severity** | WARN |
| **NCO Section** | II |
| **Rationale** | PBS directives must use `#PBS -<flag> <value>` syntax; SBATCH must use `#SBATCH --<flag>=<value>`. |

**Example warning:**
```
⚠ WARN  R2OECF004  jmodel.ecf: malformed scheduler directives at jmodel.ecf:5
```

**Fix:** Use proper `#PBS -l walltime=...` or `#SBATCH --time=...` syntax.

---

### R2OECF005 — Hard-coded absolute paths

| Field | Value |
|---|---|
| **Severity** | WARN (one per offending line) |
| **NCO Section** | IV.A.vii, IV.B.4 |
| **Rationale** | No hard-coded paths (`/lfs/`, `/work/`, `/scratch/`, `/gpfs/`, etc.) outside of variable assignments. Use environment variables. |

Assignment lines — including `export VAR=/lfs/…`, `readonly`,
`declare`, `local`, and `typeset` — are exempt. Each offending
line produces its own WARN with a `line` field set, so SARIF and
HTML output point directly at the problem line.

**Example warning:**
```
⚠ WARN  R2OECF005  jmodel.ecf:8: hard-coded path prefix '/lfs/'.
```

**Fix:** Replace hard-coded paths with environment variables
(e.g., `$COMROOT` instead of `/lfs/h1/ops/prod/com`).

---

### R2OECF007 — ecFlow .def file parses (optional)

| Field | Value |
|---|---|
| **Severity** | FAIL on parse error, PASS on clean parse |
| **NCO Section** | II |
| **Rationale** | Verify `.def` files are structurally valid ecFlow by loading them with the `ecflow.Defs` parser. |

Requires the optional `ecflow` Python binding, which is not
published on PyPI — install via the system package manager
(e.g. `apt install python3-ecflow`). When the binding is not
importable the rule is inert and emits no results; a missing
library is not itself a compliance failure.

**Fix:** Run `ecflow_client --load=<file>` locally to see the
parser error in context.

---

## Cross-Reference Rules (R2OXRF)

These rules verify consistency between `jobs/`, `ecf/`,
`scripts/`, and `ush/`. All R2OXRF rules record the line of the
offending call site, so SARIF output points directly at the
reference and CLI messages embed `file:line`.

Call paths may include subdirectories (e.g.
`${SCRIPTSmodel}/forecast/exmodel.sh`). When a call carries a
subdirectory, it must resolve to the exact relative path under
`scripts/` (or `ush/`) — bare basename matching is only used when
the call omits a directory.

**Applies to:** `operational_model`, `workflow`

### R2OXRF001 — J-job has matching ecf file (WARN)
### R2OXRF002 — Ex-scripts called from J-jobs exist (FAIL)
### R2OXRF003 — ecf files reference real J-jobs (WARN)
### R2OXRF004 — ush scripts called from ex-scripts exist (WARN)
### R2OXRF005 — Orphan scripts (WARN)

Orphan detection resolves each J-job call to a single specific
script (preferring a top-level match when the call is a bare
basename). Scripts at different paths with the same basename are
disambiguated — a script can no longer be marked referenced just
because its name appears somewhere in J-job text.

---

## Content Rules (R2OCNT)

**Applies to:** `operational_model`, `workflow`

### R2OCNT001 — J-job debug logging
### R2OCNT002 — err_chk around executable calls
### R2OCNT003 — Shebang present
### R2OCNT004 — No background processes
### R2OCNT005 — No absolute symlinks
### R2OCNT006 — Production utilities

R2OCNT006 bundles three checks drawn from NCO v11.0 III.C:

1. `dbn_alert` calls must be guarded by `$SENDDBN` (WARN if not).
2. Executables in ex-scripts should be preceded by `prep_step`
   (WARN if missing).
3. Bare `cp ` (without flags) in ex-scripts should be `cpreq` so
   failures abort the job (WARN per offending line).

### R2OCNT007 — Working directory hygiene

All content rules strip shell comments before pattern matching,
so commented-out assignments (`# export NET=...`,
`# set -x`, `# KEEPDATA=...`) no longer satisfy the check.

---

## Baselines and Line Numbers

Findings carry an optional `line` field populated by rules that
can locate a violation to a specific line (R2OXRF002/003/004,
R2OECF004/005, R2OCNT004, the `cp`-branch of R2OCNT006). The
field surfaces in:

- **SARIF** `physicalLocation.region.startLine`
- **JSON** `results[].line`
- **HTML** the Location column
- **CLI / Markdown** embedded in the message as `file:line`

Baselines fingerprint findings as `(rule_id, relpath, line)` so
a regression on a *different* line produces a new finding even if
the baseline already hides the same rule firing on line N.
