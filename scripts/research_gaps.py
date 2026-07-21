"""
Script de Identificacion de Vacios de Investigacion
Proyecto: Estado del Arte - Mercado del Huevo en Colombia
Objetivo: Identificar vacios en la literatura y contribucion original
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime


class GapIdentifier:
    """Clase para identificar vacios de investigacion"""
    
    def __init__(self, summaries_dir, comparisons_dir, synthesis_dir):
        self.summaries_dir = Path(summaries_dir)
        self.comparisons_dir = Path(comparisons_dir)
        self.synthesis_dir = Path(synthesis_dir)
        
        # Contexto del proyecto colombiano
        self.colombia_context = {
            'country': 'Colombia',
            'sector': 'Huevo',
            'ihh': 1700,
            'cr4': 69.0,
            'lerner': 18.8,
            'elasticity': -0.50,
            'market_leader': 'Incubadora Santander (34.2% cuota)',
            'sample_size': 15,
            'informal_sector': 48.5,
            'data_source': 'Supersociedades',
            'research_question': 'Como se comporta el mercado del huevo en Colombia? A que tipo de modelo teorico se asemeja mas?'
        }
    
    def load_data(self):
        """Carga datos de resumenes y analisis"""
        # Cargar consolidado de resumenes
        consolidated_file = self.summaries_dir / "consolidated_summaries.json"
        summaries = {}
        if consolidated_file.exists():
            with open(consolidated_file, 'r', encoding='utf-8') as f:
                summaries = json.load(f)
        
        # Cargar analisis comparativo
        comparative_file = self.comparisons_dir / "comparative_analysis.json"
        comparative = {}
        if comparative_file.exists():
            with open(comparative_file, 'r', encoding='utf-8') as f:
                comparative = json.load(f)
        
        # Cargar sintesis teorica
        synthesis_file = self.synthesis_dir / "theoretical_synthesis.json"
        synthesis = {}
        if synthesis_file.exists():
            with open(synthesis_file, 'r', encoding='utf-8') as f:
                synthesis = json.load(f)
        
        return summaries, comparative, synthesis
    
    def identify_geographic_gaps(self, summaries):
        """Identifica vacios geograficos en la literatura"""
        countries_covered = {}
        
        for summary in summaries.get('summaries', []):
            countries = summary.get('key_data', {}).get('countries', [])
            for country in countries:
                countries_covered[country] = countries_covered.get(country, 0) + 1
        
        # Identificar regiones sobre-representadas
        over_represented = []
        under_represented = []
        
        # Países con más de 3 menciones
        for country, count in countries_covered.items():
            if count > 3:
                over_represented.append(f"{country} ({count} estudios)")
        
        # Regiones faltantes
        missing_regions = [
            'Colombia (específicamente mercado de huevo)',
            'América Latina (excepto Brasil/México)',
            'Sudamérica',
            'Centroamérica',
            'Caribe',
            'África Subsahariana (excepto Nigeria/Etiopía)',
            'Sudeste Asiático (excepto Filipinas)'
        ]
        
        for region in missing_regions:
            if not any(region.lower() in c.lower() for c in countries_covered.keys()):
                under_represented.append(region)
        
        return {
            'countries_covered': countries_covered,
            'over_represented': over_represented,
            'under_represented': under_represented
        }
    
    def identify_methodological_gaps(self, summaries):
        """Identifica vacios metodologicos"""
        methods_used = {}
        
        for summary in summaries.get('summaries', []):
            # Detectar metodos basado en clasificacion
            categories = summary.get('classification', {}).get('categories', [])
            for category in categories:
                methods_used[category] = methods_used.get(category, 0) + 1
        
        # Metodos faltantes o poco utilizados
        methodological_gaps = []
        
        if 'Modelo teórico oligopolio' not in methods_used or methods_used.get('Modelo teórico oligopolio', 0) < 3:
            methodological_gaps.append('Estimación estructural de modelos de oligopolio')
        
        if 'Medición poder mercado' not in methods_used or methods_used.get('Medición poder mercado', 0) < 5:
            methodological_gaps.append('Estimación de índices de Lerner con datos de panel')
        
        if 'Barreras entrada' not in methods_used or methods_used.get('Barreras entrada', 0) < 5:
            methodological_gaps.append('Análisis cuantitativo de barreras de entrada')
        
        methodological_gaps.extend([
            'Análisis de conducta estratégica (pricing, publicidad)',
            'Estimación de elasticidades con datos de producto',
            'Análisis de integración vertical',
            'Evaluación de impacto de regulación sanitaria'
        ])
        
        return {
            'methods_used': methods_used,
            'gaps': methodological_gaps
        }
    
    def identify_topic_gaps(self, summaries):
        """Identifica vacios tematicos"""
        topics_covered = {}
        
        for summary in summaries.get('summaries', []):
            key_data = summary.get('key_data', {})
            
            # Detectar temas
            if key_data.get('hhi_values'):
                topics_covered['Concentración (IHH)'] = topics_covered.get('Concentración (IHH)', 0) + 1
            if key_data.get('lerner_values'):
                topics_covered['Poder de mercado (Lerner)'] = topics_covered.get('Poder de mercado (Lerner)', 0) + 1
            if key_data.get('cr_values'):
                topics_covered['Concentración (CR)'] = topics_covered.get('Concentración (CR)', 0) + 1
        
        # Temas no cubiertos o poco cubiertos
        topic_gaps = [
            'Mercado del huevo en Colombia (específicamente)',
            'Competencia entre canales de comercialización',
            'Efecto del sector informal en la dinámica de mercado',
            'Diferenciación por marca vs. diferenciación por canal',
            'Costos de transacción en la cadena avícola',
            'Regulación sanitaria como barrera de entrada',
            'Acceso a financiamiento y su efecto en competencia',
            'Comportamiento estratégico de empresas avícolas colombianas'
        ]
        
        return {
            'topics_covered': topics_covered,
            'gaps': topic_gaps
        }
    
    def assess_project_contribution(self, geographic_gaps, methodological_gaps, topic_gaps):
        """Evalua la contribucion del proyecto actual"""
        contribution = {
            'fills_geographic_gap': False,
            'fills_methodological_gap': False,
            'fills_topic_gap': False,
            'original_contribution': '',
            'significance': ''
        }
        
        # Verificar si llena vacio geografico
        if any('Colombia' in gap for gap in geographic_gaps.get('under_represented', [])):
            contribution['fills_geographic_gap'] = True
        
        # Verificar si llena vacio metodologico
        if 'Estimación de índices de Lerner con datos de panel' in methodological_gaps.get('gaps', []):
            contribution['fills_methodological_gap'] = True
        
        # Verificar si llena vacio tematico
        if any('Colombia' in gap for gap in topic_gaps.get('gaps', [])):
            contribution['fills_topic_gap'] = True
        
        # Generar contribucion original
        if contribution['fills_geographic_gap']:
            contribution['original_contribution'] = (
                "Este estudio contribuye al conocimiento existente al analizar por primera vez "
                "la estructura de mercado del huevo en Colombia utilizando datos de Supersociedades. "
                "Mientras que la literatura internacional se ha enfocado en mercados de EE.UU., Europa "
                "y algunos países en desarrollo, este trabajo llena el vacío de información sobre "
                "mercados latinoamericanos, específicamente colombianos."
            )
            contribution['significance'] = (
                "La relevancia de esta contribución radica en que Colombia es un productor "
                "significativo de huevos en Latinoamérica, y comprender su estructura de mercado "
                "es fundamental para diseñar políticas de competencia efectivas y mejorar "
                "la eficiencia del sector avícola."
            )
        
        return contribution
    
    def generate_research_gaps_report(self, geographic_gaps, methodological_gaps, topic_gaps, contribution):
        """Genera reporte completo de vacios"""
        report = {
            'analysis_date': datetime.now().isoformat(),
            'geographic_gaps': geographic_gaps,
            'methodological_gaps': methodological_gaps,
            'topic_gaps': topic_gaps,
            'project_contribution': contribution,
            'future_research_lines': self.generate_future_research_lines(),
            'summary_paragraph': self.generate_summary_paragraph(geographic_gaps, methodological_gaps, topic_gaps, contribution)
        }
        
        return report
    
    def generate_future_research_lines(self):
        """Genera lineas de investigacion futura"""
        return [
            'Análisis de conducta estratégica de las principales empresas avícolas colombianas',
            'Evaluación del impacto de la regulación sanitaria y ambiental en la competencia',
            'Estudio de la integración vertical en la cadena de valor del huevo',
            'Análisis de la dinámica competitiva entre canales de comercialización',
            'Evaluación de políticas de competencia aplicables al sector avícola',
            'Comparación con otros mercados agroalimentarios colombianos (carne, lácteos)',
            'Análisis del efecto del sector informal en la eficiencia del mercado'
        ]
    
    def generate_summary_paragraph(self, geographic_gaps, methodological_gaps, topic_gaps, contribution):
        """Genera parrafo resumen de vacios"""
        paragraph = "## Vacíos de Investigación y Contribución Original\n\n"
        
        paragraph += "### Vacíos identificados en la literatura:\n\n"
        
        paragraph += "**1. Cobertura geográfica limitada:** "
        paragraph += f"La mayoría de los estudios se concentran en {', '.join(geographic_gaps.get('over_represented', ['EE.UU.', 'Europa'])[:3])}. "
        paragraph += "Faltan estudios sobre mercados de huevo en Latinoamérica, especialmente en Colombia.\n\n"
        
        paragraph += "**2. Enfoque metodológico:** "
        paragraph += "Predominan estudios descriptivos; faltan estimaciones estructurales de modelos de oligopolio "
        paragraph += "y análisis econométricos de poder de mercado.\n\n"
        
        paragraph += "**3. Temas no explorados:** "
        paragraph += "No se ha estudiado el efecto del sector informal (48.5% de producción no reportada) "
        paragraph += "ni la diferenciación por canales de comercialización en Colombia.\n\n"
        
        paragraph += "### Contribución de este trabajo:\n\n"
        paragraph += contribution.get('original_contribution', '')
        paragraph += "\n\n"
        paragraph += contribution.get('significance', '')
        
        return paragraph
    
    def run_identification(self):
        """Ejecuta la identificacion de vacios completa"""
        print("="*80)
        print("IDENTIFICACION DE VACIOS DE INVESTIGACION")
        print("="*80)
        print()
        
        # Cargar datos
        summaries, comparative, synthesis = self.load_data()
        
        # Identificar vacios
        geographic_gaps = self.identify_geographic_gaps(summaries)
        methodological_gaps = self.identify_methodological_gaps(summaries)
        topic_gaps = self.identify_topic_gaps(summaries)
        
        # Evaluar contribucion del proyecto
        contribution = self.assess_project_contribution(geographic_gaps, methodological_gaps, topic_gaps)
        
        # Generar reporte completo
        report = self.generate_research_gaps_report(geographic_gaps, methodological_gaps, topic_gaps, contribution)
        
        # Guardar reporte
        report_file = self.synthesis_dir / "research_gaps.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Reporte guardado en: {report_file}")
        print()
        
        # Mostrar resumen
        print("="*80)
        print("RESUMEN DE VACIOS IDENTIFICADOS")
        print("="*80)
        print()
        
        print("1. VACIOS GEOGRAFICOS:")
        print(f"   Paises sobre-representados: {', '.join(geographic_gaps.get('over_represented', [])[:3])}")
        print(f"   Regiones faltantes: {', '.join(geographic_gaps.get('under_represented', [])[:3])}")
        print()
        
        print("2. VACIOS METODOLOGICOS:")
        for gap in methodological_gaps.get('gaps', [])[:3]:
            print(f"   - {gap}")
        print()
        
        print("3. VACIOS TEMATICOS:")
        for gap in topic_gaps.get('gaps', [])[:3]:
            print(f"   - {gap}")
        print()
        
        print("4. CONTRIBUCION DEL PROYECTO:")
        print(f"   Llena vacio geografico: {contribution['fills_geographic_gap']}")
        print(f"   Llena vacio metodologico: {contribution['fills_methodological_gap']}")
        print(f"   Llena vacio tematico: {contribution['fills_topic_gap']}")
        print()
        
        print("5. LINEAS DE INVESTIGACION FUTURA:")
        for line in report.get('future_research_lines', [])[:3]:
            print(f"   - {line}")
        
        print()
        print("="*80)
        print("IDENTIFICACION COMPLETADA")
        print("="*80)
        
        return report


def main():
    """Funcion principal"""
    base_dir = r"D:\Proyecto estado del arte"
    summaries_dir = os.path.join(base_dir, "summaries")
    comparisons_dir = os.path.join(base_dir, "comparisons")
    synthesis_dir = os.path.join(base_dir, "synthesis")
    
    # Crear identificador y ejecutar
    identifier = GapIdentifier(summaries_dir, comparisons_dir, synthesis_dir)
    identifier.run_identification()


if __name__ == "__main__":
    main()
