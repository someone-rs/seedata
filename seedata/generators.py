"""Seedable fake-data generators. Pure stdlib, deterministic per seed."""

from __future__ import annotations

import ipaddress
import random
import string
import uuid
from datetime import date, timedelta

FIRST = [
    "Ava", "Liam", "Maya", "Noah", "Zoe", "Ethan", "Ivy", "Lucas", "Nora",
    "Owen", "Ruby", "Felix", "Clara", "Hugo", "Lena", "Milo", "Tara",
    "Jasper", "Elif", "Kenji", "Priya", "Diego", "Sofia", "Anders",
]
LAST = [
    "Smith", "Garcia", "Kim", "Novak", "Tanaka", "Rossi", "Meyer", "Costa",
    "Larsen", "Petrov", "Nguyen", "Ali", "Fischer", "Dubois", "Silva",
    "Kowalski", "Haddad", "Berg", "Okafor", "Lindqvist",
]
DOMAINS = ["example.com", "mail.test", "demo.dev", "sample.org"]
STREETS = ["Maple St", "Oak Ave", "Cedar Ln", "Birch Rd", "Elm Blvd",
           "Willow Way", "Pine Ct", "Juniper Dr"]
CITIES = ["Springfield", "Riverton", "Lakeview", "Brookfield", "Hillcrest",
          "Fairview", "Northgate", "Elmwood"]
COMPANIES = ["Acme", "Northwind", "Globex", "Initech", "Umbrella",
             "Hooli", "Stark", "Wayne", "Soylent", "Massive Dynamic"]
SUFFIXES = ["Inc", "LLC", "Ltd", "Co", "Labs", "Group"]
JOBS = ["Engineer", "Designer", "Analyst", "Manager", "Writer",
        "Developer", "Consultant", "Architect", "Specialist", "Lead"]
WORDS = ("quick brown fox jumps over lazy dog while bright sun warms quiet "
         "streets and distant bells ring softly through morning air").split()


def _rng(seed):
    return random.Random(seed)


def name(rng):
    return f"{rng.choice(FIRST)} {rng.choice(LAST)}"


def first_name(rng):
    return rng.choice(FIRST)


def last_name(rng):
    return rng.choice(LAST)


def username(rng):
    base = f"{rng.choice(FIRST).lower()}.{rng.choice(LAST).lower()}"
    return base if rng.random() < 0.7 else f"{base}{rng.randint(2, 99)}"


def email(rng):
    return f"{username(rng)}@{rng.choice(DOMAINS)}"


def phone(rng):
    # Fictional 555-01xx range, so numbers never belong to a real person.
    return f"+1-{rng.randint(200, 989)}-555-{rng.randint(100, 199):04d}"


def street(rng):
    return f"{rng.randint(1, 9999)} {rng.choice(STREETS)}"


def city(rng):
    return rng.choice(CITIES)


def address(rng):
    return f"{street(rng)}, {city(rng)}, {rng.randint(10000, 99999)}"


def company(rng):
    return f"{rng.choice(COMPANIES)} {rng.choice(SUFFIXES)}"


def job(rng):
    return rng.choice(JOBS)


def word(rng):
    return rng.choice(WORDS)


def sentence(rng, words=8):
    picked = [rng.choice(WORDS) for _ in range(words)]
    picked[0] = picked[0].capitalize()
    return " ".join(picked) + "."


def paragraph(rng, sentences=3):
    return " ".join(sentence(rng, rng.randint(5, 12)) for _ in range(sentences))


def color(rng):
    return "#%06x" % rng.randint(0, 0xFFFFFF)


def ipv4(rng):
    # Avoid reserved ranges; keep it in plausible public-ish space.
    return str(ipaddress.IPv4Address(rng.randint(0x0B000000, 0xDF000000)))


def uuid4(rng):
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def password(rng, length=14):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(rng.choice(alphabet) for _ in range(length))


def date_between(rng, start="2020-01-01", end="2025-12-31"):
    d0 = date.fromisoformat(start)
    d1 = date.fromisoformat(end)
    if d1 < d0:
        d0, d1 = d1, d0
    return str(d0 + timedelta(days=rng.randint(0, (d1 - d0).days)))


def boolean(rng):
    return rng.choice([True, False])


def integer(rng, low=0, high=100):
    return rng.randint(low, high)


def price(rng, low=5, high=500):
    return round(rng.uniform(low, high), 2)


GENERATORS = {
    "name": name,
    "first_name": first_name,
    "last_name": last_name,
    "username": username,
    "email": email,
    "phone": phone,
    "street": street,
    "city": city,
    "address": address,
    "company": company,
    "job": job,
    "word": word,
    "sentence": sentence,
    "paragraph": paragraph,
    "color": color,
    "ipv4": ipv4,
    "uuid": uuid4,
    "password": password,
    "date": date_between,
    "bool": boolean,
    "int": integer,
    "price": price,
}

PRESETS = {
    "user": ["name", "email", "username", "phone", "city", "date"],
    "product": ["word", "price", "color", "sentence"],
    "order": ["uuid", "email", "price", "date", "bool"],
}


def parse_field(spec):
    """Parse 'name' or 'age:int:18:90' or 'score:price:5:500' into (key, fn)."""
    parts = spec.split(":")
    key = parts[0]
    kind = parts[1] if len(parts) > 1 else None
    if kind is None:
        # A bare field name is itself a generator, or a custom column name
        # mapped to the 'word' generator when unknown.
        fn = GENERATORS.get(key, word)
        return key, (lambda rng, fn=fn: fn(rng))
    gen = GENERATORS.get(kind)
    if gen is None:
        raise ValueError(f"unknown generator: {kind!r}")
    if kind == "int":
        low = int(parts[2]) if len(parts) > 2 else 0
        high = int(parts[3]) if len(parts) > 3 else 100
        return key, (lambda rng, low=low, high=high: gen(rng, low, high))
    if kind == "price":
        low = float(parts[2]) if len(parts) > 2 else 5
        high = float(parts[3]) if len(parts) > 3 else 500
        return key, (lambda rng, low=low, high=high: gen(rng, low, high))
    if kind == "date":
        start = parts[2] if len(parts) > 2 else "2020-01-01"
        end = parts[3] if len(parts) > 3 else "2025-12-31"
        return key, (lambda rng, start=start, end=end: gen(rng, start, end))
    return key, (lambda rng, gen=gen: gen(rng))


def make_record(rng, fields):
    return {key: fn(rng) for key, fn in fields}
