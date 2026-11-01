# seedata 🌱

> Seed your database with believable fake data — reproducibly.

`seedata` generates names, emails, addresses, UUIDs, colors, IPs, and full
records for seeding databases, demos, and tests. Same `--seed`, same output —
every time. **Zero dependencies, Python 3.9+.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org)

## Install

```bash
pip install seedata
# or run from source:
python -m seedata --list
```

## Quickstart

```bash
# One value
$ seedata email --seed 7
ruby.tanaka@example.com

# Five names, reproducible
$ seedata name -n 5 --seed 42
Priya Novak
Ava Larsen
Lucas Costa
Zoe Novak
Diego Berg

# A whole users table as SQL — paste it straight into your DB
$ seedata --preset user -n 3 --format sql --table users --seed 42
INSERT INTO users (name, email, username, phone, city, date) VALUES ('Priya Novak', 'ava.larsen@mail.test', 'anders.novak', '+1-758-555-0111', 'Northgate', '2020-05-10');
INSERT INTO users (name, email, username, phone, city, date) VALUES ('Ava Kim', 'ivy.costa@example.com', 'jasper.meyer91', '+1-758-555-0153', 'Brookfield', '2025-01-13');
INSERT INTO users (name, email, username, phone, city, date) VALUES ('Elif Larsen', 'ava.rossi@demo.dev', 'nora.tanaka', '+1-981-555-0143', 'Riverton', '2021-01-14');
```

## Usage

```
seedata <generator> [-n N] [--seed S]
seedata --fields name,email,age:int:18:90 [-n N] [--format json|csv|sql|plain]
seedata --preset user|product|order [-n N] [--format ...]
seedata --list
```

### Single values

23 generators: `name`, `first_name`, `last_name`, `username`, `email`,
`phone`, `street`, `city`, `address`, `company`, `job`, `word`,
`sentence`, `paragraph`, `color`, `ipv4`, `uuid`, `password`, `date`,
`bool`, `int`, `price`.

```bash
seedata uuid --seed 3 -n 2
seedata color -n 5
seedata ipv4 --seed 9
```

### Records with `--fields`

Field specs are `column` or `column:generator` or `column:generator:args`:

```bash
# age is an int 18–90, score a price 0–100, joined a date in 2024
seedata --fields name,email,age:int:18:90,score:price:0:100,joined:date:2024-01-01:2024-12-31 \
  -n 3 --format json --seed 21
```

```json
[
  {
    "name": "Ethan Dubois",
    "email": "sofia.dubois@sample.org",
    "age": 45,
    "score": 98.97,
    "joined": "2024-08-31"
  }
]
```

### Presets

- `user` — name, email, username, phone, city, date
- `product` — word, price, color, sentence
- `order` — uuid, email, price, date, bool

### Output formats

- `plain` (default) — one value per line, or comma-joined record values
- `json` — pretty-printed array
- `csv` — with header row
- `sql` — `INSERT INTO <table> (...) VALUES (...);` with proper quoting
  (`O'Brien` → `'O''Brien'`, booleans → `TRUE`/`FALSE`)

## Library use

```python
from seedata.generators import _rng, make_record, parse_field

rng = _rng(42)
fields = [parse_field(spec) for spec in "name,email,age:int:18:90".split(",")]
print(make_record(rng, fields))
# {'name': 'Priya Novak', 'email': 'ava.larsen@mail.test', 'age': 31}
```

## Why seedata?

- **Reproducible** — `--seed` makes flaky seed data a thing of the past;
  CI fixtures and demo databases stay identical across runs.
- **Zero dependencies** — stdlib only, installs in a second.
- **DB-ready** — SQL output with correct escaping, no import step needed.
- **Honest data** — emails use `example.com`/`mail.test`/`demo.dev`
  domains and phones use the reserved `+1-555`-style space, so generated
  rows never accidentally point at real people.

## Development

```bash
python -m pytest -q   # 28 tests
```

## License

MIT — see [LICENSE](LICENSE).
