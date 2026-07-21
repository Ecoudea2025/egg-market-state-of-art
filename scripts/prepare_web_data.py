import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(r'D:\Proyecto estado del arte')
DOCS_DATA = BASE / 'docs' / 'data'

DOC_NAME_MAP = {
    'Estudio_Huevos_CarnePollo_2022.txt': 'Estudio Fenavi/SC - Huevos y Carne de Pollo (2022)',
    'The_role_of_market_concentration_in_the.txt': 'Concentracion de Mercado en Cadena Agroalimentaria',
    'Market_Structure_and_Price_Transmission.txt': 'Estructura de Mercado y Transmision de Precios',
    'Art_XX_Concentracion+y+poder+de+mercado.txt': 'Articulo XX - Concentracion y Poder de Mercado',
    'concentracion y poder de mercado.txt': 'Concentracion y Poder de Mercado',
    'Impulso - Analisis de la estructura de mercado de productos pecuarios.txt': 'Impulso - Estructura de Mercado Productos Pecuarios',
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
    'Artikel5_Ana+Arifatus.txt': 'Ana y Arifatus - Analisis de Mercado',
    'Shibia et al paper for SAEA Conference.txt': 'Shibia et al. - Conferencia SAEA',
}


def clean_name(filename):
    if filename in DOC_NAME_MAP:
        return DOC_NAME_MAP[filename]
    name = filename.replace('.txt', '').replace('.pdf', '')
    name = re.sub(r'[_\-\+]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > 65:
        name = name[:62] + '...'
    return name


def generate_all():
    DOCS_DATA.mkdir(parents=True, exist_ok=True)

    with open(BASE / 'filtered_analysis' / 'citations_filtered.json', 'r', encoding='utf-8') as f:
        raw = json.load(f)

    citations = raw['filtered_citations']

    # ============================================================
    # 1. citations.json + citations.js — Todas las citas
    # ============================================================
    cit_list = []
    for c in citations:
        text = re.sub(r'\s+', ' ', c['citation_text']).strip()
        ctx = re.sub(r'\s+', ' ', c.get('context', '')[:500]).strip() if c.get('context') else ''
        cit_list.append({
            'text': text[:400],
            'quality': c.get('quality_level', 'baja'),
            'score': c.get('quality_score', 0),
            'topic': c.get('topic', ''),
            'document': clean_name(c.get('filename', '')),
            'filename': c.get('filename', ''),
            'context': ctx,
            'reference': c.get('simple_reference'),
        })

    # Sort by score descending
    cit_list.sort(key=lambda x: x['score'], reverse=True)

    write_files(cit_list, 'citations')

    # ============================================================
    # 2. documents.json + documents.js — Documentos con metadata
    # ============================================================
    by_doc = defaultdict(list)
    for c in citations:
        by_doc[c['filename']].append(c)

    docs_list = []
    for fname, clist in sorted(by_doc.items()):
        qdist = Counter(c.get('quality_level', 'baja') for c in clist)
        topics = Counter(c.get('topic', 'General') for c in clist)
        primary_quality = qdist.most_common(1)[0][0]

        # Key finding
        alta = [c for c in clist if c.get('quality_level') == 'alta']
        alta.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        key = None
        if alta:
            key = re.sub(r'\s+', ' ', alta[0]['citation_text']).strip()[:250]
        else:
            media = [c for c in clist if c.get('quality_level') == 'media']
            media.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
            if media:
                key = re.sub(r'\s+', ' ', media[0]['citation_text']).strip()[:250]

        # Citations for this doc
        doc_cits = []
        for c in sorted(clist, key=lambda x: x.get('quality_score', 0), reverse=True):
            text = re.sub(r'\s+', ' ', c['citation_text']).strip()
            doc_cits.append({
                'text': text[:350],
                'quality': c.get('quality_level', 'baja'),
                'score': c.get('quality_score', 0),
                'context': re.sub(r'\s+', ' ', c.get('context', '')[:300]).strip() if c.get('context') else '',
                'reference': c.get('simple_reference'),
            })

        docs_list.append({
            'name': clean_name(fname),
            'filename': fname,
            'count': len(clist),
            'primary_quality': primary_quality,
            'quality_dist': {'alta': qdist.get('alta', 0), 'media': qdist.get('media', 0), 'baja': qdist.get('baja', 0)},
            'topics': [t for t, _ in topics.most_common(3)],
            'key_finding': key,
            'citations': doc_cits,
        })

    docs_list.sort(key=lambda x: x['count'], reverse=True)
    write_files(docs_list, 'documents')

    # ============================================================
    # 3. graph.json + graph.js — Grafo del mapa mental
    # ============================================================
    graph = build_graph(citations, by_doc)
    write_files(graph, 'graph')

    # ============================================================
    # 4. stats.json + stats.js — Metricas resumen
    # ============================================================
    topics = Counter(c.get('topic', 'General') for c in citations)
    quality = Counter(c.get('quality_level', 'baja') for c in citations)

    stats = {
        'total_documents': len(by_doc),
        'total_citations': len(citations),
        'total_topics': len(topics),
        'quality': {
            'alta': quality.get('alta', 0),
            'media': quality.get('media', 0),
            'baja': quality.get('baja', 0),
        },
        'topics': [{'name': t, 'count': n} for t, n in topics.most_common()],
        'top_documents': [
            {'name': clean_name(f), 'count': len(c)}
            for f, c in sorted(by_doc.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        ],
    }
    write_files(stats, 'stats')

    # ============================================================
    # 5. Copy estado_del_arte.md
    # ============================================================
    md_src = BASE / 'filtered_analysis' / 'estado_del_arte_limpio.md'
    if md_src.exists():
        md_content = md_src.read_text(encoding='utf-8')
        (DOCS_DATA / 'estado_del_arte.md').write_text(md_content, encoding='utf-8')
        print(f'  estado_del_arte.md: {len(md_content)} chars')

    print()
    print('Archivos generados en docs/data/:')
    for f in sorted(DOCS_DATA.iterdir()):
        size = f.stat().st_size
        print(f'  {f.name}: {size:,} bytes')


def write_files(data, name):
    json_path = DOCS_DATA / f'{name}.json'
    js_path = DOCS_DATA / f'{name}.js'

    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    json_path.write_text(json_str, encoding='utf-8')

    # Capitalize variable name for JS
    var_name = name.upper() + '_DATA'
    js_str = f'window.{var_name} = {json_str};'
    js_path.write_text(js_str, encoding='utf-8')

    print(f'  {name}.json: {len(json_str):,} chars | {name}.js: {len(js_str):,} chars')


def build_graph(citations, by_doc):
    all_topics = sorted(set(c['topic'] for c in citations))
    topic_to_id = {}
    nodes = []
    links = []

    nodes.append({
        'id': 'central',
        'label': 'Estado del Arte: Mercado del Huevo',
        'type': 'central',
        'size': 50,
        'color': '#3b82f6',
    })

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
            'color': '#64748b',
        })
        links.append({'source': 'central', 'target': tid, 'sourceType': 'central', 'targetType': 'topic'})

    quality_colors = {'alta': '#22c55e', 'media': '#eab308', 'baja': '#f97316'}
    for fname, clist in by_doc.items():
        doc_id = 'doc_' + re.sub(r'[^a-zA-Z0-9_]', '_', fname[:60])
        name = clean_name(fname)
        qdist = Counter(c.get('quality_level', 'baja') for c in clist)
        pq = qdist.most_common(1)[0][0]
        node_size = 12 + min(len(clist) * 2, 40)

        nodes.append({
            'id': doc_id,
            'label': name,
            'type': 'doc',
            'count': len(clist),
            'size': node_size,
            'color': quality_colors.get(pq, '#94a3b8'),
            'primary_quality': pq,
            'quality_dist': {'alta': qdist.get('alta', 0), 'media': qdist.get('media', 0), 'baja': qdist.get('baja', 0)},
            'topics': [t for t, _ in Counter(c['topic'] for c in clist).most_common(3)],
        })

        # Connect doc to its topics
        doc_topics = set(c['topic'] for c in clist)
        for t in doc_topics:
            tid = topic_to_id.get(t)
            if tid:
                links.append({
                    'source': doc_id, 'target': tid,
                    'sourceType': 'doc', 'targetType': 'topic',
                })

    return {'nodes': nodes, 'links': links}


if __name__ == '__main__':
    generate_all()
