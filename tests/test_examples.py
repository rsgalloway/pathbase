#!/usr/bin/env python
#
# Copyright (c) 2026, Ryan Galloway (ryan@rsgalloway.com)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  - Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  - Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  - Neither the name of the software nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#


"""The example environments and their token rules work together."""

import os
import re

import pytest

from pathbase import Template, load_rules

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")


def _templates(*names):
    """Read the ``all`` block of example ``pathbase.env`` files, later ones overriding."""
    env = {"ROOT": "/root"}
    for name in names:
        with open(os.path.join(EXAMPLES, name, "pathbase.env")) as handle:
            block = False
            for line in handle:
                if line.startswith("all:"):
                    block = True
                elif block and line.startswith("  ") and ":" in line:
                    key, value = line.strip().split(":", 1)
                    env[key] = value.strip()
                elif block and line.strip() and not line.startswith(" "):
                    block = False
    # resolve nested ${VAR} references, as envstack would
    for _ in range(10):
        resolved = {
            key: re.sub(r"\$\{(\w+)\}", lambda m: env.get(m.group(1), m.group(0)), value)
            for key, value in env.items()
        }
        if resolved == env:
            break
        env = resolved
    return env


def _filepath(*names):
    env = _templates(*names)
    rules_files = [os.path.join(EXAMPLES, name, "rules.json") for name in names]
    spec = load_rules({"PATHBASE_RULES": os.pathsep.join(rules_files)})
    return Template.from_env("FILEPATH", env=env, rules=spec)


CASES = [
    (
        ("vfx",),
        "/root/demo/seq001/shot010/comp/comp_main_v003.1001.exr",
        [
            "/root/demo/seq001/shot010/comp/comp_main_v003.1001.txt",
            "/root/demo/seq001/shot010/comp/comp_main_v3.1001.exr",
            # a task or descriptor holding "_" would make the split a guess
            "/root/demo/seq001/shot010/comp/comp_main_extra_v003.1001.exr",
        ],
    ),
    (
        ("overrides/shared", "overrides/bigbuckbunny"),
        "/root/bigbuckbunny/seq001/shot010/tasks/lighting/shot010_render_beauty_v001.1001.exr",
        [
            # allowed by the shared rules, not by the show's
            "/root/bigbuckbunny/sq1/shot010/tasks/lighting/shot010_render_beauty_v001.1001.exr",
            "/root/bigbuckbunny/seq001/shot010/tasks/paint/shot010_render_beauty_v001.1001.exr",
        ],
    ),
    (
        ("animation",),
        "/root/bunny-film/assets/bunnyHero/rig/bunnyHero_main_v002.ma",
        [
            "/root/bunny-film/assets/bunnyHero/rig/bunnyHero_main_v002.txt",
            "/root/bunny-film/assets/bunnyHero/paint/bunnyHero_main_v002.ma",
        ],
    ),
    (
        ("data-pipeline",),
        "/root/clicks/2026-10-07/region=us-west/part-0003.parquet",
        [
            "/root/clicks/20261007/region=us-west/part-0003.parquet",
            "/root/clicks/2026-10-07/us-west/part-0003.parquet",
            "/root/clicks/2026-10-07/region=us-west/part-0003.txt",
        ],
    ),
    (
        ("logs",),
        "/root/prod/api-gateway/2026-10-07/error.log",
        [
            "/root/prod/api-gateway/2026-10-07/verbose.log",
            "/root/qa/api-gateway/2026-10-07/error.log",
        ],
    ),
    (
        ("ml-artifacts",),
        "/root/vision/resnet-sweep/run-042/model.onnx",
        [
            "/root/vision/resnet-sweep/latest/model.onnx",
            "/root/vision/resnet-sweep/run-042/model.bin",
            "/root/vision/resnet-sweep/run-042/model.final.onnx",
        ],
    ),
]


@pytest.mark.parametrize("examples, good, bad", CASES, ids=[case[0][-1] for case in CASES])
def test_example_rules_accept_conforming_paths_and_reject_others(examples, good, bad):
    template = _filepath(*examples)

    assert template.matches(good), template.pattern
    for path in bad:
        assert not template.matches(path), path
    # what parses formats back to the same path
    assert template.format(**template.parse(good)) == good


def test_every_shipped_rules_file_is_deployed_by_a_conf_target():
    import json

    with open(os.path.join(EXAMPLES, "..", "dist.json")) as handle:
        sources = {target["source"] for target in json.load(handle)["targets"].values()}
    for name in ("vfx", "animation", "data-pipeline", "logs", "ml-artifacts"):
        assert "examples/{0}/rules.json".format(name) in sources
