#!/usr/bin/env python3
"""Apply verified street addresses and geocode them with Nominatim."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_enrichment import apply

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CAFES = DATA / "cafes.json"
ADDRESSES = DATA / "addresses.json"
UA = "top-100-cafeterias-argentina/1.0 (https://github.com/JuampiHernandez/top-100-cafeterias-argentina)"


def geocode(query: str) -> dict | None:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "ar",
            "addressdetails": 1,
        }
    )
    req = urllib.request.Request(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": UA, "Accept-Language": "es"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        hits = json.loads(resp.read().decode("utf-8"))
    if not hits:
        return None
    hit = hits[0]
    return {
        "lat": round(float(hit["lat"]), 6),
        "lng": round(float(hit["lon"]), 6),
        "display": hit.get("display_name") or query,
    }


def main() -> None:
    payload = json.loads(CAFES.read_text(encoding="utf-8"))
    places = json.loads(ADDRESSES.read_text(encoding="utf-8"))["places"]
    cafes = {int(c["rank"]): c for c in payload["cafes"]}
    updated = 0
    failed = []

    for key, place in places.items():
        rank = int(key)
        cafe = cafes[rank]
        coords = None
        if place.get("lat") is not None and place.get("lng") is not None:
            coords = {
                "lat": place["lat"],
                "lng": place["lng"],
                "display": place.get("display") or place["address"],
            }
        else:
            print(f"Geocoding #{rank} {cafe['name']}: {place['query']}")
            coords = geocode(place["query"])
            time.sleep(1.1)
            if not coords:
                failed.append(rank)
                print(f"  FAILED")
                continue
            place["lat"] = coords["lat"]
            place["lng"] = coords["lng"]
            place["display"] = coords["display"]
            print(f"  {coords['lat']}, {coords['lng']}")

        cafe["address"] = place["address"]
        cafe["neighborhood"] = place["neighborhood"]
        cafe["province"] = place["province"]
        cafe["lat"] = coords["lat"]
        cafe["lng"] = coords["lng"]
        cafe["geocodeSource"] = "verified"
        cafe["precise"] = True
        updated += 1

    for cafe in payload["cafes"]:
        if cafe.get("geocodeSource") in {"curated", "nominatim", "verified"}:
            cafe["precise"] = True
        else:
            cafe["precise"] = False

    ADDRESSES.write_text(
        json.dumps(
            {
                "comment": json.loads(ADDRESSES.read_text(encoding="utf-8"))["comment"],
                "places": places,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    CAFES.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    apply()
    print(f"Updated {updated} cafes with verified addresses")
    if failed:
        print(f"Failed ranks: {failed}")


if __name__ == "__main__":
    main()
