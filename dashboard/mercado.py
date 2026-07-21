"""Datos del mercado avicola colombiano.

Carga y visualiza datos del sector: precios, consumo, produccion,
elasticidades, series mensuales, etc. Los datos provienen de
fuentes externas (FENAVI, DANE, etc.).
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import numpy as np
import re


RUTA_DATOS = Path(__file__).parent.parent / 'Datos en general.csv'
RUTA_CONSUMO = Path(__file__).parent / 'data' / 'consumo_huevo.csv'
RUTA_PRODUCCION = Path(__file__).parent / 'data' / 'produccion_huevo.csv'


@st.cache_data
def cargar_consumo() -> pd.DataFrame:
    return pd.read_csv(RUTA_CONSUMO)


@st.cache_data
def cargar_produccion() -> pd.DataFrame:
    return pd.read_csv(RUTA_PRODUCCION)


@st.cache_data
def cargar_datos_generales() -> dict:
    """Carga las distintas secciones del archivo Datos en general.csv.

    Returns:
        dict con DataFrames: 'anual', 'elasticidades', 'mensual', 'consumo_carne'
    """
    if not RUTA_DATOS.exists():
        return {}

    # El archivo tiene BOM UTF-8 (EF BB BF)
    try:
        with open(RUTA_DATOS, 'r', encoding='utf-8-sig') as f:
            lineas = f.readlines()
    except UnicodeDecodeError:
        try:
            with open(RUTA_DATOS, 'r', encoding='cp1252') as f:
                lineas = f.readlines()
        except UnicodeDecodeError:
            return {}

    resultados = {}

    # --- Seccion 1: Datos anuales (lineas 1-8) ---
    headers_raw = lineas[0].strip().split(';')
    data_rows = []
    for i in range(1, 8):
        if i < len(lineas) and lineas[i].strip():
            vals = lineas[i].strip().split(';')
            data_rows.append(vals)

    df_anual = pd.DataFrame(data_rows, columns=headers_raw)

    for col in df_anual.columns:
        df_anual[col] = df_anual[col].apply(_parsear_numero)

    resultados['anual'] = df_anual

    # --- Seccion 2: Elasticidades (linea 10 = header, 11-17 = datos) ---
    # Formato: tres bloques de elasticidades separados por ;;
    try:
        header_line = lineas[9].strip().split(';')
        elasticidad_rows = []
        for i in range(10, 17):
            if i < len(lineas):
                vals = lineas[i].strip().split(';')
                elasticidad_rows.append(vals)

        df_elasticidad = pd.DataFrame(elasticidad_rows)

        # Cada 3 columnas es un bloque: ΔQ, ΔP, Elasticidad
        bloques = ['huevo_precio', 'cerdo_cruzada', 'ingreso']
        for b_idx, bloque in enumerate(bloques):
            start = b_idx * 4
            sub = df_elasticidad.iloc[:, start:start + 3].copy()
            sub.columns = ['variacion_q', 'variacion_p', 'elasticidad']
            sub['tipo'] = bloque
            sub['anio'] = sub.index.map(lambda i: [2019, 2020, 2021, 2022, 2023, 2024][i] if i < 6 else None)
            sub['variacion_q'] = sub['variacion_q'].apply(_parsear_numero)
            sub['variacion_p'] = sub['variacion_p'].apply(_parsear_numero)
            sub['elasticidad'] = sub['elasticidad'].apply(_parsear_numero)
            resultados[f'elasticidad_{bloque}'] = sub

        # Promedios en fila 7 (indice 16 en 0-based = linea 17)
        # Formato: ε_promedio;;;-0,13;;ψ_promedio;;;-1,15;;η_promedio;;;0,56;;
        promedios = elasticidad_rows[6] if len(elasticidad_rows) > 6 else []
        resultados['elasticidad_promedio'] = {
            'huevo_precio': _parsear_numero(promedios[3]) if len(promedios) > 3 else None,
            'cerdo_cruzada': _parsear_numero(promedios[8]) if len(promedios) > 8 else None,
            'ingreso': _parsear_numero(promedios[13]) if len(promedios) > 13 else None,
        }
    except Exception:
        pass

    # --- Seccion 3: Precios mensuales (lineas 32-44) ---
    try:
        mes_header = lineas[30].strip().split(';')
        years = [x for x in mes_header if x and x != 'Mes']
        meses_data = []

        for i in range(31, 43):
            vals = lineas[i].strip().split(';')
            mes = vals[0].strip()
            precios_mes = vals[1:1 + len(years)]
            for j, p in enumerate(precios_mes):
                if p and p.strip():
                    meses_data.append({
                        'mes': mes,
                        'anio': int(years[j]),
                        'precio': _parsear_numero(p.strip()),
                    })

        resultados['mensual'] = pd.DataFrame(meses_data)
    except Exception:
        pass

    # --- Seccion 4: Consumo de carne de pollo (lineas 53-68) ---
    try:
        kg_header = lineas[51].strip().split(';')
        kg_data = []
        for i in range(52, 68):
            vals = lineas[i].strip().split(';')
            if vals[0] and vals[0].strip() and vals[0].strip() != 'Año':
                anio_str = vals[0].strip()
                kg_val = _parsear_numero(vals[1].strip()) if len(vals) > 1 and vals[1].strip() else None
                if kg_val is not None:
                    kg_data.append({'anio': anio_str, 'kg_hab': kg_val})

        resultados['consumo_carne'] = pd.DataFrame(kg_data)
    except Exception:
        pass

    return resultados


def _parsear_numero(valor):
    """Convierte string con coma decimal y puntos de miles a float."""
    if valor is None:
        return None
    valor = str(valor).strip().replace(' ', '')
    if not valor or valor in ('', '-', ';', 'N/A'):
        return None

    # Quitar puntos de miles (ej: 781.242,00 -> 781242,00)
    # Primero detectar si hay coma decimal
    if ',' in valor:
        valor = valor.replace('.', '')  # quita miles
        valor = valor.replace(',', '.')  # coma -> punto decimal
    elif '.' in valor:
        # Podria ser miles o decimal. Asumimos miles si hay 3+ digitos despues
        parts = valor.split('.')
        if len(parts[-1]) == 3 and len(parts) > 1:
            valor = valor.replace('.', '')  # es miles
        # si no, ya esta en formato decimal con punto

    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


def grafico_precios(df_anual: pd.DataFrame) -> go.Figure:
    """Precio del huevo nominal y real."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_anual['Año'], y=df_anual['P_huevo(COP/unid)'],
        mode='lines+markers', name='Precio Nominal',
        line=dict(width=3, color='#d62728'),
        marker=dict(size=8),
    ))

    if 'Pr_huevo' in df_anual.columns:
        fig.add_trace(go.Scatter(
            x=df_anual['Año'], y=df_anual['Pr_huevo'],
            mode='lines+markers', name='Precio Real (base 2018)',
            line=dict(width=2, dash='dash', color='#ff7f0e'),
            marker=dict(size=6),
        ))

    fig.update_layout(
        title='Precio del Huevo - Nominal vs Real',
        xaxis_title='Año',
        yaxis_title='COP por unidad',
        hovermode='x unified',
        template='plotly_white',
        height=400,
    )
    fig.update_yaxes(tickformat='$,.0f')
    return fig


def grafico_produccion_consumo(df_anual: pd.DataFrame,
                                df_prod: pd.DataFrame,
                                df_cons: pd.DataFrame) -> go.Figure:
    """Produccion y consumo de huevo."""
    fig = go.Figure()

    if 'Prod_huevo(millones)' in df_anual.columns:
        fig.add_trace(go.Bar(
            x=df_anual['Año'],
            y=df_anual['Prod_huevo(millones)'],
            name='Produccion (millones)',
            marker_color='#2ca02c',
            opacity=0.7,
        ))

    fig.add_trace(go.Scatter(
        x=df_cons['anio'], y=df_cons['consumo_per_capita'],
        mode='lines+markers', name='Consumo per capita',
        line=dict(width=3, color='#1f77b4'),
        marker=dict(size=8),
        yaxis='y2',
    ))

    fig.update_layout(
        title='Produccion y Consumo de Huevo en Colombia',
        xaxis_title='Año',
        yaxis=dict(title='Produccion (millones de unidades)'),
        yaxis2=dict(
            title='Consumo per capita (unidades/año)',
            overlaying='y', side='right',
        ),
        hovermode='x unified',
        template='plotly_white',
        height=400,
        legend=dict(x=0, y=1.1, orientation='h'),
    )
    return fig


def grafico_comparacion_precios(df_anual: pd.DataFrame) -> go.Figure:
    """Comparacion de precios: huevo vs cerdo vs maiz."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_anual['Año'], y=df_anual['P_huevo(COP/unid)'],
        mode='lines+markers', name='Huevo (COP/unid)',
        line=dict(width=2),
    ))

    if 'P_Cerdo(COP/Kg)' in df_anual.columns:
        fig.add_trace(go.Scatter(
            x=df_anual['Año'], y=df_anual['P_Cerdo(COP/Kg)'],
            mode='lines+markers', name='Cerdo (COP/Kg)',
            line=dict(width=2, dash='dash'),
            yaxis='y2',
        ))

    if 'Precio_Maíz(Kg)' in df_anual.columns:
        fig.add_trace(go.Scatter(
            x=df_anual['Año'], y=df_anual['Precio_Maíz(Kg)'],
            mode='lines+markers', name='Maiz (COP/Kg)',
            line=dict(width=2, dash='dot'),
            yaxis='y3',
        ))

    fig.update_layout(
        title='Comparacion de Precios del Sector',
        xaxis_title='Año',
        yaxis=dict(title='Huevo (COP/unid)', color='#1f77b4'),
        yaxis2=dict(
            title='Cerdo (COP/Kg)', overlaying='y', side='right',
            color='#ff7f0e', anchor='x',
        ),
        hovermode='x unified',
        template='plotly_white',
        height=400,
        legend=dict(x=0, y=1.1, orientation='h'),
    )
    return fig


def grafico_salario_minimo(df_anual: pd.DataFrame) -> go.Figure:
    """Salario minimo nominal y real."""
    fig = go.Figure()

    if 'Sal_min(nom)' in df_anual.columns:
        fig.add_trace(go.Scatter(
            x=df_anual['Año'], y=df_anual['Sal_min(nom)'],
            mode='lines+markers', name='Salario Minimo Nominal',
            line=dict(width=3, color='#9467bd'),
            marker=dict(size=8),
        ))

    if 'Sal_min(Real)' in df_anual.columns:
        fig.add_trace(go.Scatter(
            x=df_anual['Año'], y=df_anual['Sal_min(Real)'],
            mode='lines+markers', name='Salario Minimo Real',
            line=dict(width=2, dash='dash', color='#8c564b'),
            marker=dict(size=6),
        ))

    fig.update_layout(
        title='Salario Minimo en Colombia',
        xaxis_title='Año',
        yaxis_title='COP',
        hovermode='x unified',
        template='plotly_white',
        height=400,
    )
    fig.update_yaxes(tickformat='$,.0f')
    return fig


def grafico_elasticidades(resultados: dict) -> go.Figure:
    """Elasticidades precio, cruzada e ingreso."""
    fig = go.Figure()
    colores = {'huevo_precio': '#d62728', 'cerdo_cruzada': '#ff7f0e', 'ingreso': '#2ca02c'}
    nombres = {'huevo_precio': 'Precio Propia (ε)', 'cerdo_cruzada': 'Cruzada Cerdo (ψ)', 'ingreso': 'Ingreso (η)'}

    for bloque in ['huevo_precio', 'cerdo_cruzada', 'ingreso']:
        key = f'elasticidad_{bloque}'
        if key in resultados:
            df = resultados[key]
            fig.add_trace(go.Scatter(
                x=df['anio'], y=df['elasticidad'],
                mode='lines+markers', name=nombres[bloque],
                line=dict(width=2, color=colores[bloque]),
                marker=dict(size=8),
            ))

    # Linea de referencia en 0
    fig.add_hline(y=0, line_dash='dot', line_color='gray', opacity=0.5)

    fig.update_layout(
        title='Elasticidades del Mercado de Huevo',
        xaxis_title='Año',
        yaxis_title='Elasticidad',
        hovermode='x unified',
        template='plotly_white',
        height=400,
    )
    return fig


def grafico_mensual(df_mensual: pd.DataFrame) -> go.Figure:
    """Precios mensuales del huevo por año."""
    import plotly.colors as clrs
    fig = go.Figure()

    colores = clrs.qualitative.Plotly
    for i, anio in enumerate(sorted(df_mensual['anio'].unique())):
        df_anio = df_mensual[df_mensual['anio'] == anio].sort_values('mes')
        fig.add_trace(go.Scatter(
            x=df_anio['mes'], y=df_anio['precio'],
            mode='lines+markers', name=str(anio),
            line=dict(width=2, color=colores[i % len(colores)]),
            marker=dict(size=6),
        ))

    fig.update_layout(
        title='Precio Mensual del Huevo por Año',
        xaxis_title='Mes',
        yaxis_title='COP por unidad',
        hovermode='x unified',
        template='plotly_white',
        height=400,
    )
    fig.update_yaxes(tickformat='$,.0f')
    return fig


def grafico_consumo_carne(df_carne: pd.DataFrame) -> go.Figure:
    """Consumo historico de carne de pollo per capita."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_carne['anio'], y=df_carne['kg_hab'],
        mode='lines+markers', name='Consumo pollo (Kg/hab)',
        line=dict(width=3, color='#ff7f0e'),
        marker=dict(size=8),
        fill='tozeroy', fillcolor='rgba(255,127,14,0.1)',
    ))

    fig.update_layout(
        title='Consumo de Carne de Pollo per capita en Colombia',
        xaxis_title='Año',
        yaxis_title='Kg por persona al año',
        hovermode='x unified',
        template='plotly_white',
        height=400,
    )
    return fig


def mostrar_pagina_mercado(df_cons_financiero=None):
    """Pagina de datos del mercado avicola.

    Args:
        df_cons_financiero: DataFrame del consolidado financiero (opcional)
                            para correlacionar datos de mercado con datos contables.
    """
    st.header("Datos del Mercado Avicola")
    st.markdown("Indicadores del sector: precios, consumo, produccion y elasticidades.")

    consumos = cargar_consumo()
    produccion = cargar_produccion()
    datos = cargar_datos_generales()

    if not datos:
        st.warning("No se encontraron los datos de mercado en el archivo Datos en general.csv")
        return

    df_anual = datos.get('anual')

    tab_precios, tab_prod_cons, tab_elas, tab_mensual, tab_carne = st.tabs([
        "💰 Precios", "📦 Produccion y Consumo", "📐 Elasticidades",
        "📅 Mensual", "🍗 Consumo Carne"
    ])

    with tab_precios:
        if df_anual is not None and not df_anual.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(grafico_precios(df_anual), use_container_width=True)
            with col2:
                st.plotly_chart(grafico_comparacion_precios(df_anual), use_container_width=True)

            st.plotly_chart(grafico_salario_minimo(df_anual), use_container_width=True)

            st.subheader("Datos de Precios y Salarios")
            cols_mostrar = ['Año', 'P_huevo(COP/unid)', 'Pr_huevo',
                           'P_Cerdo(COP/Kg)', 'Precio_Maíz(Kg)',
                           'Sal_min(nom)', 'Sal_min(Real)', 'IPC']
            cols_exist = [c for c in cols_mostrar if c in df_anual.columns]
            st.dataframe(
                df_anual[cols_exist].style.format({
                    c: '${:,.0f}' for c in cols_exist if c != 'Año' and c != 'IPC'
                }),
                use_container_width=True, hide_index=True,
            )
        else:
            st.warning("No hay datos anuales disponibles.")

    with tab_prod_cons:
        col1, col2 = st.columns([2, 1])

        with col1:
            fig_pc = grafico_produccion_consumo(df_anual, produccion, consumos)
            st.plotly_chart(fig_pc, use_container_width=True)

        with col2:
            st.subheader("Resumen de Consumo")
            ult = consumos.iloc[-1]
            prom = consumos['consumo_per_capita'].mean()
            st.metric("Consumo 2025", f"{ult['consumo_per_capita']} unid/pers")
            st.metric("Promedio periodo", f"{prom:.0f} unid/pers")
            st.metric("Produccion 2025",
                      f"{produccion[produccion['anio']==2025]['produccion_millones'].iloc[0]:,.0f}M")

            st.subheader("Datos de Consumo")
            st.dataframe(consumos, use_container_width=True, hide_index=True)

            st.subheader("Datos de Produccion")
            st.dataframe(produccion, use_container_width=True, hide_index=True)

    with tab_elas:
        col1, col2 = st.columns([2, 1])

        with col1:
            fig_elas = grafico_elasticidades(datos)
            st.plotly_chart(fig_elas, use_container_width=True)

        with col2:
            st.subheader("Elasticidades Promedio")
            ep = datos.get('elasticidad_promedio', {})
            for nombre, key in [('Precio Propia (ε)', 'huevo_precio'),
                                 ('Cruzada Cerdo (ψ)', 'cerdo_cruzada'),
                                 ('Ingreso (η)', 'ingreso')]:
                val = ep.get(key)
                if val is not None:
                    tipo = "inelastica" if abs(val) < 1 else ("elastica" if abs(val) > 1 else "unitaria")
                    st.metric(nombre, f"{val:.2f}", help=f"Demanda {tipo}")

            st.markdown("---")
            st.markdown("""
            **Interpretacion:**
            - **ε (precio propia)**: ε=-0.13 → demanda inelastica.
              Un aumento de 1% en el precio reduce el consumo 0.13%.
            - **ψ (cruzada cerdo)**: ψ=-1.15 → bienes complementarios.
            - **η (ingreso)**: η=0.56 → bien normal. Al aumentar el
              ingreso 1%, el consumo de huevo aumenta 0.56%.
            """)

    with tab_mensual:
        df_mensual = datos.get('mensual')
        if df_mensual is not None and not df_mensual.empty:
            fig_mensual = grafico_mensual(df_mensual)
            st.plotly_chart(fig_mensual, use_container_width=True)

            meses_orden = ['Ene','Feb','Mar','Abr','May','Jun',
                          'Jul','Ago','Sep','Oct','Nov','Dic']
            df_pivot = df_mensual.pivot_table(
                index='mes', columns='anio', values='precio',
                aggfunc='first'
            )
            df_pivot = df_pivot.reindex(meses_orden)
            st.dataframe(
                df_pivot.style.format('${:,.0f}'),
                use_container_width=True,
            )
        else:
            st.info("No hay datos mensuales disponibles.")

    with tab_carne:
        df_carne = datos.get('consumo_carne')
        if df_carne is not None and not df_carne.empty:
            fig_carne = grafico_consumo_carne(df_carne)
            st.plotly_chart(fig_carne, use_container_width=True)

            st.dataframe(df_carne, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos de consumo de carne disponibles.")
