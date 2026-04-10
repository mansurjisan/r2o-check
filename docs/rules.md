# r2o-check Rules Reference

All rules cite specific sections of the
[NCO WCOSS Implementation Standards v11.0.0](https://www.nco.ncep.noaa.gov/idsb/implementation_standards/).

## Structure Rules (R2OSTR)

These rules verify that the repository contains the required package subdirectories
defined in NCO v11.0 Section VI.B, Table 3.

---

### R2OSTR001 — ecf/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | ecFlow scripts and definition files must reside in the `ecf/` subdirectory. |

**Example failure:**
```
✘ FAIL  R2OSTR001  Missing required directory 'ecf/'
```

**Fix:** Create the `ecf/` directory and add your ecFlow scripts (`.ecf` files) and
definition files.

---

### R2OSTR002 — jobs/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | J-jobs must be located in the `jobs/` subdirectory. Each job is associated with a single J-job (Section IV.C). |

**Example failure:**
```
✘ FAIL  R2OSTR002  Missing required directory 'jobs/'
```

**Fix:** Create the `jobs/` directory and add J-job scripts following the `JMODEL_TASK`
naming convention (all caps, beginning with J, no extension).

---

### R2OSTR003 — scripts/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Ex-scripts must be located in the `scripts/` subdirectory. Ex-scripts are the primary driver for application processing (Section IV.C). |

**Example failure:**
```
✘ FAIL  R2OSTR003  Missing required directory 'scripts/'
```

**Fix:** Create the `scripts/` directory and add ex-scripts following the `exmodel_task.sh`
naming convention (all lowercase, beginning with `ex`, with appropriate extension).

---

### R2OSTR004 — ush/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Utility scripts (ush-scripts) called by ex-scripts must reside in the `ush/` subdirectory. |

**Example failure:**
```
✘ FAIL  R2OSTR004  Missing required directory 'ush/'
```

**Fix:** Create the `ush/` directory for utility scripts. Scripts here must be all
lowercase, not begin with `ex`, and end with the appropriate extension.

---

### R2OSTR005 — sorc/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Source code that can be compiled must reside in the `sorc/` subdirectory. Each executable's source should be in a sub-directory named after the executable (Section VI.A). |

**Example failure:**
```
✘ FAIL  R2OSTR005  Missing required directory 'sorc/'
```

**Fix:** Create the `sorc/` directory containing compilable source code organized into
sub-directories per executable (e.g., `sorc/model.fd/`).

---

### R2OSTR006 — parm/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Parameter files must reside in the `parm/` subdirectory. WMO GRIB headers go in `parm/wmo/`. |

**Example failure:**
```
✘ FAIL  R2OSTR006  Missing required directory 'parm/'
```

**Fix:** Create the `parm/` directory for parameter and configuration files.

---

### R2OSTR007 — versions/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | The `versions/` directory must contain `run.ver` and `build.ver` files that track package and module versions at runtime and compile time, respectively. |

**Example failure:**
```
✘ FAIL  R2OSTR007  Missing required directory 'versions/'
```

**Fix:** Create the `versions/` directory with `run.ver` and `build.ver` files.
Example content: `export model_ver=v1.0.0`

---

### R2OSTR008 — modulefiles/ directory

| Field | Value |
|---|---|
| **Severity** | FAIL |
| **NCO Section** | VI.B, Table 3 |
| **Rationale** | Module files in Lmod/Lua format must reside in the `modulefiles/` subdirectory. WCOSS uses the Lmod environmental module system (Section VI.A.5). |

**Example failure:**
```
✘ FAIL  R2OSTR008  Missing required directory 'modulefiles/'
```

**Fix:** Create the `modulefiles/` directory and add Lmod/Lua module files for your
model's build and runtime environments.
