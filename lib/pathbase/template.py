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

import os
import re
import string
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Match, Optional, Pattern, Set, Tuple, Type, Union

from pathbase.exceptions import (
    AmbiguousTemplateError,
    FieldFormatError,
    InvalidPathError,
    InvalidTemplateError,
    MissingFieldError,
    PlatformResolutionError,
)

FieldType = Type[object]
FormatterPart = Tuple[str, Optional[str], Optional[str], Optional[str]]
PathInput = Union[str, os.PathLike]

ENV_VAR_RE: Pattern[str] = re.compile(r"\$\{([^}]+)\}|\$(\w+)")
SEPARATOR_RE: Pattern[str] = re.compile(r"[\\/]")


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
    return os.path.dirname(_coerce_path_input(path))


def _iter_template_items(env: Mapping[str, Any]) -> List[Tuple[str, str]]:
    """Return environment entries that look like path templates."""
    items = []
    for key, value in env.items():
        if not isinstance(value, str) or not value:
            continue
        if "{" not in value or "}" not in value:
            continue
        if "/" not in value and "\\" not in value:
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
        self._fields: List[str] = []
        self._formats: Dict[str, FieldType] = {}
        self._pattern: Pattern[str] = self._compile_pattern()

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
    ) -> "Template":
        """Construct a template from an environment variable."""
        env_map = os.environ if env is None else env
        try:
            template = env_map[name]
        except KeyError as err:
            raise MissingFieldError(f"environment variable not found: {name}") from err
        return cls(str(template), env=env_map, expand_env=expand_env, name=name)

    @classmethod
    def from_path(
        cls,
        path: PathInput,
        *,
        env: Optional[Mapping[str, Any]] = None,
        template: Optional[str] = None,
        expand_env: bool = True,
    ) -> "Template":
        """Construct a template by env var name or by matching a concrete path."""
        if template is not None:
            return cls.from_env(template, env=env, expand_env=expand_env)
        _, matched = match_template(path, env=env, expand_env=expand_env)
        return matched

    def _compile_pattern(self) -> Pattern[str]:
        pattern_parts = ["^"]
        seen: Set[str] = set()

        for literal_text, field_name, format_spec, conversion in self._parts:
            if conversion is not None:
                raise InvalidTemplateError("field conversions are not supported")

            pattern_parts.append(re.escape(_normalize_separators(literal_text)))

            if field_name is None:
                continue

            inferred_type = _infer_type(format_spec)

            if field_name not in self._formats:
                self._fields.append(field_name)
                self._formats[field_name] = inferred_type
            elif self._formats[field_name] is not inferred_type:
                raise InvalidTemplateError(f"field {field_name!r} uses conflicting format types")

            if field_name in seen:
                pattern_parts.append(f"(?P={field_name})")
                continue

            if inferred_type is int:
                pattern_parts.append(rf"(?P<{field_name}>-?\d+)")
            elif inferred_type is float:
                pattern_parts.append(rf"(?P<{field_name}>-?(?:\d+(?:\.\d*)?|\.\d+))")
            else:
                pattern_parts.append(rf"(?P<{field_name}>[^,;\\/]*)")

            seen.add(field_name)

        pattern_parts.append("$")
        return re.compile("".join(pattern_parts))

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
) -> List[Tuple[str, Template]]:
    """Return all environment templates that match a given path."""
    env_map = os.environ if env is None else env
    path_str = _coerce_path_input(path)
    matches = []

    items = _iter_template_items(env_map)
    items.sort(key=lambda item: _template_depth(item[1]), reverse=True)

    for name, value in items:
        try:
            template = Template(value, env=env_map, expand_env=expand_env, name=name)
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
) -> Tuple[str, Template]:
    """Return the unique matching environment template for a path."""
    path_str = _coerce_path_input(path)
    matches = find_matching_templates(path_str, env=env, expand_env=expand_env)

    if not matches:
        raise InvalidPathError("no matching template found for path: {0}".format(path_str))

    if len(matches) > 1:
        names = ", ".join(name for name, _ in matches)
        raise AmbiguousTemplateError("path matches multiple templates: {0}".format(names))

    return matches[0]
