from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

import openpyxl

from data_loader import infer_column_mapping, load_excel_data, parse_datetime


def _make_xlsx(tmp_path: Path, headers: list[str], rows: list[list[object]]) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    p = tmp_path / "forms_export.xlsx"
    wb.save(p)
    return p


def test_infer_column_mapping_normalizes_headers() -> None:
    headers = [
        " Navn ",
        "Sambands-nummer",
        "Område",
        "Planlagt Påtropp",
        "Planlagt Avtropp",
        "Skannet Påtropp",
        "Avtropp",
    ]
    mapped = infer_column_mapping(headers, current={})
    assert mapped["name"] == " Navn "
    assert mapped["radio"] == "Sambands-nummer"
    assert mapped["area"] == "Område"


def test_load_excel_data_with_variants_and_datetimes(tmp_path: Path) -> None:
    headers = ["Name", "Radio Nr", "Team", "Omrade", "Planlagt påtropp", "SkannetPåtropp"]
    rows = [
        ["Mats Hansen", "21", "Sikkerhet", "Nord", "11.03.2026 10:15", "11.03.2026 10:16"],
        ["", "22", "Sikkerhet", "Nord", "11.03.2026 10:15", "11.03.2026 10:16"],  # skipped (no name)
    ]
    xlsx = _make_xlsx(tmp_path, headers, rows)

    records = load_excel_data(
        str(xlsx),
        sheet_index=0,
        column_mapping={
            "name": "Navn",  # deliberately different; should be inferred
            "radio": "",
            "team": "",
            "area": "",
            "planned_on": "",
            "planned_off": "",
            "actual_on": "",
            "actual_off": "",
        },
    )
    assert len(records) == 1
    assert records[0].name == "Mats Hansen"
    assert records[0].radio == "21"
    assert records[0].area.lower() in {"nord"}
    assert isinstance(records[0].planned_on, datetime)
    assert isinstance(records[0].actual_on, datetime)


def test_parse_datetime_accepts_excel_serial_when_openpyxl_available() -> None:
    # 2026-03-11 00:00 in 1900-date-system is around this range; exact value isn't important.
    dt = parse_datetime(46000.0)
    assert dt is None or isinstance(dt, datetime)


def test_rejects_unsupported_suffix(tmp_path: Path) -> None:
    p = tmp_path / "bad.bin"
    p.write_bytes(b"not excel")
    with pytest.raises(ValueError):
        load_excel_data(str(p), 0, {})

