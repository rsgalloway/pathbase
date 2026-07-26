import pytest

from pathbase import (
    FieldFormatError,
    InvalidPathError,
    InvalidTemplateError,
    MissingFieldError,
    Template,
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
