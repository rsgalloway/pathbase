# Overrides

`pathbase` does not depend on envstack, but envstack is a useful way to supply
default template strings through environment variables.

A common pattern is:

- keep a shared production `pathbase.env` with default templates
- make sure the shared env directory is present in `ENVPATH`
- override only the templates that differ for that project

## Shared Production Defaults

A shared production template file might look like this:

```yaml
#!/usr/bin/env envstack
include: [default]

all: &all
  SHOW_ROOT: ${SHOW_ROOT:=${ROOT}/{show}}
  SEQUENCE_ROOT: ${SEQUENCE_ROOT:=${SHOW_ROOT}/{sequence}}
  SHOT_ROOT: ${SHOT_ROOT:=${SEQUENCE_ROOT}/{shot}}
  STEP_ROOT: ${STEP_ROOT:=${SHOT_ROOT}/{step}}
  FILEPATH: ${FILEPATH:=${STEP_ROOT}/{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}}

linux:
  <<: *all
  ROOT: ${ROOT:=/mnt/projects}

darwin:
  <<: *all
  ROOT: ${ROOT:=/Volumes/projects}

windows:
  <<: *all
  ROOT: ${ROOT:=P:/projects}
```

This gives every project a stable baseline naming model.

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
  SHOW_ROOT: ${SHOW_ROOT:=${ROOT}/bigbuckbunny}

  # This show uses department-specific work areas under a tasks folder.
  STEP_ROOT: ${STEP_ROOT:=${SHOT_ROOT}/tasks/{step}}

  # This show also includes the shot in the filename itself.
  FILEPATH: ${FILEPATH:=${STEP_ROOT}/{shot}_{task}_{descriptor}_v{version:03d}.{frame:04d}.{ext}}

linux:
  <<: *all

darwin:
  <<: *all

windows:
  <<: *all
```

That override keeps the shared vocabulary, pins the show root, changes the step
folder layout, and changes the filename pattern for one project.

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
- envstack remains responsible for inheritance, defaults, and platform roots
