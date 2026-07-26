# Distribution

`pathbase` includes a `dist.json` file for use with
[distman](https://github.com/rsgalloway/distman).

The root `dist.json` distributes:

- the `pathbase` Python package
- the generic root `pathbase.env`
- several example `pathbase.env` files under named targets

## Disting the Default Env File

To preview distributing the generic root config:

```bash
dist -d -t env
```

To actually distribute it:

```bash
dist -t env
```

## Disting an Example Flavor

`distman` already supports target selection from the CLI with `-t` / `--target`,
so the practical way to choose an example env file is to define a separate
target for each example in `dist.json`.

Examples:

```bash
dist -d -t env_vfx
dist -d -t env_animation
dist -d -t env_data_pipeline
dist -d -t env_logs
dist -d -t env_ml
```

Each of those targets deploys its selected example env file to the same
destination:

```text
{DEPLOY_ROOT}/env/pathbase.env
```

This means the target name selects which example file is disted, while the
destination path stays stable for downstream tools.

## Why Targets Work Well

- no special `distman` flag is required
- each example stays explicit and discoverable
- teams can choose which env file to distribute by target name
- downstream consumers can always read the same deployed env filename
- additional example flavors can be added later without changing the CLI model
