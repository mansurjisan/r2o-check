# r2o-check

**NCO Implementation Standards v11.0 compliance checker for NOAA operational model code.**

r2o-check is the "nf-core lint for NOAA operational model delivery" — an automated tool that validates your model package against the [NCO WCOSS Implementation Standards v11.0](https://www.nco.ncep.noaa.gov/idsb/implementation_standards/) before you submit to IDSB. It checks directory structure, file naming conventions, environment variables, build system, modulefiles, version files, and ecFlow scripts.

## Quick Start

```bash
pip install r2o-check
r2o-check lint /path/to/your/model/repo
```

## Features

- **31 rules** across 8 categories (structure, naming, environment, build, modules, versions, ecflow)
- **5 repo types**: operational_model, workflow, tool, library, model_source — rules auto-filter
- **4 output formats**: Rich CLI table, JSON, Markdown (PR comments), HTML report
- **Auto-fix**: create missing directories and stub version files
- **GitHub Action**: `uses: mansurjisan/r2o-check/action@v0.1.0`
- **Configurable**: `.r2o-check.yml` for repo type, disabled rules, ecflow settings
- **Offline**: no network access required for core lint

## Documentation

- [Quickstart Guide](docs/quickstart.md)
- [Rules Reference](docs/rules.md)
- [NCO Standards Mapping](docs/nco-standards-mapping.md)
- [Configuration](docs/quickstart.md#configuration)
- [Contributing](CONTRIBUTING.md)

## License

Apache-2.0. See [LICENSE](LICENSE).
