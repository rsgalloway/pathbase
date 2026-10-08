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

"""Template parsing and formatting primitives."""

import json
import os
import re
import string
from functools import lru_cache
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Match, Optional, Pattern, Set, Tuple, Type, Union

from pathbase.exceptions import (
    AmbiguousTemplateError,
    FieldFormatError,
    InvalidPathError,
    InvalidRulesError,
    InvalidTemplateError,
    MissingFieldError,
    PlatformResolutionError,
)

FieldType = Type[object]
FormatterPart = Tuple[str, Optional[str], Optional[str], Optional[str]]
PathInput = Union[str, os.PathLike]

ENV_VAR_RE: Pattern[str] = re.compile(r"\$\{([^}]+)\}|\$(\w+)")
SEPARATOR_RE: Pattern[str] = re.compile(r"[\\/]")

#: Environment variable holding token rules: a JSON file path, or inline JSON.
RULES_ENV_VAR = "PATHBASE_RULES"
#: Separates a field name from its allowed values: ``{ext|mov|mp4}``.
CHOICE_SEPARATOR = "|"

Rules = Mapping[str, str]


def _escape_env_vars(template: str) -> str:
    """Escape ${VAR} placeholders so string formatting leaves them intact."""

    def repl(match: Match[str]) -> str:
        token = match.group(0)
        if token.startswith("${"):
            return "${{" + token[2:-1] + "}}"
        return token

    return ENV_VAR_RE.sub(repl, template)


def _unescape_env_vars(template: str) -> str:
    """Convert escaped ${VAR} placeholders back to their literal form."""
    return template.replace("${{", "${").replace("}}", "}")


def _normalize_separators(value: str) -> str:
    """Normalize path separators for cross-platform parsing."""
    return SEPARATOR_RE.sub("/", value)


def _coerce_path_input(value: PathInput) -> str:
    """Convert a path-like input into a string."""
    return os.fspath(value)


def _default_scope(path: PathInput) -> str:
    """Derive a default envstack scope from a concrete path."""
    return os.path.dirname(_normalize_separators(_coerce_path_input(path)))


def _iter_template_items(env: Mapping[str, Any]) -> List[Tuple[str, str]]:
    """Return environment entries that look like path templates."""
    formatter = string.Formatter()
    items = []
    for key, value in env.items():
        if key == RULES_ENV_VAR or not isinstance(value, str) or not value:
            continue
        if "{" not in value or "}" not in value:
            continue
        if "/" not in value and "\\" not in value:
            continue
        try:
            parts = tuple(formatter.parse(_escape_env_vars(value)))
        except ValueError:
            continue
        if not any(field_name is not None for _, field_name, _, _ in parts):
            continue
        items.append((key, value))
    return items


def _template_depth(template: str) -> int:
    """Return a rough directory-depth score for ordering templates."""
    return _normalize_separators(template).count("/")


def _expand_env_vars(template: str, env: Mapping[str, Any]) -> str:
    """Expand $VAR and ${VAR} references using the provided mapping."""

    def repl(match: Match[str]) -> str:
        name = match.group(1) or match.group(2)
        if name in env:
            return str(env[name])
        return _escape_env_vars(match.group(0))

    return ENV_VAR_RE.sub(repl, template)


def _load_platform_environment(
    platform: str,
    *,
    stack: str,
    scope: Optional[str] = None,
) -> Mapping[str, Any]:
    """Load a resolved envstack environment for a target platform."""
    try:
        from envstack.env import load_environ, resolve_environ
    except ImportError as err:
        raise PlatformResolutionError(
            "envstack is required for platform-specific template resolution"
        ) from err

    try:
        raw = load_environ(stack, platform=platform, scope=scope)
        return resolve_environ(raw)
    except Exception as err:
        raise PlatformResolutionError(
            "failed to resolve envstack stack {0!r} for platform {1!r}: {2}".format(
                stack, platform, err
            )
        ) from err


def _split_field(field_name: str) -> Tuple[str, Optional[Tuple[str, ...]]]:
    """Split ``ext|mov|mp4`` into the field name and its allowed values."""
    if CHOICE_SEPARATOR not in field_name:
        return field_name, None
    name, *choices = field_name.split(CHOICE_SEPARATOR)
    if not name or not all(choices):
        raise InvalidTemplateError(f"invalid choices in field {field_name!r}")
    return name, tuple(choices)


def _unanchored(rule: str) -> str:
    """Drop a rule's ``^`` and ``$`` anchors so it can sit inside a larger pattern."""
    if rule.startswith("^"):
        rule = rule[1:]
    if rule.endswith("$") and not rule.endswith("\\$"):
        rule = rule[:-1]
    return rule


def _escape_literal(text: str) -> str:
    """Escape braces so literal template text survives ``str.format``."""
    return text.replace("{", "{{").replace("}", "}}")


def _check_rules(rules: Mapping[str, Any], where: str) -> Dict[str, str]:
    checked = {}
    for token, rule in (rules or {}).items():
        if not isinstance(rule, str):
            raise InvalidRulesError(f"{where}: rule for {token!r} must be a regex string")
        try:
            re.compile(rule)
        except re.error as err:
            raise InvalidRulesError(f"{where}: rule for {token!r} is not a valid regex: {err}")
        checked[token] = rule
    return checked


def rules_for(
    spec: Optional[Mapping[str, Any]], template_name: Optional[str] = None
) -> Dict[str, str]:
    """Return the token rules that apply to one template.

    ``spec`` is either a flat ``{token: regex}`` map, which applies to every
    template, or the ioscan-style shape with global ``rules`` and per-template
    ``templates.<NAME>.rules`` layered over them::

        {"rules": {"version": "^v[0-9]{3}$"},
         "templates": {"PLATE_FILE": {"rules": {"frame": "^[0-9]{8}$"}}}}

    :param spec: Rules spec, or ``None``.
    :param template_name: Template name, for per-template rules.
    :return: Token name to regex.
    :raises InvalidRulesError: If a rule is not a valid regex.
    """
    if not spec:
        return {}
    if "rules" not in spec and "templates" not in spec:
        return _check_rules(spec, "rules")
    rules = _check_rules(spec.get("rules") or {}, "rules")
    if template_name:
        own = ((spec.get("templates") or {}).get(template_name) or {}).get("rules") or {}
        rules.update(_check_rules(own, f"templates.{template_name}.rules"))
    return rules


@lru_cache(maxsize=16)
def _read_rules(source: str, stamp: Optional[float]) -> Mapping[str, Any]:
    try:
        if source.lstrip().startswith("{"):
            data = json.loads(source)
        else:
            with open(source, encoding="utf-8") as handle:
                data = json.load(handle)
    except (OSError, ValueError) as err:
        raise InvalidRulesError(f"cannot read {RULES_ENV_VAR} ({source!r}): {err}") from err
    if not isinstance(data, dict):
        raise InvalidRulesError(f"{RULES_ENV_VAR} must hold a JSON object")
    return MappingProxyType(data)


def load_rules(env: Optional[Mapping[str, Any]] = None) -> Mapping[str, Any]:
    """Return the rules spec named by ``PATHBASE_RULES``, or an empty one.

    :param env: Environment mapping; defaults to ``os.environ``.
    :return: Rules spec (see :func:`rules_for`); re-read when the file changes.
    :raises InvalidRulesError: If the file or JSON cannot be read.
    """
    source = str((os.environ if env is None else env).get(RULES_ENV_VAR) or "").strip()
    if not source:
        return {}
    stamp = None
    if not source.startswith("{"):
        try:
            stamp = os.path.getmtime(source)
        except OSError:
            stamp = None
    return _read_rules(source, stamp)


def _choice_text(choice: str, field_type: FieldType, format_spec: Optional[str], name: str) -> str:
    """Return a choice as it appears in a path, e.g. ``2`` as ``02`` for ``02d``."""
    if field_type is str:
        return choice
    try:
        return format(field_type(choice), format_spec or "")
    except (TypeError, ValueError) as err:
        raise InvalidTemplateError(
            f"choice {choice!r} for field {name!r} is not a {field_type.__name__}"
        ) from err


def _infer_type(format_spec: Optional[str]) -> FieldType:
    """Infer the field type from a simple Python format spec."""
    if not format_spec:
        return str

    format_type = format_spec[-1]
    if format_type == "d":
        return int
    if format_type == "f":
        return float

    raise InvalidTemplateError(f"unsupported format specifier: {format_spec!r}")


class Template:
    """Filesystem path template supporting both formatting and parsing."""

    def __init__(
        self,
        template: PathInput,
        *,
        env: Optional[Mapping[str, Any]] = None,
        expand_env: bool = True,
        name: Optional[str] = None,
        rules: Optional[Mapping[str, Any]] = None,
    ) -> None:
        if not template:
            raise InvalidTemplateError("template cannot be empty")

        self._template: str = _coerce_path_input(template)
        self._name = name
        self._env: Dict[str, Any] = dict(os.environ if env is None else env)
        self._format_template: str = (
            _expand_env_vars(self._template, self._env)
            if expand_env
            else _escape_env_vars(self._template)
        )
        self._resolved: str = _unescape_env_vars(self._format_template)
        self._formatter = string.Formatter()
        try:
            self._parts = tuple(self._formatter.parse(self._format_template))
        except ValueError as err:
            raise InvalidTemplateError(str(err)) from err
        spec = load_rules(self._env) if rules is None else rules
        self._rules: Dict[str, str] = rules_for(spec, name)
        self._fields: List[str] = []
        self._formats: Dict[str, FieldType] = {}
        self._choices: Dict[str, Tuple[str, ...]] = {}
        self._choice_texts: Dict[str, Tuple[str, ...]] = {}
        self._specs: Dict[str, str] = {}
        try:
            self._pattern = self._compile_pattern()
        except re.error as err:
            raise InvalidTemplateError(str(err)) from err

    def __repr__(self) -> str:
        return f"Template({self._template!r})"

    def __str__(self) -> str:
        return self._template

    @property
    def template(self) -> str:
        """Return the original template string."""
        return self._template

    @property
    def name(self) -> Optional[str]:
        """Return the environment variable name associated with this template."""
        return self._name

    @property
    def resolved_template(self) -> str:
        """Return the env-expanded template string used internally."""
        return self._resolved

    @property
    def fields(self) -> Tuple[str, ...]:
        """Return template field names in first-seen order."""
        return tuple(self._fields)

    @property
    def formats(self) -> Mapping[str, FieldType]:
        """Return a read-only mapping of field names to inferred Python types."""
        return MappingProxyType(self._formats)

    @property
    def choices(self) -> Mapping[str, Tuple[str, ...]]:
        """Return a read-only mapping of field names to their allowed values."""
        return MappingProxyType(self._choices)

    @property
    def rules(self) -> Mapping[str, str]:
        """Return a read-only mapping of field names to the regex rules that apply."""
        return MappingProxyType(
            {name: rule for name, rule in self._rules.items() if name in self._formats}
        )

    @property
    def pattern(self) -> str:
        """Return the compiled regex pattern string used for parsing."""
        return self._pattern.pattern

    @classmethod
    def from_env(
        cls,
        name: str,
        *,
        env: Optional[Mapping[str, Any]] = None,
        expand_env: bool = True,
        rules: Optional[Mapping[str, Any]] = None,
    ) -> "Template":
        """Construct a template from an environment variable."""
        env_map = os.environ if env is None else env
        try:
            template = env_map[name]
        except KeyError as err:
            raise MissingFieldError(f"environment variable not found: {name}") from err
        return cls(str(template), env=env_map, expand_env=expand_env, name=name, rules=rules)

    @classmethod
    def from_path(
        cls,
        path: PathInput,
        *,
        env: Optional[Mapping[str, Any]] = None,
        template: Optional[str] = None,
        expand_env: bool = True,
        rules: Optional[Mapping[str, Any]] = None,
    ) -> "Template":
        """Construct a template by env var name or by matching a concrete path."""
        if template is not None:
            return cls.from_env(template, env=env, expand_env=expand_env, rules=rules)
        _, matched = match_template(path, env=env, expand_env=expand_env, rules=rules)
        return matched

    def _compile_pattern(self) -> Pattern[str]:
        pattern_parts = ["^"]
        format_parts = []
        seen: Set[str] = set()

        for literal_text, raw_name, format_spec, conversion in self._parts:
            if conversion is not None:
                raise InvalidTemplateError("field conversions are not supported")

            pattern_parts.append(re.escape(_normalize_separators(literal_text)))
            format_parts.append(_escape_literal(literal_text))

            if raw_name is None:
                continue

            field_name, choices = _split_field(raw_name)
            # str.format sees the plain field; choices only constrain matching
            format_parts.append("{" + field_name + (":" + format_spec if format_spec else "") + "}")
            inferred_type = _infer_type(format_spec)

            if field_name not in self._formats:
                self._fields.append(field_name)
                self._formats[field_name] = inferred_type
                self._specs[field_name] = format_spec or ""
            elif self._formats[field_name] is not inferred_type:
                raise InvalidTemplateError(f"field {field_name!r} uses conflicting format types")

            if choices is not None:
                if self._choices.get(field_name, choices) != choices:
                    raise InvalidTemplateError(f"field {field_name!r} uses conflicting choices")
                self._choices[field_name] = choices
                # numbers are listed as values; the path holds them formatted
                self._choice_texts[field_name] = tuple(
                    _choice_text(choice, inferred_type, format_spec, field_name)
                    for choice in choices
                )

            if field_name in seen:
                pattern_parts.append(f"(?P={field_name})")
                continue

            if field_name in self._choices:
                options = "|".join(re.escape(text) for text in self._choice_texts[field_name])
                value_pattern = f"(?:{options})"
            elif field_name in self._rules:
                value_pattern = f"(?:{_unanchored(self._rules[field_name])})"
            elif inferred_type is int:
                value_pattern = r"-?\d+"
            elif inferred_type is float:
                value_pattern = r"-?(?:\d+(?:\.\d*)?|\.\d+)"
            else:
                value_pattern = r"[^,;\\/]*"
            pattern_parts.append(f"(?P<{field_name}>{value_pattern})")

            seen.add(field_name)

        pattern_parts.append("$")
        self._format_template = "".join(format_parts)
        return re.compile("".join(pattern_parts))

    def _check_value(self, name: str, value: object) -> None:
        """Raise when a value would format to text its field cannot parse back."""
        if name not in self._choices and name not in self._rules:
            return
        try:
            text = format(value, self._specs.get(name, ""))
        except (TypeError, ValueError) as err:
            raise FieldFormatError(f"field {name!r}: {err}") from err
        choices = self._choices.get(name)
        if choices is not None:
            if text not in self._choice_texts[name]:
                raise FieldFormatError(
                    f"field {name!r} must be one of {', '.join(choices)}; got {text!r}"
                )
            return
        if not re.fullmatch(_unanchored(self._rules[name]), text):
            raise FieldFormatError(f"field {name!r} must match {self._rules[name]!r}; got {text!r}")

    def _coerce_field(self, name: str, value: Any) -> object:
        expected_type = self._formats.get(name, str)
        if expected_type is str:
            return str(value)

        try:
            return expected_type(value)
        except (TypeError, ValueError) as err:
            raise FieldFormatError(
                f"field {name!r} must be compatible with {expected_type.__name__}"
            ) from err

    def format(self, **fields: Any) -> str:
        """Format the template with the provided fields."""
        missing = [name for name in self._fields if name not in fields]
        if missing:
            raise MissingFieldError(f"missing required fields: {', '.join(missing)}")

        formatted = {name: self._coerce_field(name, value) for name, value in fields.items()}
        for name in self._fields:
            self._check_value(name, formatted[name])

        try:
            return self._format_template.format(**formatted)
        except KeyError as err:
            raise MissingFieldError(f"missing required field: {err.args[0]}") from err
        except ValueError as err:
            raise InvalidTemplateError(str(err)) from err

    def apply_fields(self, **fields: Any) -> str:
        """Compatibility alias for :meth:`format`."""
        return self.format(**fields)

    def parse(self, path: PathInput) -> Dict[str, object]:
        """Parse a path string into template fields."""
        path_str = _coerce_path_input(path)
        match = self._pattern.fullmatch(_normalize_separators(path_str))
        if not match:
            raise InvalidPathError(path_str)

        parsed: Dict[str, object] = {}
        for name in self._fields:
            parsed[name] = self._coerce_field(name, match.group(name))
        return parsed

    def get_fields(self, path: PathInput) -> Dict[str, object]:
        """Compatibility alias for :meth:`parse`."""
        return self.parse(path)

    def matches(self, path: PathInput) -> bool:
        """Return True if the path matches this template."""
        return self._pattern.fullmatch(_normalize_separators(_coerce_path_input(path))) is not None

    def to_platform(
        self,
        path: PathInput,
        platform: str,
        *,
        stack: str = "pathbase",
        scope: Optional[str] = None,
        target_env: Optional[Mapping[str, Any]] = None,
        template: Optional[str] = None,
        expand_env: bool = True,
    ) -> str:
        """Convert a concrete path to a target platform using this template."""
        fields = self.parse(path)
        template_name = template or self._name

        if target_env is None:
            target_env = _load_platform_environment(
                platform,
                stack=stack,
                scope=scope or _default_scope(path),
            )

        if template_name and template_name in target_env:
            target_template = Template.from_env(
                template_name,
                env=target_env,
                expand_env=expand_env,
            )
        else:
            target_template = Template(
                self._template,
                env=target_env,
                expand_env=expand_env,
                name=template_name,
            )

        return target_template.format(**fields)

    def get_keywords(self) -> Tuple[str, ...]:
        """Compatibility helper returning template fields."""
        return self.fields

    def get_formats(self) -> Dict[str, FieldType]:
        """Compatibility helper returning a mutable copy of the format map."""
        return dict(self._formats)


def find_matching_templates(
    path: PathInput,
    *,
    env: Optional[Mapping[str, Any]] = None,
    expand_env: bool = True,
    rules: Optional[Mapping[str, Any]] = None,
) -> List[Tuple[str, Template]]:
    """Return all environment templates that match a given path.

    :param rules: Token rules spec (see :func:`rules_for`); defaults to the
        one named by ``PATHBASE_RULES`` in ``env``.
    """
    env_map = os.environ if env is None else env
    path_str = _coerce_path_input(path)
    matches = []
    # read once, outside the loop, so a broken rules file is an error rather
    # than every template being skipped as invalid
    spec = load_rules(env_map) if rules is None else rules

    items = _iter_template_items(env_map)
    items.sort(key=lambda item: _template_depth(item[1]), reverse=True)

    for name, value in items:
        try:
            template = Template(value, env=env_map, expand_env=expand_env, name=name, rules=spec)
        except InvalidTemplateError:
            continue
        if template.matches(path_str):
            matches.append((name, template))

    return matches


def match_template(
    path: PathInput,
    *,
    env: Optional[Mapping[str, Any]] = None,
    expand_env: bool = True,
    rules: Optional[Mapping[str, Any]] = None,
) -> Tuple[str, Template]:
    """Return the unique matching environment template for a path."""
    path_str = _coerce_path_input(path)
    matches = find_matching_templates(path_str, env=env, expand_env=expand_env, rules=rules)

    if not matches:
        raise InvalidPathError("no matching template found for path: {0}".format(path_str))

    if len(matches) > 1:
        names = ", ".join(name for name, _ in matches)
        raise AmbiguousTemplateError("path matches multiple templates: {0}".format(names))

    return matches[0]
