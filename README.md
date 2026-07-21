# Estado del Arte: Mercado del Huevo en Colombia

Investigacion en microeconomia aplicada sobre el mercado del huevo en Colombia. Este repositorio contiene dos proyectos complementarios:

1. **Estado del Arte** - Extraccion automatica de citas, filtrado semantico y visualizacion interactiva
2. **Dashboard Financiero** - Analisis de datos del sector avicola colombiano (SIREM, elasticidades, simulaciones)

## Sitio Web

Disponible en GitHub Pages: https://ecoudea2025.github.io/egg-market-state-of-art/

| Pagina | Descripcion |
|--------|-------------|
| **Inicio** | Mapa mental interactivo con 35 nodos D3.js + metricas |
| **Citas** | 323 citas verificadas con filtros y export CSV |
| **Documentos** | 25 documentos con resumen, barras de calidad y citas |
| **Estado del Arte** | Documento academico completo renderizado |

---

## Estructura del Repositorio

```
├── docs/                     # Sitio web (GitHub Pages)
│   ├── index.html            # Landing: mapa mental + metricas + graficos
│   ├── citas.html            # Tabla interactiva de citas
│   ├── documentos.html       # Documentos con expanders
│   ├── estado-del-arte.html  # Markdown renderizado
│   ├── styles.css            # Dark mode responsive
│   ├── shared.js             # Navegacion y utilidades
│   └── data/                 # JSONs y JS de datos
│
├── dashboard/                # Dashboard Financiero Streamlit
│   ├── app.py                # Entry point
│   ├── mercado.py            # Datos del mercado (precios, elasticidades)
│   ├── comparacion.py        # Comparacion multi-empresa
│   ├── simulacion.py         # Simulacion economica (Cournot, Bertrand)
│   ├── ingesta.py            # Gestion de datos
│   ├── preparar_datos.py     # Preparacion inicial de datos
│   ├── data/                 # CSV de datos financieros
│   └── modelos_economicos/   # Modelos de oligopolio
│
├── scripts/                  # Scripts de procesamiento
│   ├── extract_pdfs.py       # Extrae texto de PDFs academicos
│   ├── citation_filter.py    # Filtro semantico con scoring de calidad
│   ├── generate_comparative.py # Analisis comparativo
│   ├── theoretical_synthesis.py # Sintesis Cournot vs Bertrand
│   ├── deep_analysis.py      # Extraccion profunda de citas
│   └── prepare_web_data.py   # Genera JSONs para el sitio
│
├── filtered_analysis/        # Output del filtrado de citas
├── summaries/                # Resumenes por documento
├── comparisons/              # Analisis comparativos
├── synthesis/                # Sintesis y gaps
└── web/                      # Visualizacion D3.js original
```

---

## Dashboard Financiero (Streamlit)

### Caracteristicas

- **Grafico Temporal**: Series financieras de 15 empresas avicolas (2015-2025)
- **Comparacion Multi-Empresa**: Benchmarking de indicadores contables
- **Datos del Mercado**: Precios, produccion, consumo, elasticidades de FENAVI/DANE
- **Simulacion Economica**: Modelos Cournot, Bertrand y Stackelberg
- **Gestion de Datos**: Carga de PDFs y procesamiento

### Ejecutar Dashboard

```bash
# Instalar dependencias
pip install streamlit pandas plotly numpy

# Preparar datos (primera vez)
cd dashboard
python preparar_datos.py

# Ejecutar
streamlit run app.py
```

### Fuente de Datos

- **Superintendencia de Sociedades** (SIREM): Estados financieros 2015-2025
- **FENAVI**: Precios, produccion y consumo del sector avicola
- **DANE**: IPC, salario minimo y elasticidades

---

## Estado del Arte (GitHub Pages)

### Estadisticas del Filtrado

| Metrica | Valor |
|---------|-------|
| Documentos analizados | 27 |
| Citas extraidas (raw) | 3,213 |
| Citas aceptadas | 323 (10%) |
| Alta calidad | 121 |
| Media calidad | 112 |
| Baja calidad | 90 |

### Pipeline de Procesamiento

```bash
# Extraer texto de PDFs
python scripts/extract_pdfs.py

# Extraer citas y analizar
python scripts/deep_analysis.py

# Filtrar y validar calidad
python scripts/citation_filter.py

# Preparar datos para la web
python scripts/prepare_web_data.py
```

### Servir el Sitio Localmente

```bash
cd docs
python -m http.server 8080
# Abrir http://localhost:8080
```

---

## Temas Cubiertos

- **Concentracion de mercado** (IHH, CR4, Lerner)
- **Competencia y poder de mercado** en el sector avicola
- **Oligopolio** (Bertrand vs Cournot vs Stackelberg)
- **Barreras de entrada** legales y estructurales
- **Elasticidades** precio, cruzada e ingreso
- **Transmision de precios** en la cadena agroalimentaria
- **Economias de escala** y eficiencia productiva

---

## Fuentes Academicas

27 documentos procesados de fuentes como:
- Fenavi / Superintendencia de Competencia de El Salvador
- American Journal of Agricultural Economics
- Agricultural Economics and Development (Iran)
- Applied Economic Perspectives and Policy (EE.UU.)
- Sustainability (MDPI)
- Economies (MDPI)
- Tesis academicas (Filipinas, Etiopia, Colombia, Pakistan)

---

Proyecto desarrollado para el curso de Microeconomia. Universidad de Antioquia.
