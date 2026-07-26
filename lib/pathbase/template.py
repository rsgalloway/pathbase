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
from typing import Any, Dict, List, Mapping, Match, Optional, Pattern, Set, Tuple, Type

from pathbase.exceptions import (
    FieldFormatError,
    InvalidPathError,
    InvalidTemplateError,
    MissingFieldError,
)

FieldType = Type[object]
FormatterPart = Tuple[str, Optional[str], Optional[str], Optional[str]]

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


def _expand_env_vars(template: str, env: Mapping[str, Any]) -> str:
    """Expand $VAR and ${VAR} references using the provided mapping."""

    def repl(match: Match[str]) -> str:
        name = match.group(1) or match.group(2)
        if name in env:
            return str(env[name])
        return _escape_env_vars(match.group(0))

    return ENV_VAR_RE.sub(repl, template)


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
        template: str,
        *,
        env: Optional[Mapping[str, Any]] = None,
        expand_env: bool = True,
    ) -> None:
        if not template:
            raise InvalidTemplateError("template cannot be empty")

        self._template: str = str(template)
        self._env: Dict[str, Any] = dict(os.environ if env is None else env)
        self._format_template: str = (
            _expand_env_vars(self._template, self._env)
            if expand_env
            else _escape_env_vars(self._template)
        )
        self._resolved: str = _unescape_env_vars(self._format_template)
        self._formatter = string.Formatter()
        self._parts: Tuple[FormatterPart, ...] = tuple(self._formatter.parse(self._format_template))
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
        return cls(str(template), env=env_map, expand_env=expand_env)

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

    def parse(self, path: str) -> Dict[str, object]:
        """Parse a path string into template fields."""
        match = self._pattern.fullmatch(_normalize_separators(str(path)))
        if not match:
            raise InvalidPathError(str(path))

        parsed: Dict[str, object] = {}
        for name in self._fields:
            parsed[name] = self._coerce_field(name, match.group(name))
        return parsed

    def get_fields(self, path: str) -> Dict[str, object]:
        """Compatibility alias for :meth:`parse`."""
        return self.parse(path)

    def matches(self, path: str) -> bool:
        """Return True if the path matches this template."""
        return self._pattern.fullmatch(_normalize_separators(str(path))) is not None

    def get_keywords(self) -> Tuple[str, ...]:
        """Compatibility helper returning template fields."""
        return self.fields

    def get_formats(self) -> Dict[str, FieldType]:
        """Compatibility helper returning a mutable copy of the format map."""
        return dict(self._formats)
