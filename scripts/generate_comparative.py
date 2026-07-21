"""
Script de Análisis Comparativo
Proyecto: Estado del Arte - Mercado del Huevo en Colombia
Objetivo: Comparar hallazgos empíricos entre múltiples estudios
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    print("Instalando pandas...")
    os.system("pip install pandas")
    import pandas as pd


class ComparativeAnalyzer:
    """Clase para comparar hallazgos empíricos entre estudios"""
    
    def __init__(self, summaries_dir, comparisons_dir):
        self.summaries_dir = Path(summaries_dir)
        self.comparisons_dir = Path(comparisons_dir)
        self.comparisons_dir.mkdir(exist_ok=True)
        
        # Datos del proyecto colombiano para comparación
        self.colombia_data = {
            'country': 'Colombia',
            'sector': 'Huevo',
            'hhi': 1700,
            'cr4': 69.0,
            'lerner': 18.8,
            'elasticity': -0.50,
            'market_leader': 'Incubadora Santander (34.2%)',
            'sample_size': 15,
            'notes': 'Concentración moderada, fringe informal 48.5%'
        }
    
    def load_summaries(self):
        """Carga todos los resúmenes generados"""
        summaries = []
        
        summary_files = list(self.summaries_dir.glob("summary_*.json"))
        print(f"Cargando {len(summary_files)} resúmenes...")
        
        for summary_file in summary_files:
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary = json.load(f)
                    summaries.append(summary)
            except Exception as e:
                print(f"Error cargando {summary_file.name}: {str(e)}")
        
        return summaries
    
    def extract_empirical_data(self, summaries):
        """Extrae datos empíricos de cada resumen"""
        empirical_data = []
        
        for summary in summaries:
            data = {
                'filename': summary['metadata']['filename'],
                'authors': summary['metadata']['authors'],
                'year': summary['metadata']['year'],
                'title': summary['metadata']['title'],
                'categories': summary['classification']['categories'],
                'countries': summary.get('key_data', {}).get('countries', []),
                'sectors': summary.get('key_data', {}).get('sectors', []),
                'hhi_values': summary.get('key_data', {}).get('hhi_values', []),
                'cr_values': summary.get('key_data', {}).get('cr_values', []),
                'lerner_values': summary.get('key_data', {}).get('lerner_values', []),
                'elasticity_values': summary.get('key_data', {}).get('elasticity_values', []),
                'relevance_colombia': summary.get('relevance_colombia', {})
            }
            empirical_data.append(data)
        
        return empirical_data
    
    def create_comparative_table(self, empirical_data):
        """Crea tabla comparativa de hallazgos empíricos"""
        table_data = []
        
        for data in empirical_data:
            row = {
                'Autores': data['authors'],
                'Año': data['year'],
                'País': ', '.join(data['countries'][:3]) if data['countries'] else 'No especificado',
                'Sector': ', '.join(data['sectors'][:3]) if data['sectors'] else 'No especificado',
                'IHH': data['hhi_values'][0] if data['hhi_values'] else None,
                'CR': data['cr_values'][0] if data['cr_values'] else None,
                'Lerner': data['lerner_values'][0] if data['lerner_values'] else None,
                'Elasticidad': data['elasticity_values'][0] if data['elasticity_values'] else None,
                'Relevancia Colombia': data['relevance_colombia'].get('level', 'N/A')
            }
            table_data.append(row)
        
        # Agregar datos de Colombia
        table_data.append({
            'Autores': 'Proyecto actual',
            'Año': 2026,
            'País': 'Colombia',
            'Sector': 'Huevo',
            'IHH': self.colombia_data['hhi'],
            'CR': self.colombia_data['cr4'],
            'Lerner': self.colombia_data['lerner'],
            'Elasticidad': self.colombia_data['elasticity'],
            'Relevancia Colombia': 'Proyecto actual'
        })
        
        return pd.DataFrame(table_data)
    
    def analyze_patterns(self, empirical_data):
        """Analiza patrones en los datos empíricos"""
        patterns = {
            'hhi_ranges': {'bajo': 0, 'moderado': 0, 'alto': 0, 'muy_alto': 0},
            'lerner_ranges': {'bajo': 0, 'moderado': 0, 'alto': 0},
            'countries_distribution': {},
            'sectors_distribution': {},
            'models_identified': {},
            'methodological_approaches': {}
        }
        
        for data in empirical_data:
            # Analizar IHH
            for hhi in data['hhi_values']:
                if hhi < 1000:
                    patterns['hhi_ranges']['bajo'] += 1
                elif hhi < 1800:
                    patterns['hhi_ranges']['moderado'] += 1
                elif hhi < 2500:
                    patterns['hhi_ranges']['alto'] += 1
                else:
                    patterns['hhi_ranges']['muy_alto'] += 1
            
            # Analizar Lerner
            for lerner in data['lerner_values']:
                if lerner < 0.1:
                    patterns['lerner_ranges']['bajo'] += 1
                elif lerner < 0.2:
                    patterns['lerner_ranges']['moderado'] += 1
                else:
                    patterns['lerner_ranges']['alto'] += 1
            
            # Distribución de países
            for country in data['countries']:
                patterns['countries_distribution'][country] = \
                    patterns['countries_distribution'].get(country, 0) + 1
            
            # Distribución de sectores
            for sector in data['sectors']:
                patterns['sectors_distribution'][sector] = \
                    patterns['sectors_distribution'].get(sector, 0) + 1
            
            # Modelos identificados
            for category in data['categories']:
                patterns['models_identified'][category] = \
                    patterns['models_identified'].get(category, 0) + 1
        
        return patterns
    
    def compare_with_colombia(self, empirical_data):
        """Compara hallazgos con el caso colombiano"""
        comparisons = []
        
        for data in empirical_data:
            comparison = {
                'study': f"{data['authors']} ({data['year']})",
                'filename': data['filename'],
                'similarities': [],
                'differences': [],
                'methodological_comparison': {}
            }
            
            # Comparar IHH
            if data['hhi_values']:
                study_hhi = data['hhi_values'][0]
                if abs(study_hhi - self.colombia_data['hhi']) < 500:
                    comparison['similarities'].append(f"IHH similar ({study_hhi} vs {self.colombia_data['hhi']})")
                else:
                    comparison['differences'].append(f"IHH diferente ({study_hhi} vs {self.colombia_data['hhi']})")
            
            # Comparar Lerner
            if data['lerner_values']:
                study_lerner = data['lerner_values'][0]
                if abs(study_lerner - self.colombia_data['lerner']/100) < 0.05:
                    comparison['similarities'].append(f"Lerner similar ({study_lerner:.2%} vs {self.colombia_data['lerner']/100:.2%})")
                else:
                    comparison['differences'].append(f"Lerner diferente ({study_lerner:.2%} vs {self.colombia_data['lerner']/100:.2%})")
            
            # Comparar sector
            if 'huevo' in data['sectors'] or 'egg' in data['sectors']:
                comparison['similarities'].append("Mismo sector (huevo)")
            elif any(sector in data['sectors'] for sector in ['pollo', 'chicken', 'poultry', 'avicultura']):
                comparison['similarities'].append("Sector similar (avicultura)")
            
            # Comparar país
            if 'colombia' in [c.lower() for c in data['countries']]:
                comparison['similarities'].append("Mismo país (Colombia)")
            elif any(country in data['countries'] for country in ['latin america', 'latinoamérica']):
                comparison['similarities'].append("Región similar (Latinoamérica)")
            
            comparisons.append(comparison)
        
        return comparisons
    
    def identify_most_comparable(self, comparisons):
        """Identifica el estudio más comparable al caso colombiano"""
        scores = []
        
        for comparison in comparisons:
            score = len(comparison['similarities']) - len(comparison['differences'])
            scores.append({
                'study': comparison['study'],
                'filename': comparison['filename'],
                'score': score,
                'similarities': comparison['similarities'],
                'differences': comparison['differences']
            })
        
        # Ordenar por puntaje
        scores.sort(key=lambda x: x['score'], reverse=True)
        
        return scores[0] if scores else None
    
    def generate_key_insights(self, patterns, comparisons):
        """Genera insights clave del análisis"""
        insights = []
        
        # Insight sobre IHH
        if patterns['hhi_ranges']['moderado'] > 0:
            insights.append(
                f"La mayoría de los estudios reportan IHH en rango moderado "
                f"({patterns['hhi_ranges']['moderado']} estudios), similar al caso colombiano (IHH ~1,700)"
            )
        
        # Insight sobre Lerner
        if patterns['lerner_ranges']['moderado'] > 0:
            insights.append(
                f"Los niveles de Lerner moderados son comunes en la literatura "
                f"({patterns['lerner_ranges']['moderado']} estudios), consistente con Lerner ~18.8% en Colombia"
            )
        
        # Insight sobre países
        if patterns['countries_distribution']:
            top_country = max(patterns['countries_distribution'], 
                           key=patterns['countries_distribution'].get)
            insights.append(
                f"País más estudiado: {top_country} "
                f"({patterns['countries_distribution'][top_country]} estudios)"
            )
        
        # Insight sobre sectores
        if patterns['sectors_distribution']:
            top_sector = max(patterns['sectors_distribution'], 
                          key=patterns['sectors_distribution'].get)
            insights.append(
                f"Sector más estudiado: {top_sector} "
                f"({patterns['sectors_distribution'][top_sector]} menciones)"
            )
        
        return insights
    
    def run_analysis(self):
        """Ejecuta el análisis comparativo completo"""
        print("="*80)
        print("ANÁLISIS COMPARATIVO DE HALLAZGOS EMPÍRICOS")
        print("="*80)
        print()
        
        # Cargar resúmenes
        summaries = self.load_summaries()
        if not summaries:
            print("Error: No se encontraron resúmenes. Ejecute process_text.py primero.")
            return
        
        print(f"Cargados {len(summaries)} resúmenes")
        print()
        
        # Extraer datos empíricos
        empirical_data = self.extract_empirical_data(summaries)
        
        # Crear tabla comparativa
        print("Generando tabla comparativa...")
        comparative_table = self.create_comparative_table(empirical_data)
        table_file = self.comparisons_dir / "comparative_table.csv"
        comparative_table.to_csv(table_file, index=False, encoding='utf-8')
        print(f"  Tabla guardada en: {table_file}")
        
        # Guardar también como JSON
        table_json_file = self.comparisons_dir / "comparative_table.json"
        comparative_table.to_json(table_json_file, orient='records', force_ascii=False, indent=2)
        
        # Analizar patrones
        print("Analizando patrones...")
        patterns = self.analyze_patterns(empirical_data)
        
        # Comparar con Colombia
        print("Comparando con caso colombiano...")
        comparisons = self.compare_with_colombia(empirical_data)
        
        # Identificar estudio más comparable
        most_comparable = self.identify_most_comparable(comparisons)
        
        # Generar insights clave
        insights = self.generate_key_insights(patterns, comparisons)
        
        # Guardar resultados completos
        results = {
            'analysis_date': datetime.now().isoformat(),
            'total_studies': len(empirical_data),
            'colombia_data': self.colombia_data,
            'comparative_table': comparative_table.to_dict(orient='records'),
            'patterns': patterns,
            'comparisons': comparisons,
            'most_comparable_study': most_comparable,
            'key_insights': insights
        }
        
        results_file = self.comparisons_dir / "comparative_analysis.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print()
        print("="*80)
        print("RESUMEN DEL ANÁLISIS")
        print("="*80)
        print(f"Total estudios analizados: {len(empirical_data)}")
        print()
        
        print("Distribución de IHH:")
        for level, count in patterns['hhi_ranges'].items():
            if count > 0:
                print(f"  - {level}: {count}")
        print()
        
        print("Distribución de Lerner:")
        for level, count in patterns['lerner_ranges'].items():
            if count > 0:
                print(f"  - {level}: {count}")
        print()
        
        if most_comparable:
            print(f"Estudio más comparable: {most_comparable['study']}")
            print(f"  Puntaje: {most_comparable['score']}")
            print(f"  Similitudes: {', '.join(most_comparable['similarities'])}")
            print()
        
        print("Insights clave:")
        for i, insight in enumerate(insights, 1):
            print(f"  {i}. {insight}")
        
        print()
        print("="*80)
        print("ANÁLISIS COMPLETADO")
        print("="*80)
        print("Archivos generados:")
        print(f"  - Tabla comparativa: {table_file}")
        print(f"  - Análisis completo: {results_file}")
        
        return results


def main():
    """Función principal"""
    base_dir = r"D:\Proyecto estado del arte"
    summaries_dir = os.path.join(base_dir, "summaries")
    comparisons_dir = os.path.join(base_dir, "comparisons")
    
    # Verificar directorio
    if not os.path.exists(summaries_dir):
        print(f"Error: Directorio no encontrado: {summaries_dir}")
        print("Primero ejecute process_text.py")
        sys.exit(1)
    
    # Crear analizador y ejecutar
    analyzer = ComparativeAnalyzer(summaries_dir, comparisons_dir)
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
