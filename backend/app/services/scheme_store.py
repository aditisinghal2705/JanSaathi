"""
Loads and serves the schemes dataset.

This is a flat JSON file for now. To move to a database later (Azure Cosmos DB,
Azure SQL, Postgres) only this module has to change: keep the same function
names and return the same `Scheme` objects.
"""
import json
from pathlib import Path

from app.models.schemas import Category, Scheme

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SCHEMES_PATH = DATA_DIR / "schemes.json"
CATEGORIES_PATH = DATA_DIR / "categories.json"

_schemes: list[Scheme] = []
_categories_raw: list[dict] = []


def load_schemes() -> list[Scheme]:
    global _schemes
    if not _schemes:
        with open(SCHEMES_PATH, "r", encoding="utf-8") as f:
            _schemes = [Scheme(**item) for item in json.load(f)]
    return _schemes


def _load_categories_raw() -> list[dict]:
    global _categories_raw
    if not _categories_raw:
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            _categories_raw = json.load(f)
    return _categories_raw


def reload() -> None:
    """Drop caches so the next call re-reads the JSON files."""
    global _schemes, _categories_raw
    _schemes = []
    _categories_raw = []


def get_categories() -> list[Category]:
    schemes = load_schemes()
    result = []
    for raw in _load_categories_raw():
        count = sum(1 for s in schemes if s.category == raw["name"]["en"])
        result.append(Category(scheme_count=count, **raw))
    return result


def _category_name_for(value: str) -> str | None:
    """Accept either a category id ('pension') or its English name."""
    value = value.strip().lower()
    for raw in _load_categories_raw():
        if value == raw["id"].lower() or value == raw["name"]["en"].lower():
            return raw["name"]["en"]
    return None


def get_all(category: str | None = None, search: str | None = None) -> list[Scheme]:
    schemes = load_schemes()

    if category:
        wanted = _category_name_for(category) or category
        schemes = [s for s in schemes if s.category.lower() == wanted.lower()]

    if search and search.strip():
        q = search.strip().lower()
        schemes = [s for s in schemes if q in _searchable_text(s)]

    return schemes


def _searchable_text(s: Scheme) -> str:
    """Every language of every text field, lowercased, for simple substring search."""
    parts = [s.category, s.department]
    for field in (s.name, s.description, s.eligibility, s.benefits):
        parts.extend(field.values())
    parts.extend(s.keywords)
    return " ".join(parts).lower()


def get_by_id(scheme_id: str) -> Scheme | None:
    for s in load_schemes():
        if s.id == scheme_id:
            return s
    return None
