"""
Script de Procesamiento de Texto Extraído
Proyecto: Estado del Arte - Mercado del Huevo en Colombia
Objetivo: Analizar textos extraídos y generar resúmenes estructurados
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime


class TextProcessor:
    """Clase para procesar texto extraído de PDFs y generar resúmenes estructurados"""
    
    def __init__(self, extracted_dir, summaries_dir):
        self.extracted_dir = Path(extracted_dir)
        self.summaries_dir = Path(summaries_dir)
        self.summaries_dir.mkdir(exist_ok=True)
        
        # Patrones de búsqueda para datos académicos
        self.patterns = {
            'author_year': [
                r'([A-Z][a-z]+(?:\s+(?:et\s+al\.?|and\s+[A-Z][a-z]+))*)\s*\((\d{4})\)',
                r'([A-Z][a-z]+(?:,\s*[A-Z][a-z]+)+)\s*\((\d{4})\)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*,\s*(\d{4})'
            ],
            'title_patterns': [
                r'(?:Title|Título)[:\s]*([^\n]+)',
                r'^([A-Z][^.\n]{10,})\.?\s*$'
            ],
            'abstract_patterns': [
                r'(?:Abstract|Resumen)[:\s]*\n?(.*?)(?:\n\s*\n|\n(?:Keywords|Palabras))',
                r'(?:Abstract|Resumen)[:\s]*(.*?)(?:\.?\s*Keywords|\.?\s*Palabras)'
            ],
            'methodology_patterns': [
                r'(?:Methodology|Método|Methods|Metodología)[:\s]*\n?(.*?)(?:\n\s*\n|\n(?:Results|Resultados))',
                r'(?:using|utilizando|employing|empleando)\s+([\w\s]+?)(?:\s+(?:to|para|approach|método))'
            ],
            'results_patterns': [
                r'(?:Results|Resultados|Findings|Hallazgos)[:\s]*\n?(.*?)(?:\n\s*\n|\n(?:Conclusion|Conclusión|Discussion))',
                r'(?:IHH|HHI|Herfindahl)[:\s]*(\d+[\.,]?\d*)',
                r'(?:CR4|CR5|CR8)[:\s]*(\d+[\.,]?\d*)\s*%',
                r'(?:Lerner|Índice de Lerner)[:\s]*(\d+[\.,]?\d*)\s*%'
            ],
            'conclusion_patterns': [
                r'(?:Conclusion|Conclusión|Conclusions|Conclusiones)[:\s]*\n?(.*?)(?:\n\s*\n|\n(?:References|Referencias))',
                r'(?:Thus|Therefore|En conclusión|Por lo tanto)[,\s]*(.*?)(?:\.|$)'
            ]
        }
        
        # Palabras clave relevantes para el estado del arte
        self.keywords = {
            'market_structure': [
                'market structure', 'estructura de mercado', 'concentration', 'concentración',
                'oligopoly', 'oligopolio', 'monopoly', 'monopolio', 'competition', 'competencia'
            ],
            'market_power': [
                'market power', 'poder de mercado', 'Lerner', 'markup', 'margen',
                'HHI', 'Herfindahl', 'IHH', 'concentration ratio'
            ],
            'oligopoly_models': [
                'Cournot', 'Bertrand', 'Stackelberg', 'oligopoly model',
                'modelo de oligopolio', 'price competition', 'quantity competition',
                'differentiated products', 'productos diferenciados'
            ],
            'egg_market': [
                'egg', 'huevo', 'huevos', 'poultry', 'avicultura', 'aviario',
                'broiler', 'pollo', 'egg production', 'producción de huevo'
            ],
            'agricultural': [
                'agriculture', 'agricultura', 'agricultural', 'agrícola',
                'food', 'alimento', 'agri-food', 'agroalimentario'
            ],
            'barriers': [
                'barriers to entry', 'barreras de entrada', 'sunk costs', 'costos hundidos',
                'economies of scale', 'economías de escala', 'entry barriers'
            ]
        }
    
    def read_extracted_text(self, txt_file):
        """Lee un archivo de texto extraído"""
        with open(txt_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_section(self, text, section_type):
        """Extrae una sección específica del texto"""
        patterns = self.patterns.get(section_type, [])
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            if matches:
                if isinstance(matches[0], tuple):
                    return matches[0][0] if matches[0][0] else matches[0][1]
                return matches[0]
        
        return None
    
    def extract_authors_and_year(self, text):
        """Extrae autores y año de publicación"""
        for pattern in self.patterns['author_year']:
            matches = re.findall(pattern, text[:2000])  # Buscar en primeras líneas
            if matches:
                return {
                    'authors': matches[0][0],
                    'year': int(matches[0][1])
                }
        
        return {'authors': 'Unknown', 'year': None}
    
    def extract_title(self, text):
        """Extrae el título del documento"""
        lines = text.split('\n')
        
        # Buscar en primeras 20 líneas
        for i, line in enumerate(lines[:20]):
            line = line.strip()
            # El título suele estar al inicio y ser una línea sustancial
            if len(line) > 20 and not line.startswith('---'):
                # Verificar que no sea metadata
                if not any(word in line.lower() for word in ['page', 'página', 'extracted', 'archivo']):
                    return line
        
        return 'Unknown Title'
    
    def classify_article(self, text, key_data):
        """Clasifica el artículo en categorías"""
        categories = []
        text_lower = text.lower()
        
        # Verificar categorías
        if any(kw in text_lower for kw in self.keywords['egg_market']):
            categories.append('Mercado huevos internacional')
        
        if any(kw in text_lower for kw in self.keywords['oligopoly_models']):
            categories.append('Modelo teórico oligopolio')
        
        if any(kw in text_lower for kw in self.keywords['market_power']):
            categories.append('Medición poder mercado')
        
        if any(kw in text_lower for kw in self.keywords['barriers']):
            categories.append('Barreras entrada')
        
        if any(kw in text_lower for kw in self.keywords['agricultural']):
            if 'Estructura mercado agroalimentario' not in categories:
                categories.append('Estructura mercado agroalimentario')
        
        if not categories:
            categories.append('Otro')
        
        return categories
    
    def extract_key_quotes(self, text, max_quotes=5):
        """Extrae citas relevantes del texto"""
        quotes = []
        
        # Buscar oraciones que contengan palabras clave
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 50 and len(sentence) < 300:
                # Verificar si contiene información relevante
                if any(kw in sentence.lower() for kw in [
                    'i hh', 'hhi', 'herfindahl', 'lerner', 'concentration',
                    'concentración', 'oligopoly', 'oligopolio', 'market share',
                    'cuota de mercado', 'elasticity', 'elasticidad'
                ]):
                    quotes.append(sentence.strip())
        
        return quotes[:max_quotes]
    
    def extract_tables_data(self, text):
        """Extrae y estructura datos de tablas"""
        tables = []
        
        # Buscar sección de tablas
        tables_match = re.search(r'TABLAS ENCONTRADAS:(.*?)(?:$)', text, re.DOTALL)
        if tables_match:
            tables_text = tables_match.group(1)
            
            # Separar tablas individuales
            table_splits = re.split(r'--- TABLA \d+', tables_text)
            
            for i, table_text in enumerate(table_splits):
                if table_text.strip():
                    rows = []
                    for line in table_text.strip().split('\n'):
                        if '|' in line:
                            row = [cell.strip() for cell in line.split('|') if cell.strip()]
                            if row:
                                rows.append(row)
                    
                    if rows:
                        tables.append({
                            'table_number': i + 1,
                            'data': rows
                        })
        
        return tables
    
    def generate_summary(self, txt_file):
        """Genera un resumen estructurado para un archivo"""
        # Leer texto
        text = self.read_extracted_text(txt_file)
        
        # Extraer metadatos básicos
        author_info = self.extract_authors_and_year(text)
        title = self.extract_title(text)
        
        # Extraer secciones
        abstract = self.extract_section(text, 'abstract_patterns')
        methodology = self.extract_section(text, 'methodology_patterns')
        results = self.extract_section(text, 'results_patterns')
        conclusion = self.extract_section(text, 'conclusion_patterns')
        
        # Cargar datos clave si existen
        keydata_file = txt_file.parent / f"{txt_file.stem}_keydata.json"
        key_data = {}
        if keydata_file.exists():
            with open(keydata_file, 'r', encoding='utf-8') as f:
                key_data = json.load(f)
        
        # Clasificar artículo
        categories = self.classify_article(text, key_data)
        
        # Extraer citas relevantes
        key_quotes = self.extract_key_quotes(text)
        
        # Extraer tablas
        tables = self.extract_tables_data(text)
        
        # Construir resumen estructurado
        summary = {
            'metadata': {
                'filename': txt_file.name.replace('.txt', '.pdf'),
                'authors': author_info['authors'],
                'year': author_info['year'],
                'title': title,
                'processing_date': datetime.now().isoformat()
            },
            'content': {
                'abstract': abstract,
                'methodology': methodology,
                'results': results,
                'conclusion': conclusion
            },
            'key_data': key_data,
            'classification': {
                'categories': categories,
                'primary_category': categories[0] if categories else 'Otro'
            },
            'key_quotes': key_quotes,
            'tables': tables,
            'relevance_colombia': self.assess_relevance_to_colombia(text, key_data)
        }
        
        return summary
    
    def assess_relevance_to_colombia(self, text, key_data):
        """Evalúa la relevancia del artículo para el caso colombiano"""
        relevance_score = 0
        relevance_reasons = []
        
        text_lower = text.lower()
        
        # Mencionar Colombia directamente
        if 'colombia' in text_lower:
            relevance_score += 3
            relevance_reasons.append('Menciona Colombia directamente')
        
        # Mencionar Latinoamérica
        if any(term in text_lower for term in ['latin america', 'latinoamérica', 'américa latina']):
            relevance_score += 2
            relevance_reasons.append('Menciona Latinoamérica')
        
        # Mercado de huevo
        if any(term in text_lower for term in ['egg', 'huevo', 'huevos']):
            relevance_score += 2
            relevance_reasons.append('Estudia mercado de huevo')
        
        # Medidas de concentración
        if key_data.get('hhi_values') or key_data.get('cr_values'):
            relevance_score += 1
            relevance_reasons.append('Reporta medidas de concentración')
        
        # Índice de Lerner
        if key_data.get('lerner_values'):
            relevance_score += 1
            relevance_reasons.append('Reporta índice de Lerner')
        
        # Países en desarrollo
        if any(term in text_lower for term in ['developing countries', 'países en desarrollo', 'emerging']):
            relevance_score += 1
            relevance_reasons.append('Estudia países en desarrollo')
        
        # Asignar nivel de relevancia
        if relevance_score >= 5:
            level = 'Alta'
        elif relevance_score >= 3:
            level = 'Media'
        else:
            level = 'Baja'
        
        return {
            'score': relevance_score,
            'level': level,
            'reasons': relevance_reasons
        }
    
    def process_all_extracted(self):
        """Procesa todos los archivos de texto extraído"""
        print("="*80)
        print("PROCESAMIENTO DE TEXTO EXTRAÍDO")
        print("="*80)
        print(f"Directorio de entrada: {self.extracted_dir}")
        print(f"Directorio de salida: {self.summaries_dir}")
        print()
        
        # Obtener todos los archivos .txt (excluyendo metadata y keydata)
        txt_files = [f for f in self.extracted_dir.glob("*.txt") 
                    if '_metadata' not in f.name and '_keydata' not in f.name]
        
        print(f"Encontrados {len(txt_files)} archivos de texto para procesar")
        print()
        
        summaries = []
        
        for i, txt_file in enumerate(txt_files, 1):
            print(f"[{i}/{len(txt_files)}] Procesando: {txt_file.name.encode('ascii', 'ignore').decode('ascii')}")
            
            try:
                summary = self.generate_summary(txt_file)
                
                # Guardar resumen
                summary_file = self.summaries_dir / f"summary_{txt_file.stem}.json"
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                
                summaries.append(summary)
                
                print(f"    [OK] Categorias: {', '.join(summary['classification']['categories'])}")
                print(f"    [OK] Relevancia Colombia: {summary['relevance_colombia']['level']}")
                
            except Exception as e:
                print(f"    [ERROR] Error: {str(e)}")
        
        print()
        print("="*80)
        print("RESUMEN DE PROCESAMIENTO")
        print("="*80)
        
        # Estadísticas
        categories_count = {}
        relevance_count = {'Alta': 0, 'Media': 0, 'Baja': 0}
        
        for summary in summaries:
            for cat in summary['classification']['categories']:
                categories_count[cat] = categories_count.get(cat, 0) + 1
            relevance_count[summary['relevance_colombia']['level']] += 1
        
        print(f"Total artículos procesados: {len(summaries)}")
        print()
        print("Distribución por categorías:")
        for cat, count in sorted(categories_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {cat}: {count}")
        print()
        print("Relevancia para Colombia:")
        for level, count in relevance_count.items():
            print(f"  - {level}: {count}")
        
        # Guardar consolidado
        consolidated_file = self.summaries_dir / "consolidated_summaries.json"
        with open(consolidated_file, 'w', encoding='utf-8') as f:
            json.dump({
                'processing_date': datetime.now().isoformat(),
                'total_articles': len(summaries),
                'categories_distribution': categories_count,
                'relevance_distribution': relevance_count,
                'summaries': summaries
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nConsolidado guardado en: {consolidated_file}")
        
        return summaries


def main():
    """Función principal"""
    base_dir = r"D:\Proyecto estado del arte"
    extracted_dir = os.path.join(base_dir, "extracted_text")
    summaries_dir = os.path.join(base_dir, "summaries")
    
    # Verificar directorio
    if not os.path.exists(extracted_dir):
        print(f"Error: Directorio no encontrado: {extracted_dir}")
        print("Primero ejecute extract_pdfs.py")
        sys.exit(1)
    
    # Crear procesador y ejecutar
    processor = TextProcessor(extracted_dir, summaries_dir)
    summaries = processor.process_all_extracted()
    
    print("\n" + "="*80)
    print("PROCESAMIENTO COMPLETADO")
    print("="*80)
    print("Archivos generados:")
    print(f"  - Resúmenes: {summaries_dir}/summary_*.json")
    print(f"  - Consolidado: {summaries_dir}/consolidated_summaries.json")


if __name__ == "__main__":
    main()
