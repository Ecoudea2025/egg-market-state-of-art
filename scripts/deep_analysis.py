"""
Análisis Profundo de Documentos Académicos
Extrae citas textuales, datos numéricos y genera síntesis detalladas
enfocadas en lo que dicen los autores de los documentos
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime


class DeepDocumentAnalyzer:
    """Analizador profundo de documentos académicos"""
    
    def __init__(self, extracted_dir, output_dir):
        self.extracted_dir = Path(extracted_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_textual_citations(self, text, doc_name):
        """Extrae citas textuales relevantes del documento"""
        citations = []
        
        # Patrones para buscar citas sobre temas específicos
        citation_patterns = [
            # Concentración de mercado
            r'(?:concentration|concentración|HHI|Herfindahl|IHH)[^.]*\.',
            # Poder de mercado
            r'(?:market power|poder de mercado|Lerner|markup)[^.]*\.',
            # Oligopolio
            r'(?:oligopoly|oligopolio|oligopolistic)[^.]*\.',
            # Competencia
            r'(?:competition|competencia|competitive|competitivo)[^.]*\.',
            # Barreras de entrada
            r'(?:barriers to entry|barreras de entrada|entry barriers)[^.]*\.',
            # Economías de escala
            r'(?:economies of scale|economías de escala|scale economies)[^.]*\.',
            # Diferenciación de producto
            r'(?:product differentiation|diferenciación de producto|differentiated)[^.]*\.',
            # Datos numéricos específicos
            r'(?:IHH|HHI|CR4|CR5|Lerner)\s*[:=]?\s*\d+[\.,]?\d*[^.]*\.',
            # Mercados de huevo
            r'(?:egg|huevo|huevos|poultry|avicultura)[^.]*\.',
        ]
        
        for pattern in citation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                citation = match.group(0).strip()
                if len(citation) > 30 and len(citation) < 500:  # Filtrar citas muy cortas o largas
                    citations.append({
                        'text': citation,
                        'source': doc_name,
                        'topic': self.classify_citation_topic(citation)
                    })
        
        return citations
    
    def classify_citation_topic(self, citation):
        """Clasifica el tema de una cita"""
        citation_lower = citation.lower()
        
        if any(term in citation_lower for term in ['concentration', 'concentración', 'hhi', 'herfindahl', 'cr4', 'cr5']):
            return 'Concentración de mercado'
        elif any(term in citation_lower for term in ['market power', 'poder de mercado', 'lerner', 'markup']):
            return 'Poder de mercado'
        elif any(term in citation_lower for term in ['oligopoly', 'oligopolio', 'oligopolistic']):
            return 'Oligopolio'
        elif any(term in citation_lower for term in ['competition', 'competencia', 'competitive', 'competitivo']):
            return 'Competencia'
        elif any(term in citation_lower for term in ['barriers', 'barreras', 'entry']):
            return 'Barreras de entrada'
        elif any(term in citation_lower for term in ['economies of scale', 'economías de escala']):
            return 'Economías de escala'
        elif any(term in citation_lower for term in ['product differentiation', 'diferenciación', 'differentiated']):
            return 'Diferenciación de producto'
        elif any(term in citation_lower for term in ['egg', 'huevo', 'huevos', 'poultry', 'avicultura']):
            return 'Mercado de huevo/avícola'
        else:
            return 'General'
    
    def extract_numeric_data(self, text, doc_name):
        """Extrae datos numéricos específicos del documento"""
        numeric_data = {
            'hhi_values': [],
            'cr_values': [],
            'lerner_values': [],
            'market_shares': [],
            'other_metrics': []
        }
        
        # Buscar IHH/HHI
        hhi_patterns = [
            r'(?:IHH|HHI|Herfindahl)[- ](?:Hirschman)?[- ](?:Index)?[:\s]*(\d[\d\.]*\d)',
            r'(?:IHH|HHI|Herfindahl)[:\s]*(\d[\d\.]*\d)',
            r'(?:Índice de Herfindahl|Herfindahl Index)[:\s]*(\d[\d\.]*\d)',
        ]
        
        for pattern in hhi_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = match.group(1).replace('.', '').replace(',', '.')
                    value = float(value_str)
                    if 0 < value < 10000:
                        context = self.get_context(text, match.start(), 200)
                        numeric_data['hhi_values'].append({
                            'value': value,
                            'context': context,
                            'source': doc_name
                        })
                except:
                    pass
        
        # Buscar CR4, CR5, CR8
        cr_patterns = [
            r'(?:CR4|CR5|CR8)[:\s]*(\d+[\.,]?\d*)\s*%',
            r'(?:CR4|CR5|CR8)[:\s]*(\d+[\.,]?\d*)',
            r'(?:four-firm concentration ratio|concentration ratio)[:\s]*(\d+[\.,]?\d*)\s*%',
        ]
        
        for pattern in cr_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = match.group(1).replace(',', '.')
                    value = float(value_str)
                    if 0 < value <= 100:
                        context = self.get_context(text, match.start(), 200)
                        numeric_data['cr_values'].append({
                            'value': value,
                            'context': context,
                            'source': doc_name
                        })
                except:
                    pass
        
        # Buscar Lerner
        lerner_patterns = [
            r'(?:Lerner|Índice de Lerner|Lerner Index)[:\s]*(\d+[\.,]?\d*)\s*%',
            r'(?:Lerner)[:\s]*(0\.\d+)',
            r'(?:Lerner coefficient)[:\s]*(\d+[\.,]?\d*)',
        ]
        
        for pattern in lerner_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = match.group(1).replace(',', '.')
                    value = float(value_str)
                    if 0 < value < 1:
                        value = value * 100  # Convertir a porcentaje
                    if 0 < value <= 100:
                        context = self.get_context(text, match.start(), 200)
                        numeric_data['lerner_values'].append({
                            'value': value,
                            'context': context,
                            'source': doc_name
                        })
                except:
                    pass
        
        # Buscar cuotas de mercado
        market_share_patterns = [
            r'(?:market share|cuota de mercado|participación)[:\s]*(\d+[\.,]?\d*)\s*%',
            r'(?:\d+[\.,]?\d*)\s*%\s*(?:market share|cuota de mercado)',
        ]
        
        for pattern in market_share_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = re.search(r'\d+[\.,]?\d*', match.group(0)).group(0).replace(',', '.')
                    value = float(value_str)
                    if 0 < value <= 100:
                        context = self.get_context(text, match.start(), 200)
                        numeric_data['market_shares'].append({
                            'value': value,
                            'context': context,
                            'source': doc_name
                        })
                except:
                    pass
        
        return numeric_data
    
    def get_context(self, text, position, window_size):
        """Obtiene contexto alrededor de una posición"""
        start = max(0, position - window_size // 2)
        end = min(len(text), position + window_size // 2)
        context = text[start:end].strip()
        # Limpiar saltos de línea
        context = ' '.join(context.split())
        return context
    
    def extract_document_structure(self, text, doc_name):
        """Extrae la estructura del documento"""
        structure = {
            'title': '',
            'authors': '',
            'abstract': '',
            'methodology': '',
            'key_findings': [],
            'conclusions': []
        }
        
        # Buscar título (primeras líneas significativas)
        lines = text.split('\n')
        for i, line in enumerate(lines[:30]):
            line = line.strip()
            if len(line) > 20 and not line.startswith('---') and not line.startswith('ARCHIVO'):
                structure['title'] = line
                break
        
        # Buscar autores
        author_patterns = [
            r'(?:by|por|authors?:?)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:,|\s+(?:and|y))\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, text[:3000])
            if match:
                structure['authors'] = match.group(0)
                break
        
        # Buscar abstract/resumen
        abstract_patterns = [
            r'(?:Abstract|Resumen)[:\s]*\n?(.*?)(?:\n\s*\n|\n(?:Keywords|Palabras|Introduction|Introducción))',
            r'(?:Abstract|Resumen)[:\s]*(.*?)(?:\.?\s*Keywords|\.?\s*Palabras)',
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                structure['abstract'] = match.group(1).strip()[:1000]  # Limitar a 1000 chars
                break
        
        # Buscar metodología
        methodology_patterns = [
            r'(?:Methodology|Método|Methods|Metodología)[:\s]*\n?(.*?)(?:\n\s*\n|\n(?:Results|Resultados))',
            r'(?:We use|utilizamos|employing|empleando)\s+(.*?)(?:\.|$)',
        ]
        
        for pattern in methodology_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                structure['methodology'] = match.group(1).strip()[:500]
                break
        
        # Buscar hallazgos clave
        findings_patterns = [
            r'(?:findings|hallazgos|results|resultados)[:\s]*\n?(.*?)(?:\n\s*\n|\n(?:Conclusion|Conclusión))',
            r'(?:We find|encontramos|evidence|evidencia)[:\s]*(.*?)(?:\.|$)',
        ]
        
        for pattern in findings_patterns:
            matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
            for match in matches:
                finding = match.group(1).strip()[:300]
                if finding and finding not in structure['key_findings']:
                    structure['key_findings'].append(finding)
                    if len(structure['key_findings']) >= 5:
                        break
        
        return structure
    
    def analyze_single_document(self, txt_file):
        """Analiza un documento en profundidad"""
        print(f"  Analizando: {txt_file.name.encode('ascii', 'ignore').decode('ascii')}")
        
        # Leer texto
        with open(txt_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extraer información
        doc_name = txt_file.stem
        structure = self.extract_document_structure(text, doc_name)
        citations = self.extract_textual_citations(text, doc_name)
        numeric_data = self.extract_numeric_data(text, doc_name)
        
        # Crear análisis completo
        analysis = {
            'filename': txt_file.name,
            'doc_name': doc_name,
            'structure': structure,
            'citations': citations,
            'numeric_data': numeric_data,
            'total_citations': len(citations),
            'topics_covered': list(set([c['topic'] for c in citations]))
        }
        
        return analysis
    
    def generate_comparative_citations(self, all_analyses):
        """Genera citas comparativas entre documentos"""
        comparative = {
            'by_topic': {},
            'key_quotes': [],
            'numeric_comparisons': []
        }
        
        # Agrupar citas por tema
        for analysis in all_analyses:
            for citation in analysis['citations']:
                topic = citation['topic']
                if topic not in comparative['by_topic']:
                    comparative['by_topic'][topic] = []
                comparative['by_topic'][topic].append({
                    'citation': citation['text'],
                    'source': citation['source']
                })
        
        # Seleccionar citas clave (las más informativas)
        for topic, citations in comparative['by_topic'].items():
            if citations:
                # Seleccionar las citas más largas (generalmente más informativas)
                sorted_citations = sorted(citations, key=lambda x: len(x['citation']), reverse=True)
                comparative['key_quotes'].append({
                    'topic': topic,
                    'best_citation': sorted_citations[0]['citation'],
                    'source': sorted_citations[0]['source'],
                    'total_sources': len(citations)
                })
        
        return comparative
    
    def generate_deep_synthesis(self, all_analyses, comparative):
        """Genera síntesis profunda basada en los documentos"""
        synthesis = {
            'document_summary': [],
            'theoretical_framework': '',
            'empirical_evidence': '',
            'key_contributions': [],
            'research_gaps': [],
            'methodological_insights': []
        }
        
        # Resumen por documento
        for analysis in all_analyses:
            doc_summary = {
                'filename': analysis['filename'],
                'title': analysis['structure']['title'],
                'authors': analysis['structure']['authors'],
                'main_contribution': '',
                'key_findings': analysis['structure']['key_findings'][:3],
                'relevant_citations': [
                    c['text'] for c in analysis['citations'] 
                    if c['topic'] in ['Concentración de mercado', 'Poder de mercado', 'Oligopolio']
                ][:3]
            }
            synthesis['document_summary'].append(doc_summary)
        
        # Marco teórico basado en documentos
        theoretical_topics = comparative.get('by_topic', {}).get('Oligopolio', [])
        if theoretical_topics:
            synthesis['theoretical_framework'] = (
                f"La literatura revisada aborda múltiples aspectos de la teoría de oligopolio. "
                f"Se encontraron {len(theoretical_topics)} citas relevantes sobre este tema. "
                f"Los autores discuten principalmente: " + 
                "; ".join([t['citation'][:100] + "..." for t in theoretical_topics[:3]])
            )
        
        # Evidencia empírica
        empirical_topics = comparative.get('by_topic', {}).get('Concentración de mercado', [])
        if empirical_topics:
            synthesis['empirical_evidence'] = (
                f"En cuanto a evidencia empírica sobre concentración de mercado, "
                f"se encontraron {len(empirical_topics)} fuentes. Los hallazgos principales incluyen: " +
                "; ".join([t['citation'][:100] + "..." for t in empirical_topics[:3]])
            )
        
        # Contribuciones clave
        for analysis in all_analyses:
            if analysis['structure']['key_findings']:
                synthesis['key_contributions'].append({
                    'source': analysis['filename'],
                    'contribution': analysis['structure']['key_findings'][0] if analysis['structure']['key_findings'] else 'N/A'
                })
        
        return synthesis
    
    def run_deep_analysis(self):
        """Ejecuta el análisis profundo completo"""
        print("="*80)
        print("ANÁLISIS PROFUNDO DE DOCUMENTOS ACADÉMICOS")
        print("="*80)
        print()
        
        # Obtener todos los archivos de texto
        txt_files = [f for f in self.extracted_dir.glob("*.txt") 
                    if '_metadata' not in f.name and '_keydata' not in f.name]
        
        print(f"Encontrados {len(txt_files)} documentos para analizar")
        print()
        
        # Analizar cada documento
        all_analyses = []
        for i, txt_file in enumerate(txt_files, 1):
            print(f"[{i}/{len(txt_files)}]", end="")
            analysis = self.analyze_single_document(txt_file)
            all_analyses.append(analysis)
            print(f" - {analysis['total_citations']} citas encontradas")
        
        print()
        print("Generando análisis comparativo...")
        comparative = self.generate_comparative_citations(all_analyses)
        
        print("Generando síntesis profunda...")
        synthesis = self.generate_deep_synthesis(all_analyses, comparative)
        
        # Guardar resultados
        output_file = self.output_dir / "deep_analysis_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'analysis_date': datetime.now().isoformat(),
                'total_documents': len(all_analyses),
                'all_analyses': all_analyses,
                'comparative': comparative,
                'synthesis': synthesis
            }, f, indent=2, ensure_ascii=False)
        
        print()
        print("="*80)
        print("RESUMEN DEL ANÁLISIS PROFUNDO")
        print("="*80)
        print()
        
        # Estadísticas
        total_citations = sum(a['total_citations'] for a in all_analyses)
        all_topics = set()
        for a in all_analyses:
            all_topics.update(a['topics_covered'])
        
        print(f"Total documentos analizados: {len(all_analyses)}")
        print(f"Total citas extraídas: {total_citations}")
        print(f"Temas cubiertos: {', '.join(all_topics)}")
        print()
        
        # Mostrar citas clave por tema
        print("CITAS CLAVE POR TEMA:")
        print("-"*80)
        for topic_data in comparative.get('key_quotes', []):
            print(f"\n{topic_data['topic'].upper()}:")
            print(f"  Fuente: {topic_data['source']}")
            print(f"  Cita: \"{topic_data['best_citation'][:200]}...\"")
            print(f"  Total fuentes: {topic_data['total_sources']}")
        
        print()
        print("="*80)
        print(f"Resultados guardados en: {output_file}")
        print("="*80)
        
        return all_analyses, comparative, synthesis


def main():
    """Función principal"""
    base_dir = r"D:\Proyecto estado del arte"
    extracted_dir = os.path.join(base_dir, "extracted_text")
    output_dir = os.path.join(base_dir, "deep_analysis")
    
    # Crear analizador y ejecutar
    analyzer = DeepDocumentAnalyzer(extracted_dir, output_dir)
    analyzer.run_deep_analysis()


if __name__ == "__main__":
    main()
