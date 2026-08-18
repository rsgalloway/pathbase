---
layout: default
title: Animation Example
description: Example animation asset and publish templates for pathbase.
---

# Animation Example

This example uses asset, department, and version-style naming common in
animation and content production workflows.

Example template:

```text
/mnt/projects/{project}/assets/{asset}/{step}/{asset}_{task}_v{version:03d}.{ext}
```

Example filepath:

```text
/mnt/projects/bigbuckbunny/assets/bunny/model/bunny_publish_v003.usd
```

Example env file:
[examples/animation/pathbase.env](https://github.com/rsgalloway/pathbase/blob/master/examples/animation/pathbase.env)

```bash
curl -L https://raw.githubusercontent.com/rsgalloway/pathbase/master/examples/animation/pathbase.env -o pathbase.env
```

Try it:

```bash
ENVPATH=./examples/animation/ pathbase parse \
  '/mnt/projects/bigbuckbunny/assets/bunny/model/bunny_publish_v003.usd'
```

Expected output:

```json
{
  "fields": {
    "asset": "bunny",
    "project": "bigbuckbunny",
    "step": "model",
    "task": "publish",
    "version": 3,
    "ext": "usd"
  },
  "template": "FILEPATH"
}
```
