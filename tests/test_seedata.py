"""Tests for seedata."""

import csv
import io
import json
import re
import subprocess
import sys

import pytest

from seedata.cli import main, render
from seedata.generators import GENERATORS, PRESETS, _rng, make_record, parse_field


def run_cli(*args):
    proc = subprocess.run([sys.executable, "-m", "seedata", *args],
                          capture_output=True, text=True)
    return proc


def test_same_seed_same_output():
    a = run_cli("name", "--seed", "42", "-n", "5")
    b = run_cli("name", "--seed", "42", "-n", "5")
    assert a.returncode == 0
    assert a.stdout == b.stdout
    assert len(a.stdout.splitlines()) == 5


def test_different_seed_different_output():
    a = run_cli("email", "--seed", "1", "-n", "20")
    b = run_cli("email", "--seed", "2", "-n", "20")
    assert a.stdout != b.stdout


def test_email_shape():
    out = run_cli("email", "--seed", "7", "-n", "10").stdout
    for line in out.splitlines():
        assert re.fullmatch(r"[a-z]+\.[a-z]+[0-9]*@[a-z]+\.(com|test|dev|org)",
                            line), line


def test_uuid_shape():
    out = run_cli("uuid", "--seed", "3", "-n", "5").stdout
    pat = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-"
                     r"[0-9a-f]{12}$")
    assert all(pat.match(line) for line in out.splitlines())


def test_color_shape():
    out = run_cli("color", "--seed", "3", "-n", "20").stdout
    assert all(re.fullmatch(r"#[0-9a-f]{6}", line) for line in out.splitlines())


def test_ipv4_valid_and_not_reserved():
    import ipaddress
    out = run_cli("ipv4", "--seed", "9", "-n", "50").stdout
    for line in out.splitlines():
        addr = ipaddress.IPv4Address(line)
        assert not addr.is_private and not addr.is_reserved


def test_password_length():
    out = run_cli("password", "--seed", "5", "-n", "3").stdout
    assert all(len(line) == 14 for line in out.splitlines())


def test_date_within_range():
    out = run_cli("date", "--seed", "11", "-n", "20").stdout
    assert all("2020-01-01" <= line <= "2025-12-31" for line in out.splitlines())


def test_unknown_generator_errors():
    proc = run_cli("nope")
    assert proc.returncode == 2
    assert "unknown generator" in proc.stderr


def test_no_args_errors():
    proc = run_cli()
    assert proc.returncode == 2


def test_count_zero_errors():
    proc = run_cli("name", "-n", "0")
    assert proc.returncode == 2


def test_list_shows_generators():
    proc = run_cli("--list")
    assert proc.returncode == 0
    assert "email" in proc.stdout and "user" in proc.stdout


def test_fields_json_roundtrip():
    proc = run_cli("--fields", "name,email,age:int:18:90", "-n", "3",
                   "--format", "json", "--seed", "21")
    assert proc.returncode == 0
    rows = json.loads(proc.stdout)
    assert len(rows) == 3
    for row in rows:
        assert set(row) == {"name", "email", "age"}
        assert 18 <= row["age"] <= 90
        assert "@" in row["email"]


def test_preset_json():
    proc = run_cli("--preset", "user", "-n", "2", "--format", "json",
                   "--seed", "4")
    rows = json.loads(proc.stdout)
    assert len(rows) == 2
    assert set(rows[0]) == set(PRESETS["user"])


def test_preset_seed_reproducible():
    a = run_cli("--preset", "order", "-n", "5", "--format", "json", "--seed", "8")
    b = run_cli("--preset", "order", "-n", "5", "--format", "json", "--seed", "8")
    assert a.stdout == b.stdout


def test_csv_has_header():
    proc = run_cli("--preset", "user", "-n", "2", "--format", "csv",
                   "--seed", "6")
    rows = list(csv.reader(io.StringIO(proc.stdout)))
    assert rows[0] == PRESETS["user"]
    assert len(rows) == 3


def test_sql_output():
    proc = run_cli("--fields", "name,age:int:18:90", "-n", "2",
                   "--format", "sql", "--table", "users", "--seed", "6")
    assert proc.returncode == 0
    for line in proc.stdout.splitlines():
        assert line.startswith("INSERT INTO users (name, age) VALUES (")
        assert line.endswith(");")


def test_sql_escapes_quotes():
    assert render([{"name": "O'Brien"}], "sql", "t") == \
        "INSERT INTO t (name) VALUES ('O''Brien');"


def test_sql_needs_record_mode():
    proc = run_cli("name", "--format", "sql")
    assert proc.returncode == 2


def test_sql_bool_literal():
    out = render([{"ok": True, "n": 3}], "sql", "t")
    assert "TRUE" in out and "3" in out


def test_fields_and_preset_conflict():
    proc = run_cli("--fields", "name", "--preset", "user")
    assert proc.returncode == 2


def test_unknown_field_kind_errors():
    proc = run_cli("--fields", "x:banana")
    assert proc.returncode == 2


def test_int_field_bounds():
    rng = _rng(1)
    _, fn = parse_field("age:int:18:90")
    assert all(18 <= fn(rng) <= 90 for _ in range(200))


def test_price_field_bounds_and_rounding():
    rng = _rng(2)
    _, fn = parse_field("p:price:5:50")
    for _ in range(200):
        v = fn(rng)
        assert 5 <= v <= 50
        assert round(v, 2) == v


def test_date_field_custom_range():
    rng = _rng(3)
    _, fn = parse_field("d:date:2024-01-01:2024-01-31")
    assert all("2024-01-01" <= fn(rng) <= "2024-01-31" for _ in range(100))


def test_custom_column_name_uses_word():
    fields = [parse_field("nickname")]
    rec = make_record(_rng(0), fields)
    assert isinstance(rec["nickname"], str) and rec["nickname"]


def test_all_generators_produce_something():
    rng = _rng(123)
    for name, gen in GENERATORS.items():
        assert gen(rng) is not None, name


def test_plain_single_values():
    proc = run_cli("word", "-n", "4", "--seed", "0")
    assert proc.returncode == 0
    assert len(proc.stdout.splitlines()) == 4
