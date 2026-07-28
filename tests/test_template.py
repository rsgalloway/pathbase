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

from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest

import pathbase.template as template_module
from pathbase import (
    AmbiguousTemplateError,
    FieldFormatError,
    InvalidPathError,
    InvalidTemplateError,
    MissingFieldError,
    PlatformResolutionError,
    Template,
    find_matching_templates,
    match_template,
)


def test_format_returns_string():
    template = Template(
        "/shows/{show}/shots/{sequence}/{shot}/{shot}_{task}_v{version:03d}.{frame:04d}.exr"
    )

    result = template.format(
        show="bigbuckbunny",
        sequence="seq001",
        shot="0150",
        task="plate",
        version=1,
        frame=1001,
    )

    assert result == "/shows/bigbuckbunny/shots/seq001/0150/0150_plate_v001.1001.exr"


def test_parse_returns_typed_fields():
    template = Template(
        "/shows/{show}/shots/{sequence}/{shot}/{shot}_{task}_v{version:03d}.{frame:04d}.exr"
    )

    parsed = template.parse("/shows/bigbuckbunny/shots/seq001/0150/0150_plate_v001.1001.exr")

    assert parsed == {
        "show": "bigbuckbunny",
        "sequence": "seq001",
        "shot": "0150",
        "task": "plate",
        "version": 1,
        "frame": 1001,
    }


def test_repeated_fields_must_match():
    template = Template("{shot}/{shot}_{task}.exr")

    assert template.parse("0150/0150_plate.exr") == {"shot": "0150", "task": "plate"}
    with pytest.raises(InvalidPathError):
        template.parse("0150/0160_plate.exr")


def test_matches_handles_cross_platform_separators():
    template = Template("D:/shows/{show}/{shot}")

    assert template.matches(r"D:\shows\bigbuckbunny\0150")
    assert template.parse(r"D:\shows\bigbuckbunny\0150") == {
        "show": "bigbuckbunny",
        "shot": "0150",
    }


def test_missing_fields_raise_clear_error():
    template = Template("/shows/{show}/{shot}")

    with pytest.raises(MissingFieldError):
        template.format(show="bigbuckbunny")


def test_invalid_field_type_raises_specific_error():
    template = Template("/shows/{show}/v{version:03d}")

    with pytest.raises(FieldFormatError):
        template.format(show="bigbuckbunny", version="abc")


def test_empty_template_is_rejected():
    with pytest.raises(InvalidTemplateError):
        Template("")


def test_unsupported_format_spec_is_rejected():
    with pytest.raises(InvalidTemplateError):
        Template("/shows/{show}/{shot:>10}")


def test_properties_expose_template_metadata():
    template = Template("/shows/{show}/v{version:03d}/{frame:04d}.exr")

    assert template.fields == ("show", "version", "frame")
    assert template.formats["show"] is str
    assert template.formats["version"] is int
    assert template.formats["frame"] is int
    assert str(template) == "/shows/{show}/v{version:03d}/{frame:04d}.exr"
    assert "Template(" in repr(template)


def test_env_vars_expand_from_mapping():
    template = Template("${ROOT}/{show}/{shot}.exr", env={"ROOT": "/mnt/projects"})

    assert template.resolved_template == "/mnt/projects/{show}/{shot}.exr"
    assert (
        template.format(show="bigbuckbunny", shot="0150") == "/mnt/projects/bigbuckbunny/0150.exr"
    )


def test_from_env_reads_os_environ(monkeypatch):
    monkeypatch.setenv("PLATE_FILE", "$ROOT/{shot}.exr")
    monkeypatch.setenv("ROOT", "/mnt/show")

    template = Template.from_env("PLATE_FILE")

    assert template.format(shot="0150") == "/mnt/show/0150.exr"
    assert template.name == "PLATE_FILE"


def test_unresolved_braced_env_var_remains_literal():
    template = Template("${ROOT}/{shot}.exr", env={})

    assert template.resolved_template == "${ROOT}/{shot}.exr"
    assert template.format(shot="0150") == "${ROOT}/0150.exr"


def test_expand_env_false_preserves_braced_env_var_literal():
    template = Template("${ROOT}/{shot}.exr", env={"ROOT": "/mnt/projects"}, expand_env=False)

    assert template.resolved_template == "${ROOT}/{shot}.exr"
    assert template.format(shot="0150") == "${ROOT}/0150.exr"


def test_compatibility_aliases_match_primary_api():
    template = Template("/shows/{show}/v{version:03d}")

    assert template.apply_fields(show="bigbuckbunny", version=1) == template.format(
        show="bigbuckbunny", version=1
    )
    assert template.get_fields("/shows/bigbuckbunny/v001") == template.parse(
        "/shows/bigbuckbunny/v001"
    )
    assert template.get_keywords() == ("show", "version")
    assert template.get_formats() == {"show": str, "version": int}


def test_invalid_template_syntax_raises_invalid_template_error():
    with pytest.raises(InvalidTemplateError):
        Template("{foo")

    with pytest.raises(InvalidTemplateError):
        Template("foo}")


def test_template_accepts_pathlike_inputs():
    template = Template(PurePosixPath("/shows/{show}/v{version:03d}"))

    assert template.parse(Path("/shows/bigbuckbunny/v001")) == {
        "show": "bigbuckbunny",
        "version": 1,
    }


def test_matches_accepts_pure_windows_path():
    template = Template("D:/shows/{show}/{shot}")

    assert template.matches(PureWindowsPath("D:/shows/bigbuckbunny/0150"))
    assert template.parse(PureWindowsPath("D:/shows/bigbuckbunny/0150")) == {
        "show": "bigbuckbunny",
        "shot": "0150",
    }


def test_float_fields_roundtrip_as_floats():
    template = Template("/metrics/{service}/value_{value:.2f}.json")

    result = template.format(service="api", value=3.5)
    parsed = template.parse("/metrics/api/value_3.50.json")

    assert result == "/metrics/api/value_3.50.json"
    assert parsed == {"service": "api", "value": 3.5}


def test_unc_like_path_parses_with_mixed_separators():
    template = Template("//server/share/{show}/{shot}")

    assert template.parse(r"\\server\share\bigbuckbunny\0150") == {
        "show": "bigbuckbunny",
        "shot": "0150",
    }


def test_literal_periods_and_fullmatch_behavior():
    template = Template("/cache/{name}.v{version:03d}.tar.gz")

    assert template.parse("/cache/archive.v001.tar.gz") == {"name": "archive", "version": 1}
    assert not template.matches("/cache/archive.v001.tar.gz.extra")


def test_find_matching_templates_from_environment():
    env = {
        "FILEPATH": "{project}/{name}_v{version:03d}.txt",
        "SHOW_ROOT": "{project}",
        "OTHER": "plain-string",
    }

    matches = find_matching_templates("demo/report_v001.txt", env=env)

    assert [name for name, _ in matches] == ["FILEPATH"]


def test_match_template_returns_unique_match():
    env = {
        "FILEPATH": "{project}/{name}_v{version:03d}.txt",
    }

    name, template = match_template("demo/report_v001.txt", env=env)

    assert name == "FILEPATH"
    assert template.parse("demo/report_v001.txt") == {
        "project": "demo",
        "name": "report",
        "version": 1,
    }


def test_match_template_raises_for_ambiguity():
    env = {
        "FILEPATH": "{project}/{name}.txt",
        "ALT_FILEPATH": "{project}/{artifact}.txt",
    }

    with pytest.raises(AmbiguousTemplateError):
        match_template("demo/report.txt", env=env)


def test_template_from_path_uses_matching_environment_template():
    env = {
        "FILEPATH": "{project}/{name}_v{version:03d}.txt",
    }

    template = Template.from_path("demo/report_v001.txt", env=env)

    assert template.parse("demo/report_v001.txt") == {
        "project": "demo",
        "name": "report",
        "version": 1,
    }
    assert template.name == "FILEPATH"


def test_to_platform_uses_target_template_from_explicit_env():
    source_env = {
        "ROOT": "/mnt/projects",
        "FILEPATH": "${ROOT}/{project}/{name}_v{version:03d}.txt",
    }
    target_env = {
        "ROOT": "D:/projects",
        "FILEPATH": "${ROOT}/{project}/publish/{name}_v{version:03d}.txt",
    }

    template = Template.from_env("FILEPATH", env=source_env)

    result = template.to_platform(
        "/mnt/projects/demo/report_v001.txt",
        "windows",
        target_env=target_env,
    )

    assert result == "D:/projects/demo/publish/report_v001.txt"


def test_to_platform_falls_back_to_template_string_when_name_is_unknown():
    template = Template(
        "${ROOT}/{project}/{name}_v{version:03d}.txt", env={"ROOT": "/mnt/projects"}
    )

    result = template.to_platform(
        "/mnt/projects/demo/report_v001.txt",
        "windows",
        target_env={"ROOT": "D:/projects"},
    )

    assert result == "D:/projects/demo/report_v001.txt"


def test_to_platform_loads_target_platform_env_via_envstack(monkeypatch):
    source_env = {
        "ROOT": "/mnt/projects",
        "FILEPATH": "${ROOT}/{project}/{name}_v{version:03d}.txt",
    }
    template = Template.from_env("FILEPATH", env=source_env)

    calls = []

    def fake_load(platform, *, stack, scope):
        calls.append((platform, stack, scope))
        return {
            "ROOT": "D:/projects",
            "FILEPATH": "${ROOT}/{project}/{name}_v{version:03d}.txt",
        }

    monkeypatch.setattr(template_module, "_load_platform_environment", fake_load)

    result = template.to_platform(
        "/mnt/projects/demo/report_v001.txt",
        "windows",
        stack="render",
        scope="/mnt/projects/demo/env",
    )

    assert result == "D:/projects/demo/report_v001.txt"
    assert calls == [("windows", "render", "/mnt/projects/demo/env")]


def test_to_platform_raises_clear_error_without_envstack(monkeypatch):
    source_env = {
        "ROOT": "/mnt/projects",
        "FILEPATH": "${ROOT}/{project}/{name}_v{version:03d}.txt",
    }
    template = Template.from_env("FILEPATH", env=source_env)

    def fake_load(platform, *, stack, scope):
        raise PlatformResolutionError(
            "envstack is required for platform-specific template resolution"
        )

    monkeypatch.setattr(template_module, "_load_platform_environment", fake_load)

    with pytest.raises(PlatformResolutionError):
        template.to_platform("/mnt/projects/demo/report_v001.txt", "windows")
