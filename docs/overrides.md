# Overrides

`pathbase` does not depend on envstack, but envstack is a useful way to supply
template strings through environment variables. For envstack
documentation, see [envstack.dev](https://envstack.dev).

A common pattern is:

- keep a shared production `pathbase.env` with opinionated baseline templates
- make sure the shared env directory is present in `ENVPATH`
- override only the values that differ for that project in higher-priority env files
- avoid relying on ambient shell variables for template behavior

## Shared Production Baseline

A shared production template file might look like this:

```yaml
#!/usr/bin/env envstack
include: [default]
all: &all
  SHOW_ROOT: ${ROOT}/{show}
  SEQUENCE_ROOT: ${SHOW_ROOT}/{sequence}
  SHOT_ROOT: ${SEQUENCE_ROOT}/{shot}
  STEP_ROOT: ${SHOT_ROOT}/{step}
  FILEPATH: ${STEP_ROOT}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}
linux:
  <<: *all
  ROOT: /mnt/projects
darwin:
  <<: *all
  ROOT: /Volumes/projects
windows:
  <<: *all
  ROOT: D:/projects
```

This gives every project a stable naming model without depending on whatever
ambient variables happen to be present in the shell.

## Project-Specific Overrides

A project can then provide its own `pathbase.env` in a higher-priority env
directory and override only the templates that differ. Because envstack is
hierarchical, the project override does not need to re-include the shared
`pathbase` file as long as the default env directory is already present in
`ENVPATH`.

For example, `bigbuckbunny/env/pathbase.env` could look like this:

```yaml
#!/usr/bin/env envstack
include: [default]
all: &all
  SHOW: bigbuckbunny
  SHOW_ROOT: ${ROOT}/bigbuckbunny
  # This show uses department-specific work areas under a tasks folder.
  STEP_ROOT: ${SHOT_ROOT}/tasks/{step}
  # This show also includes the shot in the filename itself.
  FILEPATH: ${STEP_ROOT}/{shot}_{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}
linux:
  <<: *all
darwin:
  <<: *all
windows:
  <<: *all
```

That override keeps the shared vocabulary, pins the show root, changes the step
folder layout, and changes the filename pattern for one project.

Overrides should come from envstack hierarchy, not from ad hoc shell exports.

## Current and Legacy Templates

Sometimes a production changes its filepath spec over time but still needs to
parse older paths. A practical pattern is to keep one canonical write template
and one or more legacy read templates in the same environment.

For example:

```yaml
#!/usr/bin/env envstack
include: [default]
all: &all
  SHOW_ROOT: ${ROOT}/{show}
  SEQUENCE_ROOT: ${SHOW_ROOT}/{sequence}
  SHOT_ROOT: ${SEQUENCE_ROOT}/{shot}
  STEP_ROOT: ${SHOT_ROOT}/{step}
  # Current template used for formatting new paths.
  FILEPATH: ${STEP_ROOT}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}
  # Older layouts kept around for parsing historical data.
  FILEPATH_V1: ${SHOT_ROOT}/{task}/{task}_{descriptor}.{frame:04d}.{ext}
  FILEPATH_V2: ${STEP_ROOT}/{task}_{descriptor}.{frame:04d}.{ext}
```

This gives you a simple convention:

- `FILEPATH` is the current authoritative write template
- `FILEPATH_V*` values remain available for parsing older paths
- new publishes use the current layout, while old files still round-trip cleanly

In application code, formatting can stay explicit:

```python
from pathbase import Template

template = Template.from_env("FILEPATH")
```

For parsing, `pathbase parse PATH` and `match_template(path)` can match against
any compatible template present in the environment.

A few conventions help keep this maintainable:

- keep field names stable across template generations when the meaning is the same
- prefer one current write template instead of writing through multiple variants
- expect legacy templates to omit some newer fields
- watch for ambiguity when two historical templates can both match the same path

## Using the Resolved Template in Python

Once the environment is activated or resolved outside of `pathbase`, the
application code stays simple:

```python
import os

from pathbase import Template

template = Template.from_env("FILEPATH")

path = template.format(
    show="bigbuckbunny",
    sequence="seq001",
    shot="shot010",
    step="lighting",
    task="render",
    descriptor="beauty",
    version=1,
    frame=1001,
    ext="exr",
)
```

## Why This Split Helps

- shared defaults keep naming conventions consistent across projects
- project overrides stay small and readable
- `pathbase` remains dependency-free and only consumes the final template string
- envstack remains responsible for inheritance, overrides, and platform roots
