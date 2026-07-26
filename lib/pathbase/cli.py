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

"""Command-line tools for pathbase."""

import argparse
import json
import sys
from typing import Dict, List, Optional

from pathbase import PathbaseError, Template, match_template


def _parse_field_assignments(items: List[str]) -> Dict[str, str]:
    """Parse key=value items into a field mapping."""
    fields = {}
    for item in items:
        if "=" not in item:
            raise ValueError("field assignments must use key=value syntax")
        key, value = item.split("=", 1)
        if not key:
            raise ValueError("field names cannot be empty")
        fields[key] = value
    return fields


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level pathbase CLI parser."""
    from pathbase import __version__

    parser = argparse.ArgumentParser(
        prog="pathbase",
        description="pathbase: bidirectional filesystem path templates",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="pathbase {0}".format(__version__),
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>", required=True)

    p_format = subparsers.add_parser("format", help="format a path from a template")
    format_group = p_format.add_mutually_exclusive_group(required=True)
    format_group.add_argument("--template", help="template string")
    format_group.add_argument("--template-env", help="environment variable containing a template")
    p_format.add_argument(
        "fields",
        nargs="*",
        help="field assignments in key=value form",
    )

    p_parse = subparsers.add_parser("parse", help="parse a path using an environment template")
    p_parse.add_argument(
        "--template",
        help="environment variable name containing the template to use",
    )
    p_parse.add_argument("path", help="path to parse")

    p_match = subparsers.add_parser("match", help="find or test a matching template")
    p_match.add_argument(
        "--template",
        help="environment variable name containing the template to use",
    )
    p_match.add_argument("path", help="path to test")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Run the pathbase CLI."""
    args = build_parser().parse_args(argv)

    try:
        if args.command == "format":
            fields = _parse_field_assignments(args.fields)
            if args.template_env:
                template = Template.from_env(args.template_env)
            else:
                template = Template(args.template)
            print(template.format(**fields))
            return 0

        if args.command == "parse":
            if args.template:
                template_name = args.template
                template = Template.from_env(template_name)
            else:
                template_name, template = match_template(args.path)
            result = {
                "template": template_name,
                "fields": template.parse(args.path),
            }
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0

        if args.command == "match":
            if args.template:
                template = Template.from_env(args.template)
                if template.matches(args.path):
                    print(args.template)
                    return 0
                print("false")
                return 1
            template_name, _ = match_template(args.path)
            print(template_name)
            return 0

    except (PathbaseError, ValueError) as err:
        print(str(err), file=sys.stderr)
        return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
