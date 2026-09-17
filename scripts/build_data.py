#!/usr/bin/env python3
"""Build cafe dataset with curated + centroid coordinates (offline-friendly)."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "cafes.json"
ENRICH = ROOT / "data" / "enrichment.json"

PHOTO_POOL = [
    "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1511920170033-f8396924c348?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1447933601403-0c6688de566e?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1498804103079-a6351b050096?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1521017432531-fbd92d768814?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1600093463592-8e36ae95ef56?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1559305616-3f99cd43e353?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1493857671505-72967e2e2760?auto=format&fit=crop&w=800&q=80",
]

# Neighborhood / city centers used as anchors
CENTROIDS = {
    "colegiales": (-34.5733, -58.4490),
    "chacarita": (-34.5870, -58.4540),
    "palermo": (-34.5875, -58.4250),
    "palermo hollywood": (-34.5800, -58.4350),
    "palermo chico": (-34.5770, -58.4080),
    "puerto madero": (-34.6090, -58.3620),
    "san nicolás": (-34.6045, -58.3810),
    "villa crespo": (-34.5980, -58.4400),
    "caba": (-34.6037, -58.3816),
    "rosario": (-32.9442, -60.6505),
    "córdoba": (-31.4201, -64.1888),
    "santa cruz": (-50.3370, -72.2648),
    "el calafate": (-50.3370, -72.2648),
    "río negro": (-40.8135, -62.9967),
    "mar del plata": (-38.0055, -57.5426),
    "corrientes": (-27.4692, -58.8306),
    "wilde": (-34.7000, -58.3200),
    "la pampa": (-35.6650, -63.7580),
    "general pico": (-35.6566, -63.7568),
    "jujuy": (-24.1858, -65.2995),
    "neuquén": (-38.9516, -68.0591),
    "olivos": (-34.5075, -58.4860),
    "santa fe": (-31.6333, -60.7000),
    "salta": (-24.7821, -65.4232),
    "resistencia": (-27.4514, -58.9867),
    "mendoza": (-32.8895, -68.8458),
    "san juan": (-31.5375, -68.5364),
    "city bell": (-34.8680, -58.0450),
    "martínez": (-34.4880, -58.5080),
    "chaco": (-27.4514, -58.9867),
}

KNOWN = {
    1: {
        "lat": -34.573272,
        "lng": -58.448281,
        "address": "Teodoro García 2806, Colegiales",
        "image": "https://www.clarin.com/img/2026/09/16/VQY09ofgJ_1256x620__2.jpg",
        "description": "Tostadero y barra separados por un panel de vidrio. Sirven y tuestan su propio café, con grano colombiano de acidez media-alta y notas cítricas. Local minimalista frente a la vía del tren Mitre.",
    },
    2: {
        "lat": -34.5858,
        "lng": -58.4545,
        "address": "Av. Álvarez Thomas 764, Chacarita",
        "image": "https://www.lanacion.com.ar/resizer/v2/blanca-5WFSSALMXNHKHLMKKQ32CDAMOU.jpeg?auth=38d33f18c255f5014b2f188bc179ff5f2d31426747159b2014da51fa0192b1ed&width=800&height=600&quality=80&smart=true",
        "description": "Espacio íntimo y minimalista entre Colegiales y Chacarita. Menú dinámico de orígenes únicos según temporada, con foco en sostenibilidad y sesiones de vinilos.",
    },
    3: {
        "lat": -34.6095,
        "lng": -58.3630,
        "address": "Puerto Madero y Palermo",
        "image": "https://www.clarin.com/img/2026/09/16/NgUaif6x__720x0__1.jpg",
        "description": "Restaurante y cafetería de inspiración italiana. Granos de Brasil trabajados con Modo Barista Coffee Roasters: notas de frutos rojos, chocolate y almendra.",
    },
    4: {
        "lat": -34.5815,
        "lng": -58.4320,
        "address": "Palermo Hollywood y Villa Ortúzar",
        "image": "https://www.lanacion.com.ar/resizer/v2/vive-NSCMGRGWXJGXLAIWN4ZQCPCZ5I.jpeg?auth=c76aa734478db58cfeb8fe7ab8a9da0f59827cb5fd814f1656334df0f9edaf07&width=800&height=600&quality=80&smart=true",
        "description": "Tuestan y perfilan café de calidad de distintos orígenes, en filtrados y espresso. Dos locales: Palermo Hollywood y Villa Ortúzar.",
    },
    5: {
        "lat": -34.5885,
        "lng": -58.4520,
        "address": "Chacarita, CABA",
        "image": "https://www.lanacion.com.ar/resizer/v2/cuervo-se-ubico-en-el-quinto-QNTRC7ANQNDNPAIS7B2UCULCGY.jpeg?auth=2fe726ccd9291c68b4dc8c228724514803fdc9b7776ed9964a6b0b09123b1a8f&width=800&height=600&quality=80&smart=true",
        "description": "Fundado en 2016 por Agustín Caro y Pablo Tokatlian. Tuestan granos importados de distintos orígenes; hoy también tienen heladería.",
    },
    6: {
        "lat": -34.5775,
        "lng": -58.4085,
        "address": "Palermo Chico, CABA",
        "description": "Blanca en Palermo Chico: sexto puesto del ranking inaugural. Hermana conceptual de Blanca Studio, con foco en grano y atmósfera cuidada.",
    },
    7: {
        "lat": -34.6038,
        "lng": -58.3775,
        "address": "San Nicolás, CABA",
        "image": "https://www.clarin.com/img/2026/09/16/6VVHADCYE_720x0__1.jpg",
        "description": "Negro Cueva de Café: séptimo a nivel nacional y puesto 94 en The World's 100 Best Coffee Shops 2026.",
    },
    8: {
        "lat": -50.3395,
        "lng": -72.2700,
        "address": "El Calafate, Santa Cruz",
        "description": "Referente patagónico del ranking. Calafate Coffee Roasters llevó a Santa Cruz al top 10 nacional.",
    },
    9: {
        "lat": -34.5860,
        "lng": -58.4240,
        "address": "Palermo, CABA",
        "description": "Meme en Palermo cierra el top 10 con una propuesta de especialidad en uno de los barrios cafeteros más densos de Buenos Aires.",
    },
    10: {
        "lat": -34.5975,
        "lng": -58.4395,
        "address": "Villa Crespo, CABA",
        "description": "Raíz en Villa Crespo completa el top 10. Parte de la ola de especialidad porteña fuera del eje Palermo.",
    },
    28: {
        "lat": -34.5880,
        "lng": -58.4305,
        "address": "CABA",
        "description": "Surry Hills: puesto 28 nacional y 99 en The World's 100 Best Coffee Shops 2026.",
    },
    55: {
        "lat": -34.5872,
        "lng": -58.4258,
        "address": "CABA",
        "description": "Ninina, reconocida internacionalmente en ediciones anteriores, entra al top 100 nacional 2026.",
    },
    82: {
        "lat": -34.5855,
        "lng": -58.4220,
        "address": "Palermo, CABA",
        "description": "Sede Palermo de Ciro, que también ocupó el 3° puesto del ranking general con su propuesta italo-porteña.",
    },
}

RAW = [
    (1, "Tres", "Colegiales", "CABA"),
    (2, "Blanca Studio", "Chacarita", "CABA"),
    (3, "Ciro", "Puerto Madero y Palermo", "CABA"),
    (4, "Vive Café", "Palermo", "CABA"),
    (5, "Cuervo Café", "Chacarita", "CABA"),
    (6, "Blanca", "Palermo Chico", "CABA"),
    (7, "Negro", "San Nicolás", "CABA"),
    (8, "Calafate Coffee Roasters", "El Calafate", "Santa Cruz"),
    (9, "Meme", "Palermo", "CABA"),
    (10, "Raíz", "Villa Crespo", "CABA"),
    (11, "Fruto", "CABA", "CABA"),
    (12, "Lattente", "CABA", "CABA"),
    (13, "Ruffo", "Rosario", "Santa Fe"),
    (14, "Lab de Juju", "Rosario", "Santa Fe"),
    (15, "Parce Café Studio", "Córdoba", "Córdoba"),
    (16, "Standalone Coffee Lab", "CABA", "CABA"),
    (17, "Rita", "CABA", "CABA"),
    (18, "Casa Chacana", "Córdoba", "Córdoba"),
    (19, "Runge", "Rosario", "Santa Fe"),
    (20, "Flat & White", "CABA", "CABA"),
    (21, "Zulu Haus", "CABA", "CABA"),
    (22, "Primero Café", "CABA", "CABA"),
    (23, "Gota", "Rosario", "Santa Fe"),
    (24, "Wat Coffee", "CABA", "CABA"),
    (25, "Motofeca", "CABA", "CABA"),
    (26, "Ostia", "CABA", "CABA"),
    (27, "Vedra Café", "CABA", "CABA"),
    (28, "Surry Hills", "CABA", "CABA"),
    (29, "Cora Café", "CABA", "CABA"),
    (30, "The Coffee Store (Martínez)", "Martínez", "Buenos Aires"),
    (31, "Onno", "CABA", "CABA"),
    (32, "Café Delirante", "Río Negro", "Río Negro"),
    (33, "Lharmonie", "CABA", "CABA"),
    (34, "Café Heraldo", "Mar del Plata", "Buenos Aires"),
    (35, "Malcriada", "CABA", "CABA"),
    (36, "Punto Café", "CABA", "CABA"),
    (37, "Cofi Jaus", "CABA", "CABA"),
    (38, "Café Registrado", "CABA", "CABA"),
    (39, "Manifiesto", "CABA", "CABA"),
    (40, "Lab Tostadores", "CABA", "CABA"),
    (41, "Patio (City Bell)", "City Bell", "Buenos Aires"),
    (42, "Sosa Café", "CABA", "CABA"),
    (43, "Fomento Café", "CABA", "CABA"),
    (44, "Green Mug", "Mar del Plata", "Buenos Aires"),
    (45, "Hobby Café", "CABA", "CABA"),
    (46, "Canillita", "CABA", "CABA"),
    (47, "Krake", "Córdoba", "Córdoba"),
    (48, "Serafin", "Corrientes", "Corrientes"),
    (49, "Traje Café", "CABA", "CABA"),
    (50, "Arto", "Rosario", "Santa Fe"),
    (51, "Caffé Del Popolo", "Córdoba", "Córdoba"),
    (52, "Café Puzzi", "Wilde", "Buenos Aires"),
    (53, "Cafetino (General Pico)", "General Pico", "La Pampa"),
    (54, "Kaizen", "Jujuy", "Jujuy"),
    (55, "Ninina", "CABA", "CABA"),
    (56, "Cobin", "CABA", "CABA"),
    (57, "Doc Café", "CABA", "CABA"),
    (58, "The Tiny Coffee: Refugio", "Neuquén", "Neuquén"),
    (59, "Kuta", "Olivos", "Buenos Aires"),
    (60, "Paisa High Mountain Coffee", "Santa Cruz", "Santa Cruz"),
    (61, "Uno Dos Café", "CABA", "CABA"),
    (62, "Shiok Coffee Roasters", "Córdoba", "Córdoba"),
    (63, "Plantado Café", "CABA", "CABA"),
    (64, "Leto", "Santa Fe", "Santa Fe"),
    (65, "Café Boheme", "CABA", "CABA"),
    (66, "La Nieve", "Santa Cruz", "Santa Cruz"),
    (67, "Christen Coffee", "Santa Fe", "Santa Fe"),
    (68, "Birkin", "CABA", "CABA"),
    (69, "Daniel Bakery", "CABA", "CABA"),
    (70, "Salma Café", "CABA", "CABA"),
    (71, "Hacienda Coffee Company", "CABA", "CABA"),
    (72, "Merci Coffee Dealer", "CABA", "CABA"),
    (73, "Bulgaro", "CABA", "CABA"),
    (74, "Mr. Coffee", "Córdoba", "Córdoba"),
    (75, "Café LSA", "Salta", "Salta"),
    (76, "Passage Du Cafe", "Córdoba", "Córdoba"),
    (77, "Almendro", "Resistencia", "Chaco"),
    (78, "Fran Coffee Makers", "Mendoza", "Mendoza"),
    (79, "Feka", "Rosario", "Santa Fe"),
    (80, "Bicho Café", "CABA", "CABA"),
    (81, "Báltica Café", "CABA", "CABA"),
    (82, "Ciro Café (Palermo)", "Palermo", "CABA"),
    (83, "Sinsa Café", "CABA", "CABA"),
    (84, "Gabs Café", "CABA", "CABA"),
    (85, "Lon Philosophy", "CABA", "CABA"),
    (86, "Voltri", "CABA", "CABA"),
    (87, "Cobre Café", "CABA", "CABA"),
    (88, "Caffetos", "CABA", "CABA"),
    (89, "Ethiopia Café", "Córdoba", "Córdoba"),
    (90, "Estación Café Salta", "Salta", "Salta"),
    (91, "Juana House", "San Juan", "San Juan"),
    (92, "Korto Coffee House", "CABA", "CABA"),
    (93, "Rocco Cafe", "Santa Cruz", "Santa Cruz"),
    (94, "Ficus", "Santa Fe", "Santa Fe"),
    (95, "Café Copado", "Mendoza", "Mendoza"),
    (96, "Garden Coffee", "Santa Fe", "Santa Fe"),
    (97, "Aste Café Con Pasión", "Córdoba", "Córdoba"),
    (98, "Casa Pina", "CABA", "CABA"),
    (99, "Florian", "CABA", "CABA"),
    (100, "Habitat", "Mendoza", "Mendoza"),
]


def norm(text: str) -> str:
    return (
        text.lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )


def centroid_for(neighborhood: str, province: str):
    candidates = [neighborhood, province]
    # Prefer first matching phrase in neighborhood (e.g. "Puerto Madero y Palermo")
    neigh = norm(neighborhood)
    for key, coords in CENTROIDS.items():
        if norm(key) in neigh:
            return coords
    for candidate in candidates:
        n = norm(candidate)
        for key, coords in CENTROIDS.items():
            if n == norm(key) or norm(key) in n or n in norm(key):
                return coords
    return CENTROIDS["caba"]


def jitter(rank: int, lat: float, lng: float, spread: float = 0.012):
    angle = (rank * 137.508) % 360
    radius = 0.002 + (rank % 9) * (spread / 12)
    rad = math.radians(angle)
    return lat + radius * math.cos(rad), lng + radius * math.sin(rad)


def load_enrichment() -> dict:
    if not ENRICH.exists():
        return {"instagram": {}, "descriptions": {}}
    raw = json.loads(ENRICH.read_text(encoding="utf-8"))
    return {
        "instagram": {int(k): v for k, v in raw.get("instagram", {}).items()},
        "descriptions": {int(k): v for k, v in raw.get("descriptions", {}).items()},
    }


def default_description(name: str, neighborhood: str, province: str) -> str:
    if province.upper() == "CABA":
        place = neighborhood if neighborhood.upper() != "CABA" else "Buenos Aires"
        return f"Café de especialidad en {place}."
    if norm(province) == norm(neighborhood):
        return f"{name} es una cafetería de especialidad en {neighborhood}."
    return f"{name} es una cafetería de especialidad en {neighborhood}, {province}."


def nice_location(neighborhood: str, province: str) -> str:
    if not neighborhood or neighborhood.upper() == "CABA":
        return "Buenos Aires" if province.upper() == "CABA" else province
    if province.upper() == "CABA":
        return f"{neighborhood}, Buenos Aires"
    if neighborhood.lower() == province.lower():
        return neighborhood
    return f"{neighborhood}, {province}"


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    enrich = load_enrichment()
    results = []

    for rank, name, neighborhood, province in RAW:
        known = KNOWN.get(rank, {})
        if "lat" in known:
            lat, lng = known["lat"], known["lng"]
            source = "curated"
            address = known.get("address", f"{neighborhood}, {province}")
        else:
            base_lat, base_lng = centroid_for(neighborhood, province)
            # Spread CABA-generic pins around BA so the map is readable
            spread = 0.035 if norm(neighborhood) in {"caba"} else 0.01
            lat, lng = jitter(rank, base_lat, base_lng, spread=spread)
            source = "centroid"
            address = f"{neighborhood}, {province}"

        cafe = {
            "rank": rank,
            "name": name,
            "neighborhood": neighborhood,
            "province": province,
            "location": nice_location(neighborhood, province),
            "address": address,
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "image": known.get("image") or PHOTO_POOL[(rank - 1) % len(PHOTO_POOL)],
            "description": enrich["descriptions"].get(rank)
            or known.get("description")
            or default_description(name, neighborhood, province),
            "geocodeSource": source,
        }
        if rank in enrich["instagram"]:
            cafe["instagram"] = enrich["instagram"][rank]
        results.append(cafe)

    payload = {
        "title": "The Best Coffee Shops Argentina 2026",
        "source": "Clarín / La Nación / The Best Coffee Shops Argentina",
        "sources": [
            "https://www.clarin.com/gourmet/eligieron-100-mejores-cafeterias-argentina-numero-colegiales_0_iyNxz3mA6M.html",
            "https://www.lanacion.com.ar/sabado/las-mejores-cafeterias-argentinas-publicaron-el-ranking-con-las-mejores-quienes-estan-en-el-top-ten-nid16092026/",
            "https://x.com/clarincom/status/2100394304502141174",
        ],
        "count": len(results),
        "cafes": results,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} with {len(results)} cafes")


if __name__ == "__main__":
    main()
