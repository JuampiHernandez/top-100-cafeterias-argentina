# Top 100 cafeterías de Argentina

Mapa del ranking **The Best Coffee Shops Argentina 2026**. Lista, filtros, fichas y un mapa de Google My Maps para llevarte las 100.

App de [Juampi](https://www.instagram.com/juampihernandezz/).

## Abrir en local

```bash
python3 -m http.server 5173
```

Después [http://localhost:5173](http://localhost:5173).

Para regenerar el JSON, el KML y el CSV:

```bash
python3 scripts/apply_enrichment.py
```

`scripts/build_data.py` vuelve a armar el dataset base. No hace falta para correr la app.

## Datos

Las coordenadas del top usan direcciones publicadas. El resto está cerca del centro del barrio o la ciudad, para que el mapa nacional se lea. Las fotos destacadas salen de Clarín y La Nación. El resto es stock de Unsplash.

Instagram solo cuando el handle se pudo verificar. Si falta uno, no está inventado.

## Fuentes

- [Clarín](https://www.clarin.com/gourmet/eligieron-100-mejores-cafeterias-argentina-numero-colegiales_0_iyNxz3mA6M.html)
- [La Nación](https://www.lanacion.com.ar/sabado/las-mejores-cafeterias-argentinas-publicaron-el-ranking-con-las-mejores-quienes-estan-en-el-top-ten-nid16092026/)
