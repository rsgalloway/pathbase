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

import pathbase.template as template_module
from pathbase.cli import main


def test_cli_format(capsys):
    result = main(
        [
            "format",
            "--template",
            "{project}/{name}_v{version:03d}.txt",
            "project=demo",
            "name=report",
            "version=1",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.strip() == "demo/report_v001.txt"


def test_cli_parse(capsys):
    result = main(
        [
            "parse",
            "demo/report_v001.txt",
        ]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert "no matching template found" in captured.err


def test_cli_parse_from_environment_template(monkeypatch, capsys):
    monkeypatch.setenv("FILEPATH", "{project}/{name}_v{version:03d}.txt")

    result = main(["parse", "demo/report_v001.txt"])

    captured = capsys.readouterr()
    assert result == 0
    assert json.loads(captured.out) == {
        "fields": {
            "name": "report",
            "project": "demo",
            "version": 1,
        },
        "template": "FILEPATH",
    }


def test_cli_parse_with_explicit_template_name(monkeypatch, capsys):
    monkeypatch.setenv("FILEPATH", "{project}/{name}_v{version:03d}.txt")

    result = main(["parse", "--template", "FILEPATH", "demo/report_v001.txt"])

    captured = capsys.readouterr()
    assert result == 0
    assert json.loads(captured.out)["template"] == "FILEPATH"


def test_cli_parse_with_platform(monkeypatch, capsys):
    monkeypatch.setenv(
        "FILEPATH",
        "${ROOT}/{project}/{name}_v{version:03d}.txt",
    )
    monkeypatch.setenv("ROOT", "/mnt/projects")

    def fake_load(platform, *, stack, scope):
        assert platform == "windows"
        assert stack == "pathbase"
        assert scope == "/mnt/projects/demo"
        return {
            "ROOT": "D:/projects",
            "FILEPATH": "${ROOT}/{project}/{name}_v{version:03d}.txt",
        }

    monkeypatch.setattr(template_module, "_load_platform_environment", fake_load)

    result = main(["parse", "--platform", "windows", "/mnt/projects/demo/report_v001.txt"])

    captured = capsys.readouterr()
    assert result == 0
    assert json.loads(captured.out) == {
        "fields": {
            "name": "report",
            "project": "demo",
            "version": 1,
        },
        "platform_path": "D:/projects/demo/report_v001.txt",
        "template": "FILEPATH",
    }


def test_cli_match_success_and_failure(monkeypatch, capsys):
    monkeypatch.delenv("FILEPATH", raising=False)

    ok = main(["match", "--template", "FILEPATH", "demo/report.txt"])
    ok_out = capsys.readouterr()
    assert ok == 2
    assert "environment variable not found: FILEPATH" in ok_out.err


def test_cli_match_from_environment_template(monkeypatch, capsys):
    monkeypatch.setenv("FILEPATH", "{project}/{name}.txt")

    ok = main(["match", "demo/report.txt"])
    ok_out = capsys.readouterr()
    assert ok == 0
    assert ok_out.out.strip() == "FILEPATH"

    bad = main(["match", "--template", "FILEPATH", "demo/report.exr"])
    bad_out = capsys.readouterr()
    assert bad == 1
    assert bad_out.out.strip() == "false"


def test_cli_match_reports_ambiguity(monkeypatch, capsys):
    monkeypatch.setenv("FILEPATH", "{project}/{name}.txt")
    monkeypatch.setenv("ALT_FILEPATH", "{project}/{artifact}.txt")

    result = main(["match", "demo/report.txt"])
    captured = capsys.readouterr()

    assert result == 2
    assert "path matches multiple templates" in captured.err
