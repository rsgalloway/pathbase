#!/usr/bin/env python

"""Custom exceptions for pathbase."""


class PathbaseError(Exception):
    """Base exception for pathbase."""


class InvalidTemplateError(PathbaseError):
    """Raised when a template string is invalid."""


class MissingFieldError(PathbaseError):
    """Raised when required fields are missing during formatting."""


class FieldFormatError(PathbaseError):
    """Raised when a field value cannot be coerced to its declared type."""


class InvalidPathError(PathbaseError):
    """Raised when a path does not match a template."""
