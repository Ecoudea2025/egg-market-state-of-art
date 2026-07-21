# Estado del Arte: Mercado del Huevo en Colombia

Investigacion en microeconomia aplicada sobre el mercado del huevo en Colombia. Este repositorio contiene scripts de extraccion automatica de citas desde documentos academicos, filtrado semantico con puntuacion de calidad, y analisis comparativo de la literatura.

## Estructura del Proyecto

```
├── scripts/                  # Scripts de procesamiento
│   ├── extract_pdfs.py       # Extrae texto de PDFs academicos
│   ├── citation_filter.py    # Filtro semantico con scoring de calidad
│   ├── generate_comparative.py # Analisis comparativo
│   ├── theoretical_synthesis.py # Sintesis de modelos (Bertrand vs Cournot)
│   ├── deep_analysis.py      # Extraccion profunda de citas
│   ├── generate_web_data.py  # Genera datos para la web D3.js
│   └── prepare_web_data.py   # Genera JSONs para GitHub Pages
├── docs/                     # Sitio web (GitHub Pages)
│   ├── index.html            # Mapa mental interactivo + metricas
│   ├── citas.html            # Tabla interactiva de citas
│   ├── documentos.html       # Lista de documentos con resumen
│   ├── estado-del-arte.html  # Documento markdown renderizado
│   ├── styles.css            # Estilos dark mode
│   ├── shared.js             # Utilidades JS compartidas
│   └── data/                 # Datos en formato JSON/JS
├── filtered_analysis/        # Output del filtrado
│   ├── citations_filtered.json  # 323 citas con calidad verificada
│   ├── findings_summary.md      # Resumen de hallazgos
│   └── estado_del_arte_limpio.md # Estado del arte completo
└── web/                      # Visualizacion D3.js original
```

## Estadisticas del Filtrado

| Metrica | Valor |
|---------|-------|
| Documentos analizados | 27 |
| Citas extraidas (raw) | 3,213 |
| Citas aceptadas | 323 (10%) |
| Alta calidad | 121 |
| Media calidad | 112 |
| Baja calidad | 90 |

## Sitio Web (GitHub Pages)

Disponible en: `https://tu-usuario.github.io/egg-market-state-of-art/`

Incluye:
- **Mapa mental interactivo** con D3.js: 35 nodos (1 central, 9 temas, 25 documentos)
- **Tabla de citas** con filtros por calidad, tema y busqueda
- **Documentos** con resumen y distribucion de calidad
- **Estado del Arte** renderizado desde markdown

## Ejecutar Localmente

```bash
# Instalar dependencias
pip install -r requirements.txt

# Extraer texto de PDFs
python scripts/extract_pdfs.py

# Filtrar citas con validacion semantica
python scripts/citation_filter.py

# Preparar datos para la web
python scripts/prepare_web_data.py

# Servir el sitio localmente
cd docs
python -m http.server 8080
```

### Pipeline completo

```bash
python scripts/extract_pdfs.py         # -> extracted_text/
python scripts/deep_analysis.py        # -> deep_analysis/
python scripts/citation_filter.py      # -> filtered_analysis/
python scripts/prepare_web_data.py     # -> docs/data/
```

## Dependencias

```
# Python (para procesamiento)
# No requiere librerias externas para la web (HTML/CSS/JS puro)

# Para regenerar datos:
pandas>=2.0.0
```

## Temas Cubiertos

- Concentracion de mercado (IHH, CR4)
- Competencia y poder de mercado
- Oligopolio (Bertrand vs Cournot)
- Barreras de entrada
- Elasticidades
- Precios y transmision de precios
- Economias de escala

## Fuentes Academicas

27 documentos procesados de fuentes como:
- Fenavi / Superintendencia de Competencia de El Salvador
- American Journal of Agricultural Economics
- Agricultural Economics and Development
- Applied Economic Perspectives and Policy
- Sustainability (MDPI)
- Economies (MDPI)
- Tesis academicas (Filipinas, Etiopia, Colombia)

---

Proyecto desarrollado para el curso de Microeconomia. Universidad de Antioquia.
