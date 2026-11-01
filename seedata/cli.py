"""seedata — seedable fake-data generator for developers."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys

from .generators import GENERATORS, PRESETS, _rng, make_record, parse_field

__version__ = "1.0.0"


def _sql_literal(value):
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return repr(value)
    return "'" + str(value).replace("'", "''") + "'"


def render(records, fmt, table):
    """records: list of values, or list of dicts for record mode."""
    if fmt == "json":
        return json.dumps(records, indent=2)
    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        if records and isinstance(records[0], dict):
            writer.writerow(records[0].keys())
            for row in records:
                writer.writerow(row.values())
        else:
            writer.writerow(["value"])
            for value in records:
                writer.writerow([value])
        return buf.getvalue().rstrip("\n")
    if fmt == "sql":
        if not records or not isinstance(records[0], dict):
            raise ValueError("--format sql needs record mode "
                             "(--fields or --preset)")
        lines = []
        for row in records:
            cols = ", ".join(row.keys())
            vals = ", ".join(_sql_literal(v) for v in row.values())
            lines.append(f"INSERT INTO {table} ({cols}) VALUES ({vals});")
        return "\n".join(lines)
    # plain
    lines = []
    for row in records:
        if isinstance(row, dict):
            lines.append(", ".join(str(v) for v in row.values()))
        else:
            lines.append(str(row))
    return "\n".join(lines)


def build_parser():
    p = argparse.ArgumentParser(
        prog="seedata",
        description="Generate believable fake data, reproducibly with --seed.",
    )
    p.add_argument("generator", nargs="?",
                   help="single generator name, e.g. name, email, uuid")
    p.add_argument("-n", "--count", type=int, default=1,
                   help="how many values/records to generate (default: 1)")
    p.add_argument("--seed", type=int, default=None,
                   help="random seed; same seed => same output")
    p.add_argument("--fields", default=None,
                   help="comma-separated fields, e.g. name,email,age:int:18:90")
    p.add_argument("--preset", choices=sorted(PRESETS), default=None,
                   help="built-in record shape: user, product, order")
    p.add_argument("--format", choices=["plain", "json", "csv", "sql"],
                   default="plain", help="output format (default: plain)")
    p.add_argument("--table", default="records",
                   help="table name for --format sql (default: records)")
    p.add_argument("--list", action="store_true",
                   help="list available generators and presets, then exit")
    p.add_argument("--version", action="version", version=f"seedata {__version__}")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.list:
        print("generators:")
        for name in sorted(GENERATORS):
            print(f"  {name}")
        print("presets:")
        for name in sorted(PRESETS):
            print(f"  {name}: {', '.join(PRESETS[name])}")
        return 0

    if args.count < 1:
        print("error: --count must be >= 1", file=sys.stderr)
        return 2

    rng = _rng(args.seed)

    if args.fields or args.preset:
        if args.fields and args.preset:
            print("error: use --fields or --preset, not both", file=sys.stderr)
            return 2
        specs = (args.fields.split(",") if args.fields
                 else PRESETS[args.preset])
        try:
            fields = [parse_field(s.strip()) for s in specs if s.strip()]
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if not fields:
            print("error: no fields given", file=sys.stderr)
            return 2
        records = [make_record(rng, fields) for _ in range(args.count)]
    elif args.generator:
        gen = GENERATORS.get(args.generator)
        if gen is None:
            print(f"error: unknown generator: {args.generator!r} "
                  f"(try --list)", file=sys.stderr)
            return 2
        records = [gen(rng) for _ in range(args.count)]
    else:
        print("error: give a generator, --fields, or --preset "
              "(try --list)", file=sys.stderr)
        return 2

    try:
        print(render(records, args.format, args.table))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
