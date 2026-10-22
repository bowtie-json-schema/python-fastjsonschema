#!/usr/bin/env python3
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
import io
import json
import platform
import sys
import traceback

import fastjsonschema


# fastjsonschema doesn't know the metaschemas of the dialects it supports.
# These are copied from the jsonschema-specifications package.
METASCHEMAS = {
    f"http://json-schema.org/draft-0{version}/schema": json.loads(
        (Path(__file__).parent / "metaschemas" / f"draft{version}.json").read_text(),
    )
    for version in (4, 6, 7)
}


class Handlers(dict):
    """
    A handler for every URI scheme, retrieving schemas from a registry.

    The metaschemas of the supported dialects are always available.
    """

    def __init__(self, registry):
        super().__init__()
        self._registry = registry

    def __contains__(self, scheme):
        return True

    def __getitem__(self, scheme):
        return self._retrieve

    def _retrieve(self, uri):
        try:
            return self._registry[uri]
        except KeyError:
            if uri in METASCHEMAS:
                return METASCHEMAS[uri]
            raise fastjsonschema.JsonSchemaDefinitionException(
                f"{uri} is not in the registry",
            ) from None


@dataclass
class Runner:
    _started: bool = False
    _stdout: io.TextIOWrapper = sys.stdout

    def run(self, stdin=sys.stdin):
        for line in stdin:
            each = json.loads(line)
            cmd = each.pop("cmd")
            response = getattr(self, f"cmd_{cmd}")(**each)
            self._stdout.write(f"{json.dumps(response)}\n")
            self._stdout.flush()

    def cmd_start(self, version):
        assert version == 1
        self._started = True
        os_release = platform.freedesktop_os_release()
        return dict(
            version=1,
            implementation=dict(
                name="fastjsonschema",
                version=metadata.version("fastjsonschema"),
                homepage="https://horejsek.github.io/python-fastjsonschema/",
                documentation=(
                    "https://horejsek.github.io/python-fastjsonschema/"
                ),
                issues=(
                    "https://github.com/horejsek/python-fastjsonschema/issues"
                ),
                source="https://github.com/horejsek/python-fastjsonschema",
                dialects=[
                    "http://json-schema.org/draft-07/schema#",
                    "http://json-schema.org/draft-06/schema#",
                    "http://json-schema.org/draft-04/schema#",
                ],
                language="python",
                language_version=platform.python_version(),
                os=os_release["ID"],
                os_version=os_release["VERSION_ID"],
            ),
        )

    def cmd_dialect(self, dialect):
        assert self._started, "Not started!"
        return dict(ok=False)

    def cmd_run(self, case, seq, output="flag"):
        assert self._started, "Not started!"
        if output != "flag":
            return dict(
                seq=seq,
                skipped=True,
                message=f"fastjsonschema doesn't support {output} output",
            )
        schema = case["schema"]
        try:
            # fastjsonschema fetches remote references with a handler for
            # each URI scheme, falling back to urllib for any scheme without
            # one. Retrieve them from the case's registry instead, and never
            # from the network.
            handlers = Handlers(case.get("registry", {}))
            validate = fastjsonschema.compile(schema, handlers=handlers)

            results = []

            for test in case["tests"]:
                try:
                    validate(test["instance"])
                except fastjsonschema.JsonSchemaException:
                    results.append({"valid": False})
                else:
                    results.append({"valid": True})

            return dict(seq=seq, results=results)
        except:  # noqa: E722  fastjsonschema can raise e.g. IndentationError
            return dict(
                errored=True,
                seq=seq,
                context={"traceback": traceback.format_exc()},
            )

    def cmd_stop(self):
        assert self._started, "Not started!"
        sys.exit(0)


Runner().run()
