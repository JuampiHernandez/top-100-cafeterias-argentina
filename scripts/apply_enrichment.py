#!/usr/bin/env python3
"""Merge verified blurbs/Instagram into cafes.json and export My Maps files."""

from __future__ import annotations

import csv
import json
import xml.sax.saxutils as xml
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CAFES = DATA / "cafes.json"
ENRICH = DATA / "enrichment.json"
KML = DATA / "top100-cafeterias.kml"
CSV_OUT = DATA / "top100-cafeterias.csv"


def nice_location(cafe: dict) -> str:
    neighborhood = (cafe.get("neighborhood") or "").strip()
    province = (cafe.get("province") or "").strip()
    if not neighborhood or neighborhood.upper() == "CABA":
        return "Buenos Aires" if province.upper() == "CABA" else province
    if province.upper() == "CABA":
        return f"{neighborhood}, Buenos Aires"
    if neighborhood.lower() == province.lower():
        return neighborhood
    return f"{neighborhood}, {province}"


def write_kml(cafes: list[dict]) -> None:
    placemarks = []
    for cafe in cafes:
        name = xml.escape(f"#{cafe['rank']} {cafe['name']}")
        bits = [cafe.get("description") or "", cafe.get("address") or cafe.get("location") or ""]
        if cafe.get("instagram"):
            bits.append(cafe["instagram"])
        desc = xml.escape("\n".join(bit for bit in bits if bit))
        placemarks.append(
            f"""    <Placemark>
      <name>{name}</name>
      <description>{desc}</description>
      <Point>
        <coordinates>{cafe['lng']},{cafe['lat']},0</coordinates>
      </Point>
    </Placemark>"""
        )

    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Top 100 cafeterías Argentina 2026</name>
    <description>The Best Coffee Shops Argentina 2026. Importá este archivo en Google My Maps y después usá Copiar mapa para tenerlo en tu cuenta.</description>
{chr(10).join(placemarks)}
  </Document>
</kml>
"""
    KML.write_text(body, encoding="utf-8")


def write_csv(cafes: list[dict]) -> None:
    with CSV_OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["Name", "Description", "Latitude", "Longitude", "Instagram", "Rank", "City"],
        )
        writer.writeheader()
        for cafe in cafes:
            writer.writerow(
                {
                    "Name": f"#{cafe['rank']} {cafe['name']}",
                    "Description": cafe.get("description") or "",
                    "Latitude": cafe["lat"],
                    "Longitude": cafe["lng"],
                    "Instagram": cafe.get("instagram") or "",
                    "Rank": cafe["rank"],
                    "City": cafe.get("location") or "",
                }
            )


def apply() -> None:
    payload = json.loads(CAFES.read_text(encoding="utf-8"))
    enrich = json.loads(ENRICH.read_text(encoding="utf-8"))
    instagram = {int(k): v for k, v in enrich.get("instagram", {}).items()}
    descriptions = {int(k): v for k, v in enrich.get("descriptions", {}).items()}

    with_ig = 0
    for cafe in payload["cafes"]:
        rank = int(cafe["rank"])
        cafe["location"] = nice_location(cafe)
        if rank in descriptions:
            cafe["description"] = descriptions[rank]
        if rank in instagram:
            cafe["instagram"] = instagram[rank]
            with_ig += 1
        else:
            cafe.pop("instagram", None)

    CAFES.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_kml(payload["cafes"])
    write_csv(payload["cafes"])
    print(f"Updated {len(payload['cafes'])} cafes, {with_ig} with Instagram")
    print(f"Wrote {KML.name} and {CSV_OUT.name}")


if __name__ == "__main__":
    apply()
