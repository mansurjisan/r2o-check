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

---

### R2OSTR012 — lib/ directory (conditional)

| Field | Value |
|---|---|
| **Default severity** | WARN |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Model-specific libraries. |
| **Escalation** | None — always WARN. |

---

### R2OSTR013 — gempak/ directory (conditional)

| Field | Value |
|---|---|
| **Default severity** | WARN |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | All GEMPAK-related files. |
| **Escalation** | None — always WARN. |

---

### R2OSTR014 — parm/wmo/ subdirectory (conditional)

| Field | Value |
|---|---|
| **Default severity** | WARN |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | WMO GRIB headers must be in `parm/wmo/`. |
| **Escalation** | None — always WARN. |

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
