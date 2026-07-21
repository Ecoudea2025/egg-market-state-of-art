"""
Script de Extracción Masiva de PDFs Académicos
Proyecto: Estado del Arte - Mercado del Huevo en Colombia
Objetivo: Extraer texto y tablas de 27 PDFs de forma automatizada
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

# Verificar e instalar dependencias
try:
    import pdfplumber
except ImportError:
    print("Instalando pdfplumber...")
    os.system("pip install pdfplumber")
    import pdfplumber

try:
    import pandas as pd
except ImportError:
    print("Instalando pandas...")
    os.system("pip install pandas")
    import pandas as pd


class PDFExtractor:
    """Clase para extracción masiva de PDFs académicos"""
    
    def __init__(self, input_dir, output_dir):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.extracted_dir = self.output_dir / "extracted_text"
        self.summaries_dir = self.output_dir / "summaries"
        
        # Crear directorios
        self.extracted_dir.mkdir(exist_ok=True)
        self.summaries_dir.mkdir(exist_ok=True)
        
        self.results = []
        
    def extract_text_from_pdf(self, pdf_path):
        """Extrae texto completo de un PDF"""
        text = ""
        tables = []
        page_count = 0
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extraer texto
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- PÁGINA {page_num} ---\n"
                        text += page_text + "\n"
                    
                    # Extraer tablas
                    try:
                        page_tables = page.extract_tables()
                        if page_tables:
                            for table_idx, table in enumerate(page_tables):
                                tables.append({
                                    'page': page_num,
                                    'table_index': table_idx + 1,
                                    'data': table
                                })
                    except Exception as e:
                        pass  # Algunas tablas no se pueden extraer
                        
        except Exception as e:
            return None, [], 0, str(e)
        
        return text, tables, page_count, None
    
    def extract_metadata(self, pdf_path, text, page_count):
        """Extrae metadatos básicos del texto"""
        metadata = {
            'filename': pdf_path.name,
            'filepath': str(pdf_path),
            'text_length': len(text),
            'word_count': len(text.split()),
            'page_count': page_count,
            'extraction_date': datetime.now().isoformat(),
            'sections_found': [],
            'has.abstract': False,
            'has.references': False,
            'language': 'unknown'
        }
        
        text_lower = text.lower()
        
        # Detectar secciones comunes
        sections = ['abstract', 'introduction', 'methodology', 'methods', 
                   'results', 'conclusion', 'conclusions', 'discussion', 
                   'references', 'bibliography', 'resumen', 'introducción',
                   'metodología', 'resultados', 'conclusiones']
        
        for section in sections:
            if section in text_lower:
                metadata['sections_found'].append(section)
        
        metadata['has.abstract'] = 'abstract' in text_lower or 'resumen' in text_lower
        metadata['has.references'] = 'references' in text_lower or 'bibliography' in text_lower
        
        # Detectar idioma básico
        if any(word in text_lower for word in ['the', 'and', 'is', 'are', 'was']):
            metadata['language'] = 'english'
        elif any(word in text_lower for word in ['el', 'la', 'los', 'las', 'es', 'son']):
            metadata['language'] = 'spanish'
        
        return metadata
    
    def extract_key_data(self, text):
        """Extrae datos clave relevantes para el estado del arte"""
        data = {
            'hhi_values': [],
            'cr_values': [],
            'lerner_values': [],
            'elasticity_values': [],
            'market_shares': [],
            'concentration_measures': [],
            'countries': [],
            'sectors': []
        }
        
        text_upper = text.upper()
        
        # Buscar HHI/IHH
        hhi_patterns = [
            r'(?:IHH|HHI|HERFINDAHL)[:\s]*(\d+[\.,]?\d*)',
            r'(?:IHH|HHI|HERFINDAHL)[:\s]*(\d{1,3}(?:\.\d{3})*(?:,\d+)?)',
            r'HERFINDAHL[- ]HIRSHMAN[:\s]*(\d+[\.,]?\d*)'
        ]
        for pattern in hhi_patterns:
            matches = re.findall(pattern, text_upper)
            for match in matches:
                try:
                    value = float(match.replace('.', '').replace(',', '.'))
                    if 0 < value < 10000:  # Rango válido para HHI
                        data['hhi_values'].append(value)
                except:
                    pass
        
        # Buscar CR4, CR5, CR8
        cr_patterns = [
            r'(?:CR4|CR5|CR8|CONCENTRATION RATIO)[:\s]*(\d+[\.,]?\d*)\s*%',
            r'(?:CR4|CR5|CR8)[:\s]*(\d+[\.,]?\d*)'
        ]
        for pattern in cr_patterns:
            matches = re.findall(pattern, text_upper)
            for match in matches:
                try:
                    value = float(match.replace(',', '.'))
                    if 0 < value <= 100:
                        data['cr_values'].append(value)
                except:
                    pass
        
        # Buscar Lerner
        lerner_patterns = [
            r'(?:LERNER|ÍNDICE DE LERNER|LERNER INDEX)[:\s]*(\d+[\.,]?\d*)\s*%',
            r'(?:LERNER|ÍNDICE DE LERNER|LERNER INDEX)[:\s]*(0\.\d+)'
        ]
        for pattern in lerner_patterns:
            matches = re.findall(pattern, text_upper)
            for match in matches:
                try:
                    value = float(match.replace(',', '.'))
                    if 0 < value < 1:
                        data['lerner_values'].append(value)
                    elif 1 <= value <= 100:
                        data['lerner_values'].append(value / 100)
                except:
                    pass
        
        # Buscar elasticidades
        elasticity_patterns = [
            r'(?:ELASTICITY|ELASTICIDAD)[:\s]*[-]?(\d+[\.,]?\d*)',
            r'(?:ε|E)[:\s]*[-]?(\d+[\.,]?\d*)'
        ]
        for pattern in elasticity_patterns:
            matches = re.findall(pattern, text_upper)
            for match in matches:
                try:
                    value = float(match.replace(',', '.'))
                    if -10 < value < 0:  # Elasticidades negativas para demanda
                        data['elasticity_values'].append(value)
                except:
                    pass
        
        # Buscar países
        countries_list = [
            'colombia', 'estados unidos', 'united states', 'usa', 'us',
            'nigeria', 'etiopía', 'ethiopia', 'india', 'brasil', 'brazil',
            'méxico', 'mexico', 'argentina', 'chile', 'perú', 'peru',
            'ecuador', 'venezuela', 'españa', 'spain', 'unión europea',
            'european union', 'china', 'japón', 'japan'
        ]
        
        text_lower = text.lower()
        for country in countries_list:
            if country in text_lower:
                data['countries'].append(country)
        
        # Buscar sectores
        sectors_list = [
            'huevo', 'egg', 'huevos', 'eggs', 'avicultura', 'poultry',
            'pollo', 'chicken', 'carne', 'meat', 'lácteos', 'dairy',
            'maíz', 'corn', 'soya', 'soy', 'granos', 'grains',
            'agroalimentario', 'agri-food', 'agrícola', 'agricultural'
        ]
        
        for sector in sectors_list:
            if sector in text_lower:
                data['sectors'].append(sector)
        
        return data
    
    def process_single_pdf(self, pdf_path):
        """Procesa un solo PDF y retorna toda la informacion"""
        print(f"  Procesando: {pdf_path.name.encode('ascii', 'ignore').decode('ascii')}")
        
        # Extraer texto y tablas
        text, tables, page_count, error = self.extract_text_from_pdf(pdf_path)
        
        if error:
            return {
                'status': 'error',
                'filename': pdf_path.name,
                'error': error
            }
        
        # Extraer metadatos
        metadata = self.extract_metadata(pdf_path, text, page_count)
        metadata['tables_count'] = len(tables)
        
        # Extraer datos clave
        key_data = self.extract_key_data(text)
        
        # Guardar texto extraído
        output_file = self.extracted_dir / f"{pdf_path.stem}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"ARCHIVO: {pdf_path.name}\n")
            f.write(f"FECHA EXTRACCIÓN: {datetime.now().isoformat()}\n")
            f.write(f"LONGITUD: {len(text)} caracteres\n")
            f.write(f"PÁGINAS: {page_count}\n")
            f.write(f"TABLAS: {len(tables)} encontradas\n")
            f.write("="*80 + "\n\n")
            f.write(text)
            
            # Guardar tablas si existen
            if tables:
                f.write("\n\n" + "="*80 + "\n")
                f.write("TABLAS ENCONTRADAS:\n")
                f.write("="*80 + "\n\n")
                for table_info in tables:
                    f.write(f"--- TABLA {table_info['table_index']} (Página {table_info['page']}) ---\n")
                    for row in table_info['data']:
                        if row:
                            f.write(" | ".join([str(cell) if cell else "" for cell in row]) + "\n")
                    f.write("\n")
        
        # Guardar metadata JSON
        metadata_file = self.extracted_dir / f"{pdf_path.stem}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # Guardar datos clave JSON
        key_data_file = self.extracted_dir / f"{pdf_path.stem}_keydata.json"
        with open(key_data_file, 'w', encoding='utf-8') as f:
            json.dump(key_data, f, indent=2, ensure_ascii=False)
        
        return {
            'status': 'success',
            'filename': pdf_path.name,
            'text_file': str(output_file),
            'metadata_file': str(metadata_file),
            'keydata_file': str(key_data_file),
            'metadata': metadata,
            'key_data': key_data
        }
    
    def process_all_pdfs(self):
        """Procesa todos los PDFs del directorio"""
        print("="*80)
        print("EXTRACCIÓN MASIVA DE PDFS ACADÉMICOS")
        print("="*80)
        print(f"Directorio de entrada: {self.input_dir}")
        print(f"Directorio de salida: {self.output_dir}")
        print()
        
        # Obtener todos los PDFs
        pdf_files = list(self.input_dir.glob("*.pdf"))
        print(f"Encontrados {len(pdf_files)} archivos PDF")
        print()
        
        # Procesar cada PDF
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] ", end="")
            result = self.process_single_pdf(pdf_path)
            self.results.append(result)
            
            if result['status'] == 'success':
                print(f"    [OK] Extraido: {result['metadata']['word_count']} palabras, "
                      f"{result['metadata']['tables_count']} tablas")
            else:
                print(f"    [ERROR] Error: {result['error']}")
        
        print()
        print("="*80)
        print("RESUMEN DE EXTRACCIÓN")
        print("="*80)
        
        # Estadísticas
        successful = [r for r in self.results if r['status'] == 'success']
        failed = [r for r in self.results if r['status'] == 'error']
        
        print(f"Exitosos: {len(successful)}/{len(self.results)}")
        print(f"Fallidos: {len(failed)}/{len(self.results)}")
        
        if successful:
            total_words = sum(r['metadata']['word_count'] for r in successful)
            total_tables = sum(r['metadata']['tables_count'] for r in successful)
            print(f"Total palabras: {total_words:,}")
            print(f"Total tablas: {total_tables}")
        
        # Guardar resumen de procesamiento
        summary_file = self.output_dir / "extraction_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'extraction_date': datetime.now().isoformat(),
                'total_files': len(self.results),
                'successful': len(successful),
                'failed': len(failed),
                'results': self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\nResumen guardado en: {summary_file}")
        
        # Generar CSV resumen
        if successful:
            summary_data = []
            for r in successful:
                summary_data.append({
                    'filename': r['filename'],
                    'words': r['metadata']['word_count'],
                    'pages': r['metadata']['page_count'],
                    'tables': r['metadata']['tables_count'],
                    'language': r['metadata']['language'],
                    'hhi_found': len(r['key_data']['hhi_values']),
                    'cr_found': len(r['key_data']['cr_values']),
                    'lerner_found': len(r['key_data']['lerner_values'])
                })
            
            df = pd.DataFrame(summary_data)
            csv_file = self.output_dir / "extraction_summary.csv"
            df.to_csv(csv_file, index=False)
            print(f"CSV guardado en: {csv_file}")
        
        return self.results


def main():
    """Función principal"""
    # Configurar rutas
    input_dir = r"D:\Proyecto estado del arte"
    output_dir = r"D:\Proyecto estado del arte"
    
    # Verificar directorio de entrada
    if not os.path.exists(input_dir):
        print(f"Error: Directorio no encontrado: {input_dir}")
        sys.exit(1)
    
    # Crear extractor y procesar
    extractor = PDFExtractor(input_dir, output_dir)
    results = extractor.process_all_pdfs()
    
    print("\n" + "="*80)
    print("EXTRACCIÓN COMPLETADA")
    print("="*80)
    print("Archivos generados:")
    print(f"  - Textos extraídos: {output_dir}/extracted_text/*.txt")
    print(f"  - Metadatos: {output_dir}/extracted_text/*_metadata.json")
    print(f"  - Datos clave: {output_dir}/extracted_text/*_keydata.json")
    print(f"  - Resumen: {output_dir}/extraction_summary.json")
    print(f"  - CSV: {output_dir}/extraction_summary.csv")


if __name__ == "__main__":
    main()
