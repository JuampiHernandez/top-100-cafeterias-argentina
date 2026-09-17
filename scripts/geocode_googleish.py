#!/usr/bin/env python3
"""Look up every cafe as a named place in Argentina.

Uses Nominatim/Photon place search (the same POI graph Google Maps
draws from via OSM for many shops) and keeps only hits inside Argentina.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAFES = ROOT / "data" / "cafes.json"
OUT = ROOT / "data" / "gmaps_lookups.json"
UA = "top-100-cafeterias-argentina/1.1 (https://github.com/JuampiHernandez/top-100-cafeterias-argentina)"

AR_BOX = (-55.2, -73.6, -21.7, -53.5)  # lat_min, lng_min, lat_max, lng_max


def in_argentina(lat: float, lng: float) -> bool:
    return AR_BOX[0] <= lat <= AR_BOX[2] and AR_BOX[1] <= lng <= AR_BOX[3]


def fetch_json(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "es"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def nominatim_search(query: str, limit: int = 5) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "format": "jsonv2",
            "limit": limit,
            "countrycodes": "ar",
            "addressdetails": 1,
            "extratags": 1,
        }
    )
    hits = fetch_json(f"https://nominatim.openstreetmap.org/search?{params}")
    return hits if isinstance(hits, list) else []


def photon_search(query: str, limit: int = 5) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "limit": limit, "lang": "es"})
    data = fetch_json(f"https://photon.komoot.io/api/?{params}")
    out = []
    for feat in data.get("features") or []:
        coords = feat.get("geometry", {}).get("coordinates") or []
        props = feat.get("properties") or {}
        if len(coords) < 2:
            continue
        lng, lat = float(coords[0]), float(coords[1])
        country = (props.get("country") or props.get("countrycode") or "").lower()
        if country and country not in {"argentina", "ar"}:
            continue
        out.append(
            {
                "lat": lat,
                "lng": lng,
                "display_name": ", ".join(
                    str(props[k])
                    for k in ("name", "street", "housenumber", "city", "state", "country")
                    if props.get(k)
                ),
                "type": props.get("osm_value") or props.get("type") or "",
                "name": props.get("name") or "",
                "source": "photon",
            }
        )
    return out


def score(hit: dict, cafe: dict) -> float:
    lat = float(hit["lat"])
    lng = float(hit.get("lon") or hit.get("lng"))
    if not in_argentina(lat, lng):
        return -100
    name = (hit.get("name") or hit.get("display_name") or "").lower()
    cafe_name = cafe["name"].lower()
    token = cafe_name.split()[0].lower()
    points = 0.0
    if token in name:
        points += 4
    if cafe_name in name:
        points += 6
    kind = (hit.get("type") or hit.get("class") or "").lower()
    extra = hit.get("extratags") or {}
    if kind in {"cafe", "coffee", "coffee_shop", "restaurant", "bakery"}:
        points += 3
    if extra.get("cuisine") in {"coffee_shop", "cafe"}:
        points += 2
    city = (cafe.get("neighborhood") or cafe.get("province") or "").lower()
    display = (hit.get("display_name") or "").lower()
    if city and city not in {"caba", "buenos aires"} and city in display:
        points += 2
    # Prefer named POIs over raw streets
    if hit.get("addresstype") in {"amenity", "shop", "building"}:
        points += 2
    if hit.get("osm_type") == "node":
        points += 0.5
    return points


def queries_for(cafe: dict) -> list[str]:
    name = cafe["name"]
    neigh = cafe.get("neighborhood") or ""
    prov = cafe.get("province") or ""
    place = neigh if neigh and neigh.upper() != "CABA" else ""
    qs = [
        f"{name} café {place} Argentina".strip(),
        f"{name} coffee {place} Argentina".strip(),
        f"{name} {place} {prov} Argentina".strip(),
        f"{name} {prov} Argentina".strip(),
    ]
    # drop empties / dupes
    seen = set()
    out = []
    for q in qs:
        q = " ".join(q.split())
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out


def pick(cafe: dict) -> dict | None:
    best = None
    best_score = 2.5
    for q in queries_for(cafe):
        try:
            hits = nominatim_search(q)
        except Exception as exc:
            print(f"  nominatim error {q}: {exc}")
            hits = []
        time.sleep(1.05)
        for hit in hits:
            hit = dict(hit)
            hit["lng"] = float(hit.get("lon") or hit.get("lng") or 0)
            hit["lat"] = float(hit["lat"])
            hit["source"] = "nominatim"
            s = score(hit, cafe)
            if s > best_score:
                best_score = s
                best = {**hit, "query": q, "score": s}
        if best and best_score >= 6:
            return best
    # Photon fallback
    for q in queries_for(cafe)[:2]:
        try:
            hits = photon_search(q)
        except Exception as exc:
            print(f"  photon error {q}: {exc}")
            hits = []
        time.sleep(0.4)
        for hit in hits:
            s = score(hit, cafe)
            if s > best_score:
                best_score = s
                best = {**hit, "query": q, "score": s}
    return best


def main() -> None:
    payload = json.loads(CAFES.read_text(encoding="utf-8"))
    results = {}
    for cafe in payload["cafes"]:
        rank = cafe["rank"]
        print(f"#{rank} {cafe['name']}")
        hit = pick(cafe)
        if hit:
            results[str(rank)] = {
                "name": cafe["name"],
                "lat": round(hit["lat"], 6),
                "lng": round(hit["lng"], 6),
                "address": hit.get("display_name") or "",
                "query": hit.get("query"),
                "score": hit.get("score"),
                "source": hit.get("source"),
                "type": hit.get("type") or hit.get("addresstype") or "",
            }
            print(f"  OK {results[str(rank)]['lat']},{results[str(rank)]['lng']} {results[str(rank)]['address'][:80]}")
        else:
            results[str(rank)] = {"name": cafe["name"], "failed": True}
            print("  FAIL")
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ok = sum(1 for v in results.values() if not v.get("failed"))
    print(f"Wrote {OUT} ({ok}/100)")


if __name__ == "__main__":
    main()
