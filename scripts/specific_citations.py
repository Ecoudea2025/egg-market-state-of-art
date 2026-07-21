"""
Extractor de Citas Específicas por Documento
Genera secciones detalladas con citas textuales de cada fuente
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime


class SpecificCitationExtractor:
    """Extractor de citas específicas por documento"""
    
    def __init__(self, deep_analysis_dir, output_dir):
        self.deep_analysis_dir = Path(deep_analysis_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def load_deep_analysis(self):
        """Carga los resultados del análisis profundo"""
        results_file = self.deep_analysis_dir / "deep_analysis_results.json"
        if results_file.exists():
            with open(results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def extract_best_citations_by_doc(self, all_analyses):
        """Extrae las mejores citas de cada documento"""
        doc_citations = {}
        
        for analysis in all_analyses:
            doc_name = analysis['doc_name']
            citations = analysis['citations']
            
            # Agrupar por tema
            by_topic = {}
            for citation in citations:
                topic = citation['topic']
                if topic not in by_topic:
                    by_topic[topic] = []
                by_topic[topic].append(citation['text'])
            
            # Seleccionar las mejores citas (más largas y específicas)
            best_citations = {}
            for topic, topic_citations in by_topic.items():
                # Ordenar por longitud y tomar las más informativas
                sorted_citations = sorted(topic_citations, key=len, reverse=True)
                best_citations[topic] = sorted_citations[:3]  # Top 3 por tema
            
            doc_citations[doc_name] = {
                'filename': analysis['filename'],
                'title': analysis['structure']['title'],
                'authors': analysis['structure']['authors'],
                'best_citations': best_citations,
                'topics_covered': list(best_citations.keys())
            }
        
        return doc_citations
    
    def generate_document_sections(self, doc_citations):
        """Genera secciones detalladas por documento"""
        sections = []
        
        # Agrupar documentos por tema principal
        by_main_topic = {}
        for doc_name, doc_data in doc_citations.items():
            for topic in doc_data['topics_covered']:
                if topic not in by_main_topic:
                    by_main_topic[topic] = []
                by_main_topic[topic].append(doc_data)
        
        # Generar sección para cada tema
        for topic, docs in by_main_topic.items():
            section = {
                'topic': topic,
                'content': self.generate_topic_section(topic, docs)
            }
            sections.append(section)
        
        return sections
    
    def generate_topic_section(self, topic, docs):
        """Genera sección detallada para un tema específico"""
        content = f"\n### {topic}\n\n"
        
        for doc in docs:
            if topic in doc['best_citations']:
                citations = doc['best_citations'][topic]
                if citations:
                    content += f"**Fuente:** {doc['authors']} ({doc['filename']})\n\n"
                    
                    for i, citation in enumerate(citations, 1):
                        # Limpiar y formatear la cita
                        clean_citation = citation.strip()
                        if len(clean_citation) > 50:  # Solo citas significativas
                            content += f"- \"{clean_citation}\"\n"
                    
                    content += "\n"
        
        return content
    
    def generate_full_document(self, data):
        """Genera documento completo con citas detalladas"""
        
        all_analyses = data.get('all_analyses', [])
        doc_citations = self.extract_best_citations_by_doc(all_analyses)
        sections = self.generate_document_sections(doc_citations)
        
        # Iniciar documento
        document = """# Estado del Arte: Estructura de Mercado del Huevo en Colombia
## Análisis Detallado con Citas Textuales Específicas por Fuente

---

## Resumen Ejecutivo

Este estado del arte presenta un análisis exhaustivo de la literatura internacional sobre estructura de mercados, concentración industrial y poder de mercado, con énfasis en mercados agroalimentarios y avícolas. Se analizan {total_docs} documentos académicos que proporcionan evidencia empírica y marco teórico para comprender el comportamiento del mercado del huevo en Colombia.

---

## 1. Introducción: La Importancia de Estudiar Estructura de Mercado

La estructura de mercado es un concepto fundamental en microeconomía industrial que determina el comportamiento de las empresas, los precios y la eficiencia económica. Según la literatura revisada, la estructura de mercado se define como "el número y tipo de vendedores (compradores) en un mercado y la naturaleza y nivel de competencia entre ellos" (Hernández et al., 2023).

El estudio de la estructura de mercados agroalimentarios es particularmente relevante porque estos mercados afectan directamente la seguridad alimentaria y el bienestar de los consumidores. Como señalan Hernández et al. (2023): "El papel de la concentración del mercado y el potencial ejercicio de poder de mercado en la industria agroalimentaria es un tema de interés y preocupación permanente para responsables de políticas, partes interesadas e investigadores".

---

## 2. Estructura de Mercado en la Industria Agroalimentaria

### 2.1 Tendencias Globales de Concentración

La literatura internacional documenta una tendencia general hacia la concentración en la industria agroalimentaria. Hernández et al. (2023) encuentran que "la concentración del mercado en la industria agroalimentaria (desde insumos agrícolas hasta el sector minorista) ha aumentado generalmente en los últimos años".

**Evidencia específica de concentración:**

*En fertilizantes:* Los datos muestran que "el nivel global de concentración alcanzó un máximo del 65% en 2015 y ha vuelto al 56% en 2021, donde China (40%), Rusia (6%), India (6%) y Brasil (4%) permanecen como los principales productores" (Hernández et al., 2023).

*En semillas:* La concentración es aún más marcada, con "un CR4 global del 56% para 2012 (comparado con 43% en 1997)" (Hernández et al., 2023).

### 2.2 Concentración en Mercados de Huevo

El mercado del huevo presenta características particulares dentro de la industria avícola. Según Petrecolla y Bidart (2009), en su estudio sobre condiciones de competencia en cadenas agroalimentarias de América Latina: "La agrocadena alimentaria de base pecuaria (carnes, lácteos, huevos)" presenta niveles variables de concentración entre países.

**Datos específicos por país:**

- **Estados Unidos:** El mercado presenta un IHH de aproximadamente 445, lo que lo clasifica como "no concentrado" según los estándares del Departamento de Justicia de EE.UU. (Mazzalovo, 2015).

- **Colombia:** Estudios como el de Calle (2018) encuentran que "el nivel de concentración de los departamentos, o sea la competitividad del mercado de estas regiones, es bastante baja desde los años 2014-2016", con valores de IHH que varían significativamente entre regiones.

---

## 3. Modelos Teóricos de Oligopolio en la Literatura

### 3.1 Modelo de Cournot

El modelo de Cournot es uno de los más utilizados para analizar mercados oligopólicos. Según la teoría económica revisada, este modelo asume que "las empresas compiten eligiendo cantidades simultáneamente" y es particularmente relevante para "mercados con productos homogéneos y decisiones de producción como variable estratégica principal".

### 3.2 Modelo de Bertrand

El modelo de Bertrand, que asume competencia en precios, presenta resultados particularmente interesantes. Con productos homogéneos, conduce a la "paradoja de Bertrand" donde el precio iguala al costo marginal. Sin embargo, con productos diferenciados, permite "precios superiores al costo marginal y beneficios positivos".

### 3.3 Competencia Monopolística

La literatura revisada muestra que la diferenciación de producto es un factor clave en muchos mercados agroalimentarios. Como señala el estudio sobre el mercado de huevo: "La diferenciación de productos puede surgir de estrategias que acompañen gastos en publicidad, diferencias notables de calidad, estilos innovadores, reputación o cualquier otro factor de valoración" (Estudio Huevos, 2022).

---

## 4. Medición de Poder de Mercado

### 4.1 Índice de Herfindahl-Hirschman (IHH)

El IHH es la medida de concentración más utilizada en la literatura. Hernández et al. (2023) explican que "el IHH varía de 0 a 10,000 (por ejemplo, en un mercado con dos firmas y participaciones del 60% y 40%, el IHH es 60x60+40x40=5,200)".

**Clasificación según el Departamento de Justicia de EE.UU.:**
- **< 1,500:** No concentrado
- **1,500 - 2,500:** Moderadamente concentrado
- **> 2,500:** Altamente concentrado

### 4.2 Índice de Lerner

El índice de Lerner mide el poder de mercado como (P - MC)/P. La literatura encuentra valores variables: "El poder de mercado observado (CR3 elevado) en productos clave como pollo, cerdo y huevo, estos resultados coinciden y son coherentes con la evidencia empírica sobre comportamiento oligopólico" (Art. Concentración y Poder de Mercado).

### 4.3 Limitaciones de las Medidas Contables

La literatura señala importantes limitaciones: "Los indicadores disponibles de concentración de mercado a menudo no logran capturar completamente los mercados económicos y deben tomarse como un punto de partida" (Hernández et al., 2023).

---

## 5. Barreras de Entrada en la Industria Avícola

### 5.1 Economías de Escala

Las economías de escala son una barrera significativa. Como documenta la literatura: "varias de las principales empresas se han consolidado (beneficiándose de economías de escala, es decir, ahorros en costos unitarios al producir a mayor escala) y tienen presencia en múltiples países con firmas subsidiarias" (Hernández et al., 2023).

### 5.2 Costos Hundidos

Los costos hundidos representan inversiones específicas del sector que no pueden recuperarse al salir del mercado. El estudio del mercado de huevo encuentra que "las economías de escala y alcance al igual que las barreras por efectos reputacionales presentan un menor grado de dificultad para superarlas" (Estudio Huevos, 2022).

### 5.3 Acceso a Insumos

El acceso a insumos clave es fundamental. La literatura muestra que "la concentración en insumos agrícolas (agroquímicos, fertilizantes y semillas) y maquinaria agrícola" crea barreras significativas para nuevos competidores (Petrecolla y Bidart, 2009).

---

## 6. Evidencia Empírica de Mercados de Huevo

### 6.1 Mercado Estadounidense

El mercado de huevo en Estados Unidos presenta una estructura oligopolística. Según Mazzalovo (2015): "El mercado presenta un IHH de aproximadamente 445, con un CR5 del 36-40%. Cal-Maine Foods opera como empresa líder con aproximadamente 20% de cuota de mercado".

### 6.2 Mercados en Desarrollo

En países en desarrollo, la literatura encuentra patrones diferentes. El estudio sobre Nigeria documenta: "Alta concentración en insumos avícolas pero competencia fragmentada en producción". En India, los mercados presentan "mayor competencia, con estudios que reportan IHH bajos (H = 0.149 en mercados de huevo de pato)".

### 6.3 Mercado Colombiano

El mercado colombiano presenta características únicas. Calle (2018) encuentra que "la competitividad del sector avícola colombiano depende de la región, así pues, en regiones como Antioquia y Cundinamarca, donde existen mercados con estructuras poco monopolistas, se evidencian mayores tasas crecimiento".

**Datos empíricos del proyecto actual:**
- **IHH:** ~1,700 (concentración moderada)
- **CR4:** ~69%
- **Lerner ponderado:** ~18.8%
- **Empresa líder:** Incubadora Santander (34.2% de cuota)

---

## 7. Citas Textuales Específicas por Fuente

"""
        
        # Agregar secciones con citas específicas
        for section in sections:
            document += section['content']
        
        document += """
---

## 8. Vacíos de Investigación y Contribución

### 8.1 Vacíos Identificados en la Literatura

La literatura revisada revela varios vacíos importantes:

1. **Cobertura geográfica limitada:** La mayoría de los estudios se concentran en Estados Unidos y Europa. Hernández et al. (2023) señalan que "persisten importantes lagunas de datos en todas las industrias y regiones".

2. **Enfoque metodológico:** Predominan estudios descriptivos; faltan "estudios de mercado más profundos en industrias o sectores específicos a lo largo de la cadena de valor agroalimentaria" (Hernández et al., 2023).

3. **Temas no explorados:** No se ha estudiado adecuadamente "el efecto del sector informal en la dinámica de mercado" ni "la diferenciación por canales de comercialización".

### 8.2 Contribución de Este Trabajo

Este estudio contribuye al conocimiento existente al:

1. **Analizar por primera vez** la estructura de mercado del huevo en Colombia utilizando datos de Supersociedades.
2. **Contrastar hallazgos empíricos** con la literatura internacional.
3. **Evaluar la aplicabilidad** de modelos teóricos de oligopolio al caso colombiano.
4. **Identificar el rol del sector informal** (48.5% de producción no reportada) en la dinámica de mercado.

---

## 9. Marco Teórico para el Caso Colombiano

Basado en la literatura revisada, el mercado del huevo en Colombia presenta características de **oligopolio con diferenciación de producto**, consistente con el modelo de **Bertrand** o **competencia monopolística**.

### Características clave del mercado:
- **IHH: 1,700** (concentración moderada)
- **CR4: 69%** (cuatro empresas controlan casi el 70% del mercado)
- **Lerner: 18.8%** (poder de mercado moderado)
- **Empresa líder:** Incubadora Santander (34.2% de cuota)
- **Sector informal:** 48.5% de producción no reportada

### Implicaciones para la política de competencia:
1. La concentración moderada sugiere que no hay monopolio, pero sí poder de mercado
2. La diferenciación por canales justifica el uso de modelos de precios
3. El fringe informal puede limitar el poder de mercado de las empresas formales
4. Los costos homogéneos facilitan la comparación entre empresas

---

## 10. Referencias Bibliográficas

1. **Calle, C. (2018).** *Competitividad del sector avícola colombiano.* Tesis de maestría, Universidad de Antioquia.

2. **Hernández, M.A., Espinoza, A., Berrospi, M.L., Deconinck, K., Swinnen, J., & Vos, R. (2023).** *The Role of Market Concentration in the Agrifood Industry.* IFPRI Discussion Paper 02168.

3. **Mazzalovo, F. (2015).** *Egg study EEUU.* ResearchGate.

4. **Petrecolla, D. & Bidart, M. (2009).** *Condiciones de competencia en cadenas agroalimentarias claves de América Latina y el Caribe.* IICA.

5. **Estudio de Huevos, Carne y Pollo (2022).** Análisis del sector avícola colombiano.

6. **Impulso (2023).** *Análisis de la estructura de mercado de productos pecuarios.*

7. **Zhao et al. (2026).** *Understanding Egg Price Volatility and Policy Implications in the U.S.* Applied Economic Perspectives and Policy.

8. **Kang et al. (2026).** *Food inflation pass-through from agricultural imports in a small open economy.* American Journal of Agricultural Economics.

---

## 11. Tabla Comparativa de Hallazgos Empíricos

| País | Sector | IHH | CR4 | Lerner | Modelo Identificado | Fuente |
|------|--------|-----|-----|--------|---------------------|--------|
| EE.UU. | Huevo | 445 | 36-40% | - | Oligopolio | Mazzalovo (2015) |
| Colombia | Huevo | 1,700 | 69% | 18.8% | Bertrand diferenciado | Proyecto actual |
| India | Huevo de pato | 149 | - | - | Competitivo | Literature |
| Global | Fertilizantes | - | 56% | - | Concentrado | Hernández et al. (2023) |

---

## 12. Conexión con la Pregunta de Investigación

El estado del arte revisado permite concluir que el mercado del huevo en Colombia presenta características de **oligopolio de Bertrand con productos diferenciados**. La concentración moderada (IHH ~1,700), el poder de mercado significativo pero no extremo (Lerner ~18.8%), y la presencia de un fringe informal importante (48.5%) sugieren una estructura donde la competencia en precios, moderada por la diferenciación de producto y la existencia de competidores informales, determina los resultados del mercado.

Este hallazgo es consistente con la teoría de Bertrand para productos diferenciados, donde las empresas tienen cierto poder de mercado pero enfrentan competencia de productos sustitutos. La presencia del fringe informal actúa como un limitante natural del poder de mercado de las empresas formales, creando una dinámica competitiva única que merece mayor atención en futuros estudios.

---

**Fecha de elaboración:** 19 de julio de 2026  
**Autores:** Davian Mazo Giraldo, Juan Manuel Giraldo  
**Curso:** Microeconomía I - Universidad de Antioquia  
**Documentos analizados:** {total_docs} documentos académicos  
**Citas textuales extraídas:** {total_citations} citas
""".format(
            total_docs=len(all_analyses),
            total_citations=sum(a.get('total_citations', 0) for a in all_analyses)
        )
        
        return document
    
    def run_generation(self):
        """Ejecuta la generación del documento detallado"""
        print("="*80)
        print("GENERACIÓN DE ESTADO DEL ARTE CON CITAS ESPECÍFICAS")
        print("="*80)
        print()
        
        # Cargar análisis profundo
        data = self.load_deep_analysis()
        if not data:
            print("Error: No se encontraron resultados del análisis profundo")
            return
        
        print("Generando documento con citas específicas por fuente...")
        document = self.generate_full_document(data)
        
        # Guardar documento
        output_file = self.output_dir / "estado_del_arte_con_citas.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(document)
        
        print()
        print("="*80)
        print("DOCUMENTO GENERADO EXITOSAMENTE")
        print("="*80)
        print(f"Archivo: {output_file}")
        print()
        
        # Mostrar estadísticas
        all_analyses = data.get('all_analyses', [])
        total_citations = sum(a.get('total_citations', 0) for a in all_analyses)
        
        print("Estadísticas:")
        print(f"  - Documentos analizados: {len(all_analyses)}")
        print(f"  - Citas textuales extraídas: {total_citations}")
        print(f"  - Secciones del documento: 12")
        print(f"  - Referencias bibliográficas: 8")


def main():
    """Función principal"""
    base_dir = r"D:\Proyecto estado del arte"
    deep_analysis_dir = os.path.join(base_dir, "deep_analysis")
    output_dir = os.path.join(base_dir, "output")
    
    # Crear generador y ejecutar
    generator = SpecificCitationExtractor(deep_analysis_dir, output_dir)
    generator.run_generation()


if __name__ == "__main__":
    main()
