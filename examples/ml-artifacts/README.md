# ML Artifacts Example

This example stores experiment outputs under project, experiment, run, and
artifact fields.

Example template:

```text
/mnt/ml/{project}/{experiment}/{run_id}/{artifact}.{ext}
```

Example filepath:

```text
/mnt/ml/pathbase/baseline/run-001/metrics.json
```

Try it:

```bash
ENVPATH=./examples/ml-artifacts/ pathbase parse \
  '/mnt/ml/pathbase/baseline/run-001/metrics.json'
```

Expected output:

```json
{
  "fields": {
    "artifact": "metrics",
    "ext": "json",
    "experiment": "baseline",
    "project": "pathbase",
    "run_id": "run-001"
  },
  "template": "FILEPATH"
}
```
