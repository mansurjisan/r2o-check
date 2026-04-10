# NCO Standards Mapping

Maps every r2o-check rule ID to the exact NCO WCOSS Implementation
Standards v11.0.0 section it enforces.

## Structure Rules

| Rule ID | NCO Section | Description |
|---|---|---|
| R2OSTR001 | VI.B, Table 3 | ecf/ directory |
| R2OSTR002 | VI.B, Table 3 | jobs/ directory |
| R2OSTR003 | VI.B, Table 3 | scripts/ directory |
| R2OSTR004 | VI.B, Table 3 | ush/ directory |
| R2OSTR005 | VI.B, Table 3 | sorc/ directory |
| R2OSTR006 | VI.B, Table 3 | parm/ directory |
| R2OSTR007 | VI.B, Table 3 | versions/ directory |
| R2OSTR008 | VI.B, Table 3 | modulefiles/ directory |
| R2OSTR009 | VI.B, Table 3 | doc/ directory (conditional) |
| R2OSTR010 | VI.B, Table 3 | exec/ directory (conditional, escalates) |
| R2OSTR011 | VI.B, Table 3 | fix/ directory (conditional) |
| R2OSTR012 | VI.B, Table 3 | lib/ directory (conditional) |
| R2OSTR013 | VI.B, Table 3 | gempak/ directory (conditional) |
| R2OSTR014 | VI.B, Table 3 | parm/wmo/ subdirectory (conditional) |

## Naming Rules

| Rule ID | NCO Section | Description |
|---|---|---|
| R2ONAM001 | IV.C | J-job naming (JMODEL_TASK) |
| R2ONAM002 | IV.C | Ex-script naming (exmodel_task.sh) |
| R2ONAM003 | VI.A.5 | Modulefile format (.lua) |
| R2ONAM005 | IV.C | Ush script naming |

## Environment Rules

| Rule ID | NCO Section | Description |
|---|---|---|
| R2OENV001 | III.A, Table 1 | Core J-job env vars (FAIL) |
| R2OENV002 | III.A, Table 1 | Context J-job env vars (WARN) |

## Build Rules

| Rule ID | NCO Section | Description |
|---|---|---|
| R2OBLD001 | VI.A.8 | Makefile targets (all, debug, install, clean) |
| R2OBLD002 | VI.A.8 | CMake build system (project, install) |

## Module Rules

| Rule ID | NCO Section | Description |
|---|---|---|
| R2OMOD001 | VI.A.4-5 | Modulefile dependencies (compiler) |

## Version Rules

| Rule ID | NCO Section | Description |
|---|---|---|
| R2OVER001 | VI.B, Table 3 | run.ver exists (FAIL) |
| R2OVER002 | VI.B, Table 3 | build.ver exists (FAIL) |
| R2OVER003 | VI.B, Table 3 | run.ver content format (WARN) |
| R2OVER004 | VI.B, Table 3 | build.ver content format (WARN) |

## ecFlow Rules

| Rule ID | NCO Section | Description |
|---|---|---|
| R2OECF001 | II | head.h / tail.h includes |
| R2OECF002 | II | Paired ecflow_client init/complete |
| R2OECF003 | II, IV.A | Trap handler |
| R2OECF004 | II | PBS/Slurm directive format |
| R2OECF005 | IV.A.vii, IV.B.4 | Hard-coded absolute paths |
| R2OECF006 | II | Custom head.h/tail.h verification |
