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
