"""Seed import module.

"""
from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from . import queries as Q
from .schema import get_conn, init_db


@dataclass
class ImportStats:
    """ImportStats class.
    
    """
    electronics_added: int = 0
    electronics_skipped: int = 0
    filament_added: int = 0
    filament_skipped: int = 0
    paper_added: int = 0
    paper_skipped: int = 0


def _clean(value: str | None) -> str:
    """ clean.
    
    Parameters
    ----------
    value : Any
        value parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    if value is None:
        return ""
    text = value.strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def _to_float(value: str) -> float | None:
    """ to float.
    
    Parameters
    ----------
    value : Any
        value parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    text = _clean(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_int(value: str) -> int:
    """ to int.
    
    Parameters
    ----------
    value : Any
        value parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    parsed = _to_float(value)
    if parsed is None:
        return 0
    return int(parsed)


def _normalize_url(value: str) -> str:
    """ normalize url.
    
    Parameters
    ----------
    value : Any
        value parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    url = _clean(value)
    if not url:
        return ""
    if "https://" in url and not url.startswith("https://"):
        url = url[url.find("https://") :]
    url = url.strip("[]() ")
    return url


def _cost_each(value: str) -> float | None:
    """ cost each.
    
    Parameters
    ----------
    value : Any
        value parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    text = _clean(value).lower().replace(" ", "")
    if not text or text in {"free", "$0", "0"}:
        return 0.0 if text else None

    match = re.search(r"\$?(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    base = float(match.group(1))

    divisor_match = re.search(r"/(\d+(?:\.\d+)?)", text)
    if divisor_match:
        divisor = float(divisor_match.group(1))
        if divisor > 0:
            return round(base / divisor, 4)

    return round(base, 4)


def _supplier_from_url(url: str) -> str:
    """ supplier from url.
    
    Parameters
    ----------
    url : Any
        url parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def _normalize_electronics_category(raw: str) -> str:
    """ normalize electronics category.
    
    Parameters
    ----------
    raw : Any
        raw parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    key = _clean(raw).lower()
    if key == "mono jacks":
        return "mono_jack"
    if key == "switches":
        return "microswitch"
    if key == "control interfaces":
        return "board"
    return "other"


def _normalize_filament_type(raw: str) -> str:
    """ normalize filament type.
    
    Parameters
    ----------
    raw : Any
        raw parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    key = _clean(raw).upper()
    # Return any non-empty type string as-is so unknown materials
    # (e.g. SUPPORT_MATERIAL, SILK_PLA, PA12) aren't silently lost.
    if key:
        return key
    return "PLA"


def _paper_type_from_row(product: str, raw_type: str) -> str:
    """ paper type from row.
    
    Parameters
    ----------
    product : Any
        product parameter.
    
    raw_type : Any
        raw_type parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    p = _clean(product).lower()
    t = _clean(raw_type).lower()
    if "pin" in p:
        return "pin_feed_11.5x11"
    if "sheet" in p:
        return "sheet_feed_11.5x11"
    if "label" in p:
        return "generic_label"
    if t == "braille_paper":
        return "sheet_feed_11.5x11"
    return "generic_label"


def _paper_quantity_from_row(product: str, quantity_raw: str) -> int:
    """ paper quantity from row.
    
    Parameters
    ----------
    product : Any
        product parameter.
    
    quantity_raw : Any
        quantity_raw parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    base_quantity = _to_int(quantity_raw)
    if base_quantity <= 0:
        return 0

    product_text = _clean(product).lower()
    match = re.search(r"(?:box of|\()(\d+)(?:\s*sheets?)?\)?", product_text)
    if match:
        return base_quantity * int(match.group(1))

    return base_quantity


def _replace_existing_inventory() -> None:
    """ replace existing inventory.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        conn.execute("DELETE FROM electronics")
        conn.execute("DELETE FROM filament")
        conn.execute("DELETE FROM braille_paper")


def _electronics_exists(name: str, brand: str, spec: str, supplier: str) -> bool:
    """ electronics exists.
    
    Parameters
    ----------
    name : Any
        name parameter.
    
    brand : Any
        brand parameter.
    
    spec : Any
        spec parameter.
    
    supplier : Any
        supplier parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT 1 FROM electronics WHERE name = ? AND IFNULL(brand, '') = ? AND IFNULL(spec, '') = ? AND IFNULL(supplier, '') = ? LIMIT 1",
            (name, brand, spec, supplier),
        )
        return cur.fetchone() is not None


def _filament_exists(brand: str, color: str, filament_type: str) -> bool:
    """ filament exists.
    
    Parameters
    ----------
    brand : Any
        brand parameter.
    
    color : Any
        color parameter.
    
    filament_type : Any
        filament_type parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT 1 FROM filament WHERE brand = ? AND color = ? AND filament_type = ? LIMIT 1",
            (brand, color, filament_type),
        )
        return cur.fetchone() is not None


def _paper_exists(paper_type: str, supplier: str, notes: str) -> bool:
    """ paper exists.
    
    Parameters
    ----------
    paper_type : Any
        paper_type parameter.
    
    supplier : Any
        supplier parameter.
    
    notes : Any
        notes parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT 1 FROM braille_paper WHERE paper_type = ? AND IFNULL(supplier, '') = ? AND IFNULL(notes, '') = ? LIMIT 1",
            (paper_type, supplier, notes),
        )
        return cur.fetchone() is not None


def _cost_per_kg_from_spool(spool_cost: float, spool_grams: float) -> float | None:
    """ cost per kg from spool.
    
    Parameters
    ----------
    spool_cost : Any
        spool_cost parameter.
    
    spool_grams : Any
        spool_grams parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    if spool_cost < 0 or spool_grams <= 0:
        return None
    return round(spool_cost * (1000.0 / spool_grams), 4)


def inventory_totals() -> dict[str, float]:
    """Inventory totals.
    
    Returns
    -------
    Any
        Function result.
    
    """
    with get_conn() as conn:
        electronics_rows = conn.execute("SELECT COUNT(*) AS c, COALESCE(SUM(quantity), 0) AS q FROM electronics").fetchone()
        filament_rows = conn.execute(
            "SELECT COUNT(*) AS c, COALESCE(SUM(quantity_g), 0) AS q, COALESCE(AVG(cost_per_kg), 0) AS avg_cost FROM filament"
        ).fetchone()
        paper_rows = conn.execute("SELECT COUNT(*) AS c, COALESCE(SUM(quantity), 0) AS q FROM braille_paper").fetchone()

    return {
        "electronics_rows": int(electronics_rows["c"]),
        "electronics_quantity_total": float(electronics_rows["q"]),
        "filament_rows": int(filament_rows["c"]),
        "filament_grams_total": float(filament_rows["q"]),
        "filament_avg_cost_per_kg": float(filament_rows["avg_cost"]),
        "paper_rows": int(paper_rows["c"]),
        "paper_quantity_total": float(paper_rows["q"]),
    }


def _print_totals() -> None:
    """ print totals.
    
    Returns
    -------
    Any
        Function result.
    
    """
    totals = inventory_totals()
    print("[INVENTORY TOTALS]")
    print(
        "Electronics rows: "
        f"{totals['electronics_rows']} (quantity total: {totals['electronics_quantity_total']:.2f})"
    )
    print(
        "Filament rows: "
        f"{totals['filament_rows']} (grams total: {totals['filament_grams_total']:.2f}, "
        f"avg cost/kg: ${totals['filament_avg_cost_per_kg']:.2f})"
    )
    print(
        "Paper rows: "
        f"{totals['paper_rows']} (quantity total: {totals['paper_quantity_total']:.0f})"
    )


def import_seed_csv(
    csv_path: Path,
    *,
    replace_existing: bool = False,
    filament_spool_grams: float = 1000.0,
    filament_spool_cost: float | None = None,
    dry_run: bool = False,
) -> ImportStats:
    """Import seed csv.
    
    Parameters
    ----------
    csv_path : Any
        csv_path parameter.
    
    Returns
    -------
    Any
        Function result.
    
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    init_db()
    if replace_existing and not dry_run:
        _replace_existing_inventory()

    stats = ImportStats()
    seen_keys: set[str] = set()

    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            category = _clean(row.get("Category"))
            product = _clean(row.get("Product"))
            cost = _clean(row.get("Cost"))
            url = _normalize_url(_clean(row.get("URL")))
            notes = _clean(row.get("Notes"))
            item_type = _clean(row.get("TYPE"))
            brand = _clean(row.get("BRAND"))
            color = _clean(row.get("COLOR"))
            qty_raw = _clean(row.get("QUANTITY"))

            row_key = "|".join(
                [category.lower(), product.lower(), item_type.lower(), brand.lower(), color.lower(), qty_raw, url]
            )
            if row_key in seen_keys:
                continue
            seen_keys.add(row_key)

            if category.lower() == "inventory":
                if item_type.upper() == "BRAILLE_PAPER":
                    paper_type = _paper_type_from_row(product, item_type)
                    qty = _paper_quantity_from_row(product, qty_raw)
                    supplier = brand
                    paper_notes = notes
                    if product:
                        paper_notes = (paper_notes + " | " if paper_notes else "") + f"Product: {product}"

                    if _paper_exists(paper_type, supplier, paper_notes):
                        stats.paper_skipped += 1
                        continue

                    if dry_run:
                        stats.paper_added += 1
                        continue

                    Q.add_paper(
                        paper_type=paper_type,
                        quantity=qty,
                        supplier=supplier,
                        notes=paper_notes,
                    )
                    stats.paper_added += 1
                    continue

                filament_type = _normalize_filament_type(item_type)
                filament_brand = brand or "Unknown"
                filament_color = color or "Unknown"
                spool_count = _to_float(qty_raw)
                quantity_g = (spool_count * filament_spool_grams) if spool_count is not None else 0.0
                cost_per_kg = None
                if filament_spool_cost is not None:
                    cost_per_kg = _cost_per_kg_from_spool(filament_spool_cost, filament_spool_grams)

                if _filament_exists(filament_brand, filament_color, filament_type):
                    stats.filament_skipped += 1
                    continue

                filament_notes = notes
                if spool_count is not None:
                    filament_notes = (
                        (filament_notes + " | ") if filament_notes else ""
                    ) + f"Imported as {spool_count:g} spool(s) @ {filament_spool_grams:g}g each"
                if filament_spool_cost is not None:
                    filament_notes = (
                        (filament_notes + " | ") if filament_notes else ""
                    ) + f"Spool cost used: ${filament_spool_cost:.2f}"

                if dry_run:
                    stats.filament_added += 1
                    continue

                Q.add_filament(
                    brand=filament_brand,
                    color=filament_color,
                    filament_type=filament_type,
                    quantity_g=quantity_g,
                    cost_per_kg=cost_per_kg,
                    supplier="",
                    notes=filament_notes,
                )
                stats.filament_added += 1
                continue

            if not product:
                stats.electronics_skipped += 1
                continue

            elec_category = _normalize_electronics_category(category)
            qty = _to_float(qty_raw) or 0.0
            cost_each = _cost_each(cost)
            supplier = _supplier_from_url(url)
            spec = item_type if item_type else None

            extra_notes = []
            if notes:
                extra_notes.append(notes)
            if url:
                extra_notes.append(f"Source URL: {url}")
            if category:
                extra_notes.append(f"Source category: {category}")
            note_text = " | ".join(extra_notes)

            if _electronics_exists(product, brand, spec or "", supplier):
                stats.electronics_skipped += 1
                continue

            if dry_run:
                stats.electronics_added += 1
                continue

            Q.add_electronic(
                category=elec_category,
                name=product,
                quantity=qty,
                brand=brand or None,
                spec=spec,
                unit="pcs",
                cost_each=cost_each,
                supplier=supplier,
                notes=note_text,
            )
            stats.electronics_added += 1

    return stats


def _build_parser() -> argparse.ArgumentParser:
    """ build parser.
    
    Returns
    -------
    Any
        Function result.
    
    """
    parser = argparse.ArgumentParser(
        description="Seed Accessibility Manager inventory tables from a CSV file.",
    )
    parser.add_argument("csv_path", type=Path, help="Path to the CSV file to import")
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Delete existing electronics/filament/paper data before import",
    )
    parser.add_argument(
        "--filament-spool-grams",
        type=float,
        default=1000.0,
        help="Estimated grams per spool when inventory rows only provide spool count",
    )
    parser.add_argument(
        "--grams-per-spool",
        type=float,
        help="Deprecated alias for --filament-spool-grams",
    )
    parser.add_argument(
        "--filament-spool-cost",
        type=float,
        help="Optional cost per filament spool; used to calculate cost_per_kg",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report what would be imported, without writing to the database",
    )
    parser.add_argument(
        "--verify-totals",
        action="store_true",
        help="Print electronics/filament/paper totals after import",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Print inventory totals and exit without importing",
    )
    return parser


def main() -> None:
    """Main.
    
    Returns
    -------
    Any
        Function result.
    
    """
    args = _build_parser().parse_args()

    if args.verify_only:
        init_db()
        _print_totals()
        return

    spool_grams = args.filament_spool_grams
    if args.grams_per_spool is not None:
        spool_grams = args.grams_per_spool

    stats = import_seed_csv(
        args.csv_path,
        replace_existing=args.replace_existing,
        filament_spool_grams=spool_grams,
        filament_spool_cost=args.filament_spool_cost,
        dry_run=args.dry_run,
    )

    mode = "DRY RUN" if args.dry_run else "IMPORT COMPLETE"
    print(f"[{mode}] {args.csv_path}")
    print(f"Electronics added: {stats.electronics_added}")
    print(f"Electronics skipped: {stats.electronics_skipped}")
    print(f"Filament added: {stats.filament_added}")
    print(f"Filament skipped: {stats.filament_skipped}")
    print(f"Paper added: {stats.paper_added}")
    print(f"Paper skipped: {stats.paper_skipped}")

    if args.verify_totals and not args.dry_run:
        _print_totals()


if __name__ == "__main__":
    main()
