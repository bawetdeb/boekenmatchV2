"""Import source catalog without guessing reading characteristics or availability."""
import hashlib
import json
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/sources/jeugdboeken.xlsx"
OUTPUT = ROOT / "data/library-catalog.json"
UNKNOWN = ["isbn", "levels", "schoolYear", "readingDifficulty", "readingSpeed",
           "chapterLength", "pages", "themes", "interests", "realismFantasy",
           "ageMin", "ageMax", "sensitiveTopics", "summary", "coverUrl",
           "auraId", "auraUrl", "location", "available"]


def build_catalog(source=SOURCE):
    workbook = openpyxl.load_workbook(source, data_only=False)
    records = []
    for sheet in workbook:
        headers = [cell.value for cell in sheet[1]]
        if headers != ["Titel [ Mat. aanduiding ... ] ", "Auteur(s)", "Niveau"]:
            raise ValueError(f"Onverwachte kolommen: {sheet.title}")
        for row_number, row in enumerate(sheet.iter_rows(min_row=2), 2):
            values = [cell.value for cell in row]
            if all(value is None for value in values):
                continue
            if any(cell.data_type == "f" for cell in row):
                raise ValueError(f"Formule vereist handmatige controle: {sheet.title}:{row_number}")
            title, author, level = [str(value).strip() if value is not None else None for value in values]
            missing = [name for name, value in [("title", title), ("author", author), ("catalogLevel", level)] if not value]
            records.append({
                "id": f"excel-{sheet.title}-{row_number:04d}",
                "title": title or None, "author": author or None,
                "catalogLevel": level or None,
                **{name: None for name in UNKNOWN},
                "missingFields": missing + UNKNOWN,
                "metadataStatus": "needs-review", "recommendationReady": False,
                "source": {"file": "data/sources/jeugdboeken.xlsx", "sheet": sheet.title,
                           "row": row_number, "values": dict(zip(headers, values))},
            })
    workbook.close()
    return {"source": "excel", "sourceSha256": hashlib.sha256(Path(source).read_bytes()).hexdigest(),
            "recordCount": len(records), "records": records}


if __name__ == "__main__":
    catalog = build_catalog()
    OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {catalog['recordCount']} source rows into {OUTPUT}")
