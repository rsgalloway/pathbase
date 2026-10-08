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

import json

import pytest

from pathbase import (
    FieldFormatError,
    InvalidPathError,
    InvalidRulesError,
    InvalidTemplateError,
    Template,
    find_matching_templates,
    rules_for,
)

MOVIE = "/shots/{shot}/mov/{shot}_{version}.{ext|mov|mp4}"
FRAMES = "/shots/{shot}/{version}/{shot}_{version}.{frame:04d}.{ext}"


def test_inline_choices_constrain_parsing_and_formatting():
    template = Template(MOVIE, env={})

    assert template.fields == ("shot", "version", "ext")
    assert dict(template.choices) == {"ext": ("mov", "mp4")}
    assert template.parse("/shots/s010/mov/s010_v001.mp4")["ext"] == "mp4"
    assert not template.matches("/shots/s010/mov/s010_v001.png")
    assert template.format(shot="s010", version="v001", ext="mov") == (
        "/shots/s010/mov/s010_v001.mov"
    )
    with pytest.raises(FieldFormatError, match="one of mov, mp4"):
        template.format(shot="s010", version="v001", ext="png")


def test_choices_keep_format_specs_and_repeat_without_restating():
    template = Template("/{take|1|2:02d}/{name}_{take:02d}.exr", env={})

    assert template.parse("/02/plate_02.exr") == {"take": 2, "name": "plate"}
    assert not template.matches("/03/plate_03.exr")


def test_conflicting_or_empty_choices_are_invalid():
    with pytest.raises(InvalidTemplateError, match="conflicting choices"):
        Template("/{ext|mov}/{name}.{ext|mp4}", env={})
    with pytest.raises(InvalidTemplateError, match="invalid choices"):
        Template("/{name}.{ext|}", env={})


def test_rules_constrain_tokens_from_a_flat_map():
    template = Template(FRAMES, env={}, rules={"version": "^v[0-9]{3}$", "frame": "^[0-9]{4}$"})

    assert template.parse("/shots/s010/v001/s010_v001.1001.exr")["frame"] == 1001
    assert not template.matches("/shots/s010/v1/s010_v1.1001.exr")
    # a rule closes the padding gap: {frame:04d} alone also accepts 5 digits
    assert not template.matches("/shots/s010/v001/s010_v001.10010.exr")
    assert dict(template.rules) == {"version": "^v[0-9]{3}$", "frame": "^[0-9]{4}$"}
    with pytest.raises(FieldFormatError, match="must match"):
        template.format(shot="s010", version="v1", frame=1001, ext="exr")


def test_rules_let_the_match_find_the_right_split():
    # without a rule, "s010_extra" could be the shot; the rule moves the split
    template = Template("/{shot}_{task}.exr", env={}, rules={"shot": "^s[0-9]{3}$"})

    assert template.parse("/s010_comp_v2.exr") == {"shot": "s010", "task": "comp_v2"}


def test_template_rules_layer_over_global_ones():
    spec = {
        "rules": {"version": "^v[0-9]{3}$"},
        "templates": {"FRAMES": {"rules": {"frame": "^[0-9]{8}$"}}},
    }

    assert rules_for(spec, "FRAMES") == {"version": "^v[0-9]{3}$", "frame": "^[0-9]{8}$"}
    assert rules_for(spec, "OTHER") == {"version": "^v[0-9]{3}$"}


def test_rules_are_read_from_the_environment(tmp_path):
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(json.dumps({"templates": {"MOVIE": {"rules": {"version": "^v\\d+$"}}}}))
    env = {"MOVIE": MOVIE, "PATHBASE_RULES": str(rules_file)}

    assert [name for name, _ in find_matching_templates("/shots/s/mov/s_v001.mov", env=env)] == [
        "MOVIE"
    ]
    assert find_matching_templates("/shots/s/mov/s_final.mov", env=env) == []

    inline = {"MOVIE": MOVIE, "PATHBASE_RULES": json.dumps({"shot": "^s$"})}
    assert Template.from_env("MOVIE", env=inline).rules == {"shot": "^s$"}


def test_broken_rules_are_errors_not_silently_skipped_templates(tmp_path):
    env = {"MOVIE": MOVIE, "PATHBASE_RULES": str(tmp_path / "missing.json")}

    with pytest.raises(InvalidRulesError, match="cannot read"):
        find_matching_templates("/shots/s/mov/s_v001.mov", env=env)
    with pytest.raises(InvalidRulesError, match="not a valid regex"):
        rules_for({"shot": "("})


def test_templates_without_rules_behave_as_before():
    template = Template(FRAMES, env={})

    assert template.choices == {} and template.rules == {}
    with pytest.raises(InvalidPathError):
        template.parse("/elsewhere/s010.exr")
