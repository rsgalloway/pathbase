# Distribution

`pathbase` includes a `dist.json` file for use with
[distman](https://github.com/rsgalloway/distman).

The root `dist.json` distributes:

- the `pathbase` Python package
- several example `pathbase.env` files under named targets

## Disting an Example Flavor

[distman](https://github.com/rsgalloway/distman) already supports target
selection from the CLI with `-t` / `--target`, so the practical way to choose
an example env file is to define a separate target for each example in
`dist.json`.

For example, to distribute the VFX `pathbase.env`:

```bash
dist -t env_vfx
```

That copies:

```text
examples/vfx/pathbase.env
```

to:

```text
{DEPLOY_ROOT}/env/pathbase.env
```

Each of those targets deploys its selected example env file to the same
destination. This means the target name selects which example file is disted,
while the destination path stays stable for downstream tools.

## Why Targets Work Well

- no special [distman](https://github.com/rsgalloway/distman) flag is required
- each example stays explicit and discoverable
- teams can choose which env file to distribute by target name
- downstream consumers can always read the same deployed env filename
- additional example flavors can be added later without changing the CLI model
