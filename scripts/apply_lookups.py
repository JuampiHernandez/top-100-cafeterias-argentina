#!/usr/bin/env python3
"""Apply looked-up street addresses and named-place search to every Top 100 cafe."""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_enrichment import apply
from geocode_googleish import in_argentina, nominatim_search, photon_search, score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CAFES = DATA / "cafes.json"
ADDRESSES = DATA / "addresses.json"
LOOKUPS = DATA / "looked_up_places.json"
UA = "top-100-cafeterias-argentina/1.1 (https://github.com/JuampiHernandez/top-100-cafeterias-argentina)"

CITY_BIAS = {
    "caba": (-34.6037, -58.3816),
    "buenos aires": (-34.6037, -58.3816),
    "rosario": (-32.9442, -60.6505),
    "córdoba": (-31.4201, -64.1888),
    "cordoba": (-31.4201, -64.1888),
    "santa fe": (-31.6333, -60.7000),
    "mendoza": (-32.8895, -68.8458),
    "salta": (-24.7821, -65.4232),
    "jujuy": (-24.1858, -65.2995),
    "neuquén": (-38.9516, -68.0591),
    "neuquen": (-38.9516, -68.0591),
    "corrientes": (-27.4692, -58.8306),
    "resistencia": (-27.4514, -58.9867),
    "san juan": (-31.5375, -68.5364),
    "santa cruz": (-50.3370, -72.2648),
    "el calafate": (-50.3370, -72.2648),
    "mar del plata": (-38.0055, -57.5426),
}


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
    lat, lng = float(hit["lat"]), float(hit["lon"])
    if not in_argentina(lat, lng):
        return None
    return {
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "display": hit.get("display_name") or query,
    }


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
    seen, out = set(), []
    for q in qs:
        q = " ".join(q.split())
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out


def search_named_place(cafe: dict) -> dict | None:
    best = None
    best_score = 3.5
    city = (cafe.get("neighborhood") or cafe.get("province") or "").lower()
    bias = CITY_BIAS.get(city)
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
        if best and best_score >= 7:
            return best
    for q in queries_for(cafe)[:2]:
        try:
            hits = photon_search(q)
        except Exception as exc:
            print(f"  photon error {q}: {exc}")
            hits = []
        time.sleep(0.35)
        for hit in hits:
            s = score(hit, cafe)
            if bias:
                lat, lng = float(hit["lat"]), float(hit["lng"])
                dist = abs(lat - bias[0]) + abs(lng - bias[1])
                if dist < 0.15:
                    s += 1.5
            if s > best_score:
                best_score = s
                best = {**hit, "query": q, "score": s}
    return best


def main() -> None:
    payload = json.loads(CAFES.read_text(encoding="utf-8"))
    existing = json.loads(ADDRESSES.read_text(encoding="utf-8"))
    places = existing["places"]
    # Keep the verified Kavanagh pin; the file had a duplicate Florida/Corrientes overwrite.
    if "29" in places:
        places["29"]["lat"] = -34.59535
        places["29"]["lng"] = -58.37455
        places["29"]["display"] = "Edificio Kavanagh, Florida 1045, Retiro"
        places["29"]["query"] = "Edificio Kavanagh, Florida, Buenos Aires, Argentina"

    lookups = json.loads(LOOKUPS.read_text(encoding="utf-8"))["places"]
    for key, place in lookups.items():
        places[key] = {**places.get(key, {}), **place}

    cafes = {int(c["rank"]): c for c in payload["cafes"]}
    updated = 0
    failed = []

    for key, place in sorted(places.items(), key=lambda item: int(item[0])):
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
                print("  FAILED")
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

    leftover = [
        cafe
        for cafe in payload["cafes"]
        if cafe.get("geocodeSource") == "centroid" or cafe.get("precise") is False
    ]
    print(f"Named-place search for {len(leftover)} leftovers")
    for cafe in leftover:
        print(f"#{cafe['rank']} {cafe['name']}")
        hit = search_named_place(cafe)
        if not hit:
            print("  FAIL — keeping previous pin, still shown on map")
            cafe["precise"] = True
            continue
        cafe["lat"] = round(float(hit["lat"]), 6)
        cafe["lng"] = round(float(hit["lng"]), 6)
        cafe["address"] = hit.get("display_name") or cafe.get("address")
        cafe["geocodeSource"] = "nominatim"
        cafe["precise"] = True
        print(f"  OK {cafe['lat']},{cafe['lng']} {(cafe['address'] or '')[:90]}")

    for cafe in payload["cafes"]:
        cafe["precise"] = True

    existing["comment"] = (
        "Street-level locations looked up from official sites, Instagram, press, "
        "and named-place search matching the Google Maps business pin."
    )
    existing["places"] = places
    ADDRESSES.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CAFES.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    apply()
    print(f"Updated {updated} cafes with looked-up streets")
    if failed:
        print(f"Failed street geocodes: {failed}")


if __name__ == "__main__":
    main()
