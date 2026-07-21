import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(r'D:\Proyecto estado del arte')

# Human-readable names for documents
DOC_NAME_MAP = {
    'Estudio_Huevos_CarnePollo_2022.txt': 'Estudio Fenavi/SC - Huevos y Carne de Pollo (2022)',
    'The_role_of_market_concentration_in_the.txt': 'Concentracion de Mercado en Cadena Agroalimentaria',
    'Market_Structure_and_Price_Transmission.txt': 'Estructura de Mercado y Transmision de Precios',
    'Art_XX_Concentración+y+poder+de+mercado.txt': 'Articulo XX - Concentracion y Poder de Mercado',
    'concentracion y poder de mercado.txt': 'Concentracion y Poder de Mercado',
    'Impulso – Análisis de la estructura de mercado de productos pecuarios.txt': 'Impulso - Estructura de Mercado Productos Pecuarios',
    'FinalThesis_AwolZeberga.txt': 'Tesis Final - Awol Zeberga',
    'CalleCamilo_2018_CompetitividadAvicolaColombia.txt': 'Calle y Camilo (2018) - Competitividad Avicola Colombia',
    'Market Composition and Performance of Firms in Broiler, Chicken Egg, and Swine Production- Implications to the Philippine Competition Act.txt': 'Mercado Avicola Filipinas - Ley de Competencia',
    'understanding-oligopoly-structure-behavior-and-implications.txt': 'Estructura Oligopolica - Comportamiento e Implicaciones',
    'American J Agri Economics - 2026 - Kang - Food inflation passthrough from agricultural imports in a small open economy.txt': 'Kang (2026) - Inflacion de Alimentos en Economia Abierta',
    'Applied Eco Perspectives Pol - 2026 - Zhao - Understanding Egg Price Volatility and Policy Implications in the U S  With.txt': 'Zhao (2026) - Volatilidad Precios Huevo en EE.UU.',
    'admin,+9.+399+Done.+New.txt': 'Estudio Agroindustrial - Nueva Publicacion',
    'sustainability-14-08030.txt': 'Sostenibilidad en Mercados Agricolas',
    'economies-12-00245-v2.txt': 'Economias - Analisis de Mercado',
    '10.30490_aead.2023.351385.1253.txt': 'AEAD (2023) - Choques de Precios en Mercado de Huevo Irani',
    '588_agris-on-line-3-2023-khoiriyah-forgenie-iriany.txt': 'Khoiriyah et al. (2023) - Patrones Alimentarios',
    '5.+Modelling+Food+Patterns+in+Pakistan.txt': 'Modelado de Patrones Alimentarios en Pakistan',
    'SAEA2015_AgProductionRestrictionsAntitrustAnalysis_Bolotova 01-15-2015.txt': 'Bolotova (2015) - Restricciones de Produccion y Antitrust',
    'Presidential Address.txt': 'Discurso Presidencial - Economia Agricola',
    'American J Agri Economics - 2021 -  - Issue Information.txt': 'AJAE (2021) - Informacion de Edicion',
    'Condiciones de competencia en cadenas.txt': 'Condiciones de Competencia en Cadenas',
    '20130203163434703403.txt': 'Estudio de Mercado Agroindustrial (2013)',
    'The role of market concentration in the.txt': 'Rol de la Concentracion de Mercado',
    'Artikel5_Ana+Arifatus.txt': 'Ana y Arifatus - Analisis de Mercado',
    'Shibia et al paper for SAEA Conference.txt': 'Shibia et al. - Conferencia SAEA',
    'Egg study EEUU.txt': 'Estudio de Huevo - EE.UU. (sin citas extraidas)',
    'Estudio del arte huevos colombia.txt': 'Estado del Arte - Huevos Colombia',
}


def clean_filename(filename):
    if filename in DOC_NAME_MAP:
        return DOC_NAME_MAP[filename]
    name = filename.replace('.txt', '')
    name = name.replace('.pdf', '')
    name = re.sub(r'[_\-\+]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > 60:
        words = name.split()
        result = []
        length = 0
        for w in words:
            if length + len(w) > 55:
                result.append('...')
                break
            result.append(w)
            length += len(w) + 1
        name = ' '.join(result)
    return name


def extract_key_finding(citations, doc_name):
    alta = [c for c in citations if c.get('quality_level') == 'alta']
    alta.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
    if alta:
        text = alta[0]['citation_text']
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 250:
            text = text[:250] + '...'
        return text

    media = [c for c in citations if c.get('quality_level') == 'media']
    media.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
    if media:
        text = media[0]['citation_text']
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 250:
            text = text[:250] + '...'
        return text
    return None

def generate():
    with open(BASE / 'filtered_analysis' / 'citations_filtered.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    citations = data['filtered_citations']

    # Group by filename
    docs = defaultdict(list)
    for c in citations:
        docs[c['filename']].append(c)

    # Determine primary topic per document (most frequent)
    doc_topics = {}
    for fname, clist in docs.items():
        topic_counts = Counter(c['topic'] for c in clist)
        doc_topics[fname] = topic_counts.most_common(3)

    # All unique topics
    all_topics = sorted(set(c['topic'] for c in citations))

    # Build graph data
    nodes = []
    links = []

    # Map for quick dedup
    topic_to_id = {}

    # Central node
    nodes.append({
        'id': 'central',
        'label': 'Estado del Arte: Mercado del Huevo',
        'type': 'central',
        'size': 50,
        'color': '#3b82f6'
    })

    # Topic nodes
    topic_colors = ['#64748b', '#64748b', '#64748b', '#64748b', '#64748b',
                    '#64748b', '#64748b', '#64748b', '#64748b', '#64748b']
    for i, topic in enumerate(all_topics):
        tid = f'topic_{i}'
        topic_to_id[topic] = tid
        count = sum(1 for c in citations if c['topic'] == topic)
        nodes.append({
            'id': tid,
            'label': topic,
            'type': 'topic',
            'count': count,
            'size': 18 + min(count, 50),
            'color': topic_colors[i] if i < len(topic_colors) else '#94a3b8'
        })
        links.append({'source': 'central', 'target': tid, 'sourceType': 'central', 'targetType': 'topic'})

    # Document nodes
    quality_colors = {'alta': '#22c55e', 'media': '#eab308', 'baja': '#f97316'}

    for fname, clist in docs.items():
        doc_id = f'doc_{fname.replace(".", "_").replace(" ", "_")[:80]}'
        name = clean_filename(fname)

        quality_dist = Counter(c.get('quality_level', 'baja') for c in clist)
        primary_quality = quality_dist.most_common(1)[0][0] if quality_dist else 'baja'

        # Get short summary
        key_finding = extract_key_finding(clist, name)

        # Build citations list for side panel
        cit_list = []
        for c in sorted(clist, key=lambda x: x.get('quality_score', 0), reverse=True):
            text = c['citation_text']
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 300:
                text = text[:300] + '...'
            cit_list.append({
                'text': text,
                'quality': c.get('quality_level', 'baja'),
                'score': c.get('quality_score', 0),
                'context': c.get('context', '')[:400] if c.get('context') else '',
                'reference': c.get('simple_reference')
            })

        node_size = 12 + min(len(clist) * 2, 40)
        doc_node = {
            'id': doc_id,
            'label': name,
            'type': 'doc',
            'filename': fname,
            'count': len(clist),
            'size': node_size,
            'color': quality_colors.get(primary_quality, '#94a3b8'),
            'quality_dist': dict(quality_dist),
            'primary_quality': primary_quality,
            'key_finding': key_finding,
            'citations': cit_list,
            'topics': [t for t, _ in doc_topics[fname]]
        }
        nodes.append(doc_node)

        # Connect to TOPICS of this document (not just primary)
        for topic, count in doc_topics[fname]:
            tid = topic_to_id.get(topic)
            if tid:
                # Only link once (skip duplicates from different doc->topic pairs)
                link_id = f'{doc_id}->{tid}'
                if not any(l.get('id') == link_id for l in links):
                    links.append({
                        'id': link_id,
                        'source': doc_id,
                        'target': tid,
                        'sourceType': 'doc',
                        'targetType': 'topic',
                        'weight': count
                    })

    graph = {
        'nodes': nodes,
        'links': links,
        'stats': {
            'total_documents': len(docs),
            'total_topics': len(all_topics),
            'total_citations': len(citations),
            'quality_alta': sum(1 for c in citations if c.get('quality_level') == 'alta'),
            'quality_media': sum(1 for c in citations if c.get('quality_level') == 'media'),
            'quality_baja': sum(1 for c in citations if c.get('quality_level') == 'baja'),
        }
    }

    out_path = BASE / 'web' / 'data.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(f'Graph data generated: {out_path}')
    print(f'  Nodes: {len(nodes)} (1 central + {len(all_topics)} topics + {len(docs)} docs)')
    print(f'  Links: {len(links)}')
    print(f'  Documents: {len(docs)}')
    print(f'  Citations: {len(citations)}')
    print()

    # Show top documents
    doc_stats = sorted([(clean_filename(f), len(c)) for f, c in docs.items()], key=lambda x: x[1], reverse=True)
    print('Top documents by citation count:')
    for name, count in doc_stats[:10]:
        print(f'  {name}: {count} citas')

if __name__ == '__main__':
    generate()
