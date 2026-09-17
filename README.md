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

Las coordenadas con dirección de calle salen de sitios oficiales, Instagram y notas de prensa, geocodificadas con Nominatim. Si una ficha de CABA no tiene dirección publicada, **no se pinta en el mapa**: antes se las esparcía alrededor de Plaza de Mayo y parecía que el Microcentro estaba lleno de cafeterías. El resto del país, si solo sabemos la ciudad, sigue cerca del centro de esa ciudad.

Para regenerar pins con direcciones verificadas:

```bash
python3 scripts/apply_addresses.py
```

Las fotos destacadas salen de Clarín y La Nación. El resto es stock de Unsplash.

Instagram solo cuando el handle se pudo verificar. Si falta uno, no está inventado.

## Fuentes

- [Clarín](https://www.clarin.com/gourmet/eligieron-100-mejores-cafeterias-argentina-numero-colegiales_0_iyNxz3mA6M.html)
- [La Nación](https://www.lanacion.com.ar/sabado/las-mejores-cafeterias-argentinas-publicaron-el-ranking-con-las-mejores-quienes-estan-en-el-top-ten-nid16092026/)
