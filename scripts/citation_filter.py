"""
Citation Filter: Filtro de Calidad y Contexto Semantico
Proyecto: Estado del Arte - Mercado del Huevo en Colombia
Objetivo: Validar citas textuales con contexto, deduplicar y generar resumen de hallazgos
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime


class CitationFilter:
    """Filtro de calidad y contexto semantico para citas academicas"""

    def __init__(self, deep_analysis_dir, extracted_dir, output_dir):
        self.deep_analysis_dir = Path(deep_analysis_dir)
        self.extracted_dir = Path(extracted_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Ventana de contexto: 750 caracteres antes y despues
        self.context_window = 750

        # Tipo de contexto y puntajes
        self.context_scores = {
            'hallazgo_autor': 3,
            'referencia': 2,
            'cita_directa': 3,
            'afirmacion_general': 1,
            'datos_tabla': -1,
            'fragmento': 0
        }

        # Patrones de ruido
        self.noise_patterns = [
            r'---\s*P[Aa]GINA\s*\d+\s*---',
            r'---\s*PAGE\s*\d+\s*---',
            r'\d+\s*$',
            r'[|]\s*[|]\s*[|]',
            r'[^\x00-\x7F\u00C0-\u024F\u0400-\u04FF\u0590-\u05FF]{4,}',
            r'(?:Fuente|Source)[:\s]*[Ee]laboraci[oO]n propia',
            r'(?:Fuente|Source)[:\s]*Elaboraci[oO]n propia',
        ]

        # Patrones de contexto semantico
        self.hallazgo_patterns = [
            r'(?:encontramos|we\s+find|results\s+show|hallazgos?|evidencia|evidence\s+suggests)',
            r'(?:this\s+study|este\s+estudio|our\s+results|nuestros\s+resultados)',
            r'(?:the\s+analysis|el\s+an[aA]lisis|the\s+study|el\s+estudio)',
            r'(?:concluimos|concluye|conclude|concludes)',
            r'(?:demuestra|shows|demonstrates)',
            r'(?:sugiere|suggests|indica|indicates)',
            r'(?:encontramos que|encontr[oO] que|hallamos que)',
            r'(?:se\s+encuentra\s+que|se\s+observ[aA]\s+que|se\s+evidencia\s+que)',
            r'(?:el\s+(?:resultado|hallazgo)\s+(?:principal|key|m[aA]s\s+importante))',
        ]

        self.referencia_patterns = [
            r'(?:seg[uU]n|according\s+to|como\s+se[~nN]ala|as\s+noted\s+by|como\s+dice|como\s+se[~nN]ala)',
            r'(?:\(\d{4}\))',
            r'(?:et\s+al\.)',
            r'(?:citado\s+por|cited\s+by)',
            r'(?:Smith|Porter|Keynes|Varian|Hern[aA]ndez|Calle|Petrecolla|Bolotova)',
        ]

        self.tabla_patterns = [
            r'(?:\d+[\.,]?\d*\s*[%]\s*\d+[\.,]?\d*\s*[%])',
            r'(?:\|\s*\|)',
            r'(?:Fuente|Source)[:\s]',
            r'(?:IC|IT|IP|IE|ICC)\s+\d+',
            r'(?:IHH|HHI)\s+\d+',
        ]

    def load_data(self):
        """Carga datos del analisis profundo"""
        results_file = self.deep_analysis_dir / "deep_analysis_results.json"
        if not results_file.exists():
            print(f"Error: No se encuentra {results_file}")
            return None, None, None
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        all_analyses = data.get('all_analyses', [])
        comparative = data.get('comparative', {})
        synthesis = data.get('synthesis', {})
        return all_analyses, comparative, synthesis

    def load_original_text(self, doc_name):
        """Carga el texto original del documento"""
        # El doc_name es el nombre del archivo sin extension
        txt_file = self.extracted_dir / f"{doc_name}.txt"
        if txt_file.exists():
            with open(txt_file, 'r', encoding='utf-8') as f:
                return f.read()
        # Intentar con el nombre original del archivo
        return None

    def clean_text_for_search(self, text):
        """Limpia el texto para busqueda (normaliza whitespace)"""
        return re.sub(r'\s+', ' ', text)

    def find_citation_context(self, text, citation_text):
        """Busca la cita en el texto original y extrae contexto"""
        if not text:
            return None, None

        text_clean = self.clean_text_for_search(text)
        citation_clean = self.clean_text_for_search(citation_text)

        # Buscar fragmento largo de la cita (primeros 60 caracteres significativos)
        search_key = citation_clean[:60].strip()
        position = text_clean.find(search_key)

        if position == -1:
            # Intentar con menos caracteres
            search_key = citation_clean[:40].strip()
            position = text_clean.find(search_key)
            if position == -1:
                search_key = citation_clean[:30].strip()
                position = text_clean.find(search_key)
                if position == -1:
                    return None, None

        # Extraer contexto
        start = max(0, position - self.context_window)
        end = min(len(text_clean), position + len(search_key) + self.context_window)

        # Expandir a limites de oracion
        while start > 0 and text_clean[start] not in '.!?':
            start -= 1
        if start > 0:
            start += 1

        while end < len(text_clean) and text_clean[end] not in '.!?':
            end += 1
        if end < len(text_clean):
            end += 1

        context = text_clean[start:end].strip()
        return context, position

    def classify_context_type(self, context, citation_text):
        """Clasifica el tipo de contexto de la cita"""
        if not context:
            return 'fragmento'

        context_lower = context.lower()
        citation_lower = citation_text.lower()

        # Verificar si es datos de tabla
        if any(re.search(p, context) for p in self.tabla_patterns):
            return 'datos_tabla'

        # Verificar hallazgo del autor
        if any(re.search(p, context_lower) for p in self.hallazgo_patterns):
            return 'hallazgo_autor'

        # Verificar si es cita directa (entre comillas)
        if '"' in citation_text:
            return 'cita_directa'

        # Verificar referencia
        if any(re.search(p, context_lower) for p in self.referencia_patterns):
            return 'referencia'

        # Verificar si parece oracion completa
        if self.has_complete_sentence(citation_text):
            return 'afirmacion_general'

        return 'fragmento'

    def has_complete_sentence(self, text):
        """Verifica si el texto tiene estructura de oracion completa"""
        text_lower = text.lower().strip()

        # Si empieza con parentesis o simbolos raros, es fragmento
        if re.match(r'^[\[\(\).,:;]', text_lower):
            return False

        # Si termina con parentesis abierto o simbolos, es fragmento
        if re.match(r'.*[\(\[,:;]$', text_lower):
            return False

        # Debe ser una oracion con mas de 5 palabras
        words = text_lower.split()
        if len(words) < 6:
            return False

        patrones_completos = [
            # Plural noun + verb: "Eggs are...", "Results show..."
            r'\b\w{3,}s\s+(?:are|were|have|has|show|indicate|represent|constitute)\b',
            # Singular noun + verb: "The market is...", "The study shows..."
            r'\b\w{3,}\s+(?:is|was|has|shows|indicates|represents)\b',
            # Art + noun + verb
            r'\b(?:el|la|los|las|the|un|una|unos|unas|a|an)\s+\w+\s+\w+[ea]s?\b',
            r'\b(?:el|la|los|las|the|un|una|unos|unas|a|an)\s+\w+\s+(?:es|est[aá]|ha|fue|era|will|is|are|was|were|ser[aá]|estaba|tiene|puede|debe)\b',
            # Pronombre/articulo + verbo
            r'\b(?:nosotros|we|ellos|they|este|this|estos|these)\s+\w+\s+\w+[ea]n?\b',
            r'\b(?:se\s+encuentra|se\s+observ[aá]|se\s+evidencia|se\s+concluye|se\s+encuentran)\s+\w+',
            # Sujetos academicos comunes
            r'\b(?:el\s+mercado|la\s+industria|las\s+empresas|los\s+consumidores|el\s+estudio|la\s+investigaci[oó]n)\s+\w+',
            r'\b(?:la\s+concentraci[oó]n|el\s+IHH|el\s+[iI]ndice|la\s+competencia|el\s+resultado|los\s+resultados)\s+\w+',
            # Patrones en ingles
            r'\b(?:t?here\s+is|t?here\s+are|there\s+was)\s+\w+',
            r'\b(?:this\s+study|our\s+results|the\s+results|the\s+analysis|our\s+findings)\s+\w+',
            # Verbos modales
            r'\b(\w+\s+)*\w+\s+(?:can\s+be|may\s+be|could\s+be|should\s+be|would\s+be)\b',
            # Reflexivos y pasivas en espanol
            r'\bse\s+\w+[oa]\s+\w+',
        ]

        return any(re.search(p, text_lower) for p in patrones_completos)

    def is_noise(self, text):
        """Verifica si el texto es ruido (tablas, fragmentos, etc.)"""
        reasons = []

        # Demasiados saltos de linea
        if text.count('\n') > 5:
            reasons.append('demasiados saltos de linea')

        # Tiene marcadores de pagina
        for pattern in self.noise_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                reasons.append('contiene marcador de pagina/tabla')

        # Caracteres no legibles
        non_ascii = len(re.findall(r'[^\x00-\x7F\u00C0-\u024F]', text))
        if non_ascii > len(text) * 0.1 and non_ascii > 3:
            reasons.append('demasiados caracteres no legibles')

        # Comienza con numero de pagina
        if re.match(r'^\d+\s+[A-Z]', text):
            reasons.append('comienza con numero de pagina')

        # Termina con parentesis abierto o coma (fragmento incompleto)
        if re.match(r'.*[\(\[,:;]\s*$', text):
            reasons.append('termina incompleto')

        # Contiene solo numeros y signos de puntuacion
        only_numeric = re.sub(r'[\d\s\.,\-\(\)\[\]%$€]', '', text)
        if len(only_numeric) < len(text) * 0.3:
            reasons.append('mayormente numerico')

        # Contiene demasiados pipes (datos de tabla)
        if text.count('|') > 2:
            reasons.append('contiene pipes (datos tabla)')

        # Comienza con minuscula (fragmento de oracion)
        if re.match(r'^[a-z]', text.strip()):
            reasons.append('comienza en minuscula (fragmento)')

        # Tiene mas de 3 palabras que contienen solo numeros
        words = text.split()
        numeric_words = sum(1 for w in words if re.match(r'^\d+[\.,]?\d*$', w.strip()))
        if numeric_words > 3:
            reasons.append('demasiados numeros')

        # Contiene direcciones de URL o DOI
        if re.search(r'http[s]?://|doi\.org|www\.', text):
            reasons.append('contiene URL/DOI')

        # Parece encabezado de tabla (lineas con columnas alineadas)
        lines = text.split('\n')
        column_like = sum(1 for line in lines if re.match(r'^\s*\w+\s+\d+\s+\d+', line))
        if column_like > 2:
            reasons.append('parece tabla (columnas alineadas)')

        # Parece titulo/encabezado (todo mayusculas, pocas palabras)
        upper_words = sum(1 for w in words if w.isupper() and len(w) > 2)
        if len(words) < 15 and upper_words > len(words) * 0.5:
            reasons.append('parece encabezado/titulo')

        # Contiene secuencias raras como "---" o "***"
        if re.search(r'[-*]{3,}', text):
            reasons.append('contiene separador')

        # Parece fila de tabla con mezcla de letras sueltas
        if re.search(r'\b[a-z]\s+[a-z]\s+[a-z]\b', text):
            reasons.append('contiene letras sueltas (tabla)')

        # Empieza con numero de seccion (1., 2., a), b)) 
        if re.match(r'^\s*(?:\d+\.|[a-zA-Z]\)|[a-zA-Z]\.)\s+', text):
            reasons.append('empieza con numero/letra de seccion')

        return len(reasons) > 0, ', '.join(reasons) if reasons else None

    def assess_citation_quality(self, citation_text, context, classification):
        """Evalua la calidad de una cita"""
        quality_score = 0
        reasons = []

        # Puntaje por tipo de contexto
        score = self.context_scores.get(classification, 0)
        quality_score += score
        if score > 0:
            reasons.append(f"contexto: {classification}")

        # Puntaje por longitud
        if len(citation_text) > 250:
            quality_score += 2
            reasons.append('cita muy extensa (>250 chars)')
        elif len(citation_text) > 120:
            quality_score += 1
            reasons.append('cita completa (120-250 chars)')
        elif len(citation_text) < 50:
            quality_score -= 2
            reasons.append('cita demasiado corta')

        # Puntaje por estructura gramatical
        if self.has_complete_sentence(citation_text):
            quality_score += 2
            reasons.append('oracion completa')
        else:
            quality_score -= 2
            reasons.append('fragmento incompleto')

        # Puntaje por presencia moderada de datos numericos
        numeric_count = len(re.findall(r'\d+[\.,]?\d*', citation_text))
        if 1 <= numeric_count <= 3:
            quality_score += 1
            reasons.append('contiene datos numericos relevantes')
        elif numeric_count > 5:
            quality_score -= 1
            reasons.append('demasiados datos numericos')

        # Penalizar ruido evidente
        is_noise, noise_reason = self.is_noise(citation_text)
        if is_noise:
            quality_score -= 4
            reasons.append(f"ruido: {noise_reason}")

        # Bonus por contexto rico
        if context and len(context) > 200:
            quality_score += 1
            reasons.append('contexto rico disponible')

        # Penalizar si comienza con conjuncion/relativo
        if re.match(r'^(?:que|which|where|who|y|and|but|pero|mas|sin|para|con|de\s+la|del|en\s+(?:el|la)|por\s+(?:el|la)|al|this|that|these|those)\s', citation_text.lower().strip()):
            quality_score -= 1
            reasons.append('comienza con conjuncion')

        # Penalizar si termina en preposicion o articulo
        if re.match(r'.*\s(?:de|en|con|para|por|a|the|a|an|el|la|los|las|un|una|del|al)\s*$', citation_text.lower().strip()):
            quality_score -= 1
            reasons.append('termina en preposicion/articulo')

        # Bonus por ser una afirmacion sustancial (muchas palabras significativas)
        words = citation_text.split()
        content_words = [w for w in words if len(w) > 3]
        if len(content_words) > 12:
            quality_score += 1
            reasons.append('oracion sustancial')

        # Redondear score minimo en -5
        quality_score = max(-5, quality_score)

        return quality_score, reasons

    def deduplicate_citations(self, citations):
        """Elimina citas duplicadas o muy similares del mismo documento"""
        deduped = []
        seen = []

        for citation in sorted(citations, key=lambda x: x['quality_score'], reverse=True):
            text = citation['citation_text'].lower()[:100]
            source = citation['source']

            is_dup = False
            for existing in seen:
                if existing['source'] == source:
                    # Similitud simple: palabras compartidas
                    words1 = set(text.split())
                    words2 = set(existing['text'].split())
                    if not words1 or not words2:
                        continue
                    similarity = len(words1 & words2) / max(len(words1), len(words2))
                    if similarity > 0.6:
                        is_dup = True
                        break

            if not is_dup:
                deduped.append(citation)
                seen.append({'source': source, 'text': text})

        return deduped

    def extract_simple_author_reference(self, context):
        """Extrae referencia simple autor/año si es facil de detectar"""
        # Solo patrones muy simples
        patterns = [
            r'([A-Z][a-z]+(?:\s+(?:et\s+al\.?|and\s+[A-Z][a-z]+|y\s+[A-Z][a-z]+))?)\s*\((\d{4})\)',
        ]
        for pattern in patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(0)
        return None

    def process_all_citations(self, all_analyses):
        """Procesa todas las citas aplicando filtros"""
        print("="*80)
        print("FILTRO DE CALIDAD Y CONTEXTO DE CITAS")
        print("="*80)
        print()

        all_filtered = []
        stats = {'total_original': 0, 'by_document': {}}
        findings_by_doc = {}

        total_docs = len(all_analyses)

        for doc_idx, analysis in enumerate(all_analyses, 1):
            doc_name = analysis.get('doc_name', '')
            filename = analysis.get('filename', '')
            citations = analysis.get('citations', [])
            structure = analysis.get('structure', {})

            print(f"[{doc_idx}/{total_docs}] {filename.encode('ascii', 'ignore').decode('ascii')}")

            # Cargar texto original
            original_text = self.load_original_text(doc_name)

            doc_filtered = []
            doc_rejected = []

            for citation in citations:
                citation_text = citation.get('text', '').strip()
                topic = citation.get('topic', 'General')

                if not citation_text or len(citation_text) < 25:
                    continue

                # Obtener contexto
                context, position = self.find_citation_context(original_text, citation_text)

                # Clasificar contexto
                classification = self.classify_context_type(context, citation_text)

                # Evaluar calidad
                quality_score, reasons = self.assess_citation_quality(
                    citation_text, context, classification
                )

                # Verificar ruido
                is_noise, noise_reason = self.is_noise(citation_text)

                # Extraer referencia simple si existe
                simple_ref = None
                if context and classification in ['referencia', 'hallazgo_autor']:
                    simple_ref = self.extract_simple_author_reference(context)

                citation_entry = {
                    'citation_text': citation_text,
                    'source': doc_name,
                    'filename': filename,
                    'topic': topic,
                    'classification': classification,
                    'quality_score': quality_score,
                    'quality_level': self.get_quality_level(quality_score),
                    'reasons': reasons,
                    'is_noise': is_noise,
                    'noise_reason': noise_reason,
                    'context': context[:500] if context else None,
                    'simple_reference': simple_ref
                }

                if is_noise or quality_score < 0:
                    doc_rejected.append(citation_entry)
                else:
                    doc_filtered.append(citation_entry)

            # Deduplicar
            doc_filtered = self.deduplicate_citations(doc_filtered)

            # Reordenar por calidad
            doc_filtered.sort(key=lambda x: x['quality_score'], reverse=True)

            all_filtered.extend(doc_filtered)

            # Estadisticas del documento
            doc_stats = {
                'total_raw': len(citations),
                'accepted': len(doc_filtered),
                'rejected': len(doc_rejected),
                'quality_distribution': {}
            }

            for level in ['alta', 'media', 'baja']:
                count = len([c for c in doc_filtered if c['quality_level'] == level])
                doc_stats['quality_distribution'][level] = count

            stats['by_document'][filename] = doc_stats

            # Hallazgos del documento (citas de alta calidad con contexto)
            doc_findings = {
                'filename': filename,
                'doc_name': doc_name,
                'title': structure.get('title', 'Sin titulo'),
                'total_accepted': len(doc_filtered),
                'high_quality': [c for c in doc_filtered if c['quality_level'] == 'alta'],
                'main_topics': list(set(c['topic'] for c in doc_filtered)),
                'quality_summary': f"{doc_stats['quality_distribution']['alta']} alta, "
                                   f"{doc_stats['quality_distribution']['media']} media, "
                                   f"{doc_stats['quality_distribution']['baja']} baja"
            }
            findings_by_doc[filename] = doc_findings

            print(f"  Raw: {len(citations)} | Aceptadas: {doc_stats['accepted']} | "
                  f"Rechazadas: {doc_stats['rejected']}")

        # Separar por nivel de calidad
        high_quality = [c for c in all_filtered if c['quality_level'] == 'alta']
        medium_quality = [c for c in all_filtered if c['quality_level'] == 'media']
        low_quality = [c for c in all_filtered if c['quality_level'] == 'baja']

        print()
        print("="*80)
        print("RESUMEN DEL FILTRADO")
        print("="*80)
        print(f"Total citas originales: {stats['total_original']}")
        print(f"Total citas aceptadas: {len(all_filtered)}")
        print(f"  - Alta calidad: {len(high_quality)}")
        print(f"  - Media calidad: {len(medium_quality)}")
        print(f"  - Baja calidad: {len(low_quality)}")
        print()

        return all_filtered, stats, findings_by_doc

    def get_quality_level(self, score):
        """Obtiene el nivel de calidad basado en el puntaje"""
        if score >= 5:
            return 'alta'
        elif score >= 2:
            return 'media'
        elif score >= 0:
            return 'baja'
        return 'ruido'

    def generate_findings_summary(self, findings_by_doc, output_file):
        """Genera resumen de hallazgos por documento"""
        total_alta = sum(len(f['high_quality']) for f in findings_by_doc.values())
        total_media = sum(
            len([c for c in f.get('high_quality', [])] +
                [{'quality_level': 'media'}]) 
            for f in findings_by_doc.values()
        )

        content = """# Resumen de Hallazgos por Documento
## Filtro de Calidad de Citas Academicas

---

## Estadisticas Generales

| Metrica | Valor |
|---------|-------|
| Documentos analizados | {docs} |
| Citas de alta calidad | {alta} |
| Citas de media calidad | {media} |

---

## Hallazgos por Documento

""".format(
            docs=len(findings_by_doc),
            alta=total_alta,
            media=total_media
        )

        for filename, findings in findings_by_doc.items():
            content += f"\n### {findings['title'][:100]}\n"
            content += f"**Archivo:** {filename}\n"
            content += f"**Calidad:** {findings['quality_summary']}\n"
            content += f"**Temas:** {', '.join(findings['main_topics'][:5])}\n\n"

            if findings['high_quality']:
                content += "#### Hallazgos de Alta Calidad:\n\n"
                for cit in findings['high_quality'][:5]:
                    # Limitar a 200 chars para el resumen
                    text = cit['citation_text'][:200]
                    content += f"- \"{text}...\"\n"
                    content += f"  - Tema: {cit['topic']} | Contexto: {cit['classification']}\n"
                    if cit['simple_reference']:
                        content += f"  - Referencia: {cit['simple_reference']}\n"
                    content += "\n"

            content += "---\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Resumen de hallazgos guardado en: {output_file}")

    def generate_clean_state_of_art(self, all_filtered, output_file):
        """Genera estado del arte limpio solo con citas de calidad"""
        high_quality = [c for c in all_filtered if c['quality_level'] == 'alta']
        medium_quality = [c for c in all_filtered if c['quality_level'] == 'media']

        # Agrupar por tema
        by_topic = {}
        for citation in high_quality + medium_quality:
            topic = citation['topic']
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(citation)

        content = """# Estado del Arte: Citas Verificadas con Contexto
## Filtradas por Calidad Semantica

---

## Resumen

Este documento contiene {total} citas verificadas con contexto.
- **Alta calidad:** {alta} citas
- **Media calidad:** {media} citas

---

""".format(
            total=len(high_quality) + len(medium_quality),
            alta=len(high_quality),
            media=len(medium_quality)
        )

        for topic in sorted(by_topic.keys()):
            citations = by_topic[topic]
            # Ordenar: alta primero, luego media
            citations.sort(key=lambda x: x['quality_score'], reverse=True)

            content += f"\n## {topic}\n\n"

            for citation in citations:
                text = citation['citation_text'][:400]
                level_label = "ALTA" if citation['quality_level'] == 'alta' else "MEDIA"
                content += f"### [{level_label}] \"{text}\"\n"
                content += f"**Fuente:** {citation['filename']} | "
                content += f"**Score:** {citation['quality_score']} | "
                content += f"**Contexto:** {citation['classification']}\n"

                if citation.get('simple_reference'):
                    content += f"**Referencia:** {citation['simple_reference']}\n"

                if citation.get('context'):
                    ctx = citation['context'][:300]
                    content += f"**Contexto:** {ctx}...\n"

                content += "\n"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Estado del arte limpio guardado en: {output_file}")

    def save_filtered_results(self, all_filtered, stats, findings_by_doc):
        """Guarda los resultados filtrados en JSON"""
        output = {
            'filtering_date': datetime.now().isoformat(),
            'parameters': {
                'context_window': self.context_window,
            },
            'stats': {
                'total_filtered': len(all_filtered),
                'by_quality': {
                    'alta': len([c for c in all_filtered if c['quality_level'] == 'alta']),
                    'media': len([c for c in all_filtered if c['quality_level'] == 'media']),
                    'baja': len([c for c in all_filtered if c['quality_level'] == 'baja']),
                }
            },
            'filtered_citations': all_filtered,
            'findings_by_document': {
                k: {
                    'filename': v['filename'],
                    'title': v['title'],
                    'total_accepted': v['total_accepted'],
                    'high_quality_count': len(v['high_quality']),
                    'main_topics': v['main_topics'],
                    'quality_summary': v['quality_summary']
                }
                for k, v in findings_by_doc.items()
            }
        }

        output_file = self.output_dir / "citations_filtered.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Datos filtrados guardados en: {output_file}")

    def run(self):
        """Ejecuta el pipeline completo de filtrado"""
        # Cargar datos
        all_analyses, comparative, synthesis = self.load_data()
        if not all_analyses:
            print("Error: No se pudieron cargar los datos.")
            return

        # Contar citas originales
        total_raw = sum(len(a.get('citations', [])) for a in all_analyses)

        # Procesar
        all_filtered, stats, findings_by_doc = self.process_all_citations(all_analyses)

        # Actualizar estadisticas
        stats['total_original'] = total_raw

        # Guardar resultados JSON
        self.save_filtered_results(all_filtered, stats, findings_by_doc)

        # Generar resumen de hallazgos
        summary_file = self.output_dir / "findings_summary.md"
        self.generate_findings_summary(findings_by_doc, summary_file)

        # Generar estado del arte limpio
        clean_file = self.output_dir / "estado_del_arte_limpio.md"
        self.generate_clean_state_of_art(all_filtered, clean_file)

        print()
        print("="*80)
        print("FILTRADO COMPLETADO EXITOSAMENTE")
        print("="*80)
        print(f"Archivos generados:")
        print(f"  - {self.output_dir}/citations_filtered.json")
        print(f"  - {self.output_dir}/findings_summary.md")
        print(f"  - {self.output_dir}/estado_del_arte_limpio.md")
        print()
        print(f"Resumen: {total_raw} -> {len(all_filtered)} citas "
              f"({total_raw - len(all_filtered)} eliminadas)")


def main():
    """Funcion principal"""
    base_dir = r"D:\Proyecto estado del arte"
    deep_analysis_dir = os.path.join(base_dir, "deep_analysis")
    extracted_dir = os.path.join(base_dir, "extracted_text")
    output_dir = os.path.join(base_dir, "filtered_analysis")

    filter_obj = CitationFilter(deep_analysis_dir, extracted_dir, output_dir)
    filter_obj.run()


if __name__ == "__main__":
    main()
