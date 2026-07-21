"""Modulo de comparacion multi-empresa.

Vista principal: grafico de lineas temporal con todas las empresas
simultaneamente para un indicador seleccionado.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np


NOMBRES_INDICADORES = {
    'ingresos_actividades_ordinarias': 'Ingresos Operacionales',
    'costo_ventas': 'Costo de Ventas',
    'ganancia_bruta': 'Ganancia Bruta',
    'otros_ingresos': 'Otros Ingresos',
    'gastos_ventas': 'Gastos de Ventas',
    'gastos_administracion': 'Gastos de Administracion',
    'otros_gastos': 'Otros Gastos',
    'otras_ganancias_perdidas': 'Otras Ganancias/Perdidas',
    'ganancia_operacion': 'Ganancia Operacional',
    'ingresos_financieros': 'Ingresos Financieros',
    'costos_financieros': 'Costos Financieros',
    'ganancia_antes_impuestos': 'Ganancia antes de Impuestos',
    'impuestos': 'Impuestos',
    'ganancia_operaciones_continuadas': 'Ganancia Op. Continuadas',
    'ganancia_operaciones_discontinuadas': 'Ganancia Op. Discontinuadas',
    'ganancia_neta': 'Ganancia Neta',
    'margen_bruto': 'Margen Bruto (%)',
    'margen_operacional': 'Margen Operacional (%)',
    'margen_neto': 'Margen Neto (%)',
    'intensidad_gasto_comercial': 'Intensidad Gasto Comercial (%)',
    'intensidad_gasto_admin': 'Intensidad Gasto Administrativo (%)',
    'carga_fiscal_efectiva': 'Carga Fiscal Efectiva (%)',
}

ES_RATIO = {
    'margen_bruto', 'margen_operacional', 'margen_neto',
    'intensidad_gasto_comercial', 'intensidad_gasto_admin',
    'carga_fiscal_efectiva',
}


def _generar_paleta_colores(n: int) -> list[str]:
    """Genera paleta de colores diferenciada para N empresas."""
    import plotly.colors as clrs
    base = clrs.qualitative.Plotly + clrs.qualitative.Set2 + clrs.qualitative.Set1
    return (base * (n // len(base) + 1))[:n]


def grafico_todas_empresas(
    df_cons: pd.DataFrame,
    empresas: list[str],
    campo: str,
    anios_rango: tuple[int, int],
    mostrar_promedio: bool = True,
    mostrar_banda: bool = True,
) -> go.Figure:
    """Grafico de lineas con todas las empresas seleccionadas.

    Args:
        df_cons: DataFrame consolidado
        empresas: Lista de empresas a graficar
        campo: Indicador a visualizar
        anios_rango: (min, max) años
        mostrar_promedio: Agrega linea del promedio simple
        mostrar_banda: Agrega banda de +/-1 desviacion estandar

    Returns:
        Figure de Plotly
    """
    df_filt = df_cons[
        df_cons['anio_fiscal'].between(anios_rango[0], anios_rango[1])
    ].copy()

    fig = go.Figure()

    colores = _generar_paleta_colores(len(empresas))
    dash_styles = ['solid', 'dash', 'dot', 'dashdot', 'longdash']

    for i, emp in enumerate(empresas):
        df_emp = df_filt[df_filt['empresa'] == emp].sort_values('anio_fiscal')
        if df_emp.empty or df_emp[campo].isna().all():
            continue

        fig.add_trace(go.Scatter(
            x=df_emp['anio_fiscal'],
            y=df_emp[campo],
            mode='lines+markers',
            name=emp,
            line=dict(
                width=2,
                color=colores[i],
                dash=dash_styles[i % len(dash_styles)],
            ),
            marker=dict(size=5, symbol='circle'),
            hovertemplate=f"<b>{emp}</b><br>Año: %{{x}}<br>Valor: %{{y:$,.0f}}<extra></extra>"
                          if campo not in ES_RATIO else
                          f"<b>{emp}</b><br>Año: %{{x}}<br>Valor: %{{y:.2%}}<extra></extra>",
        ))

    # Promedio simple entre empresas seleccionadas
    if mostrar_promedio and len(empresas) >= 2:
        df_prom = df_filt[df_filt['empresa'].isin(empresas)]
        df_prom = df_prom.groupby('anio_fiscal')[campo].mean().reset_index()

        fig.add_trace(go.Scatter(
            x=df_prom['anio_fiscal'],
            y=df_prom[campo],
            mode='lines',
            name='Promedio',
            line=dict(width=3, color='black', dash='dot'),
            marker=dict(size=0),
        ))

        # Banda de desviacion estandar
        if mostrar_banda:
            df_banda = df_filt[df_filt['empresa'].isin(empresas)]
            df_banda = df_banda.groupby('anio_fiscal')[campo].agg(
                ['mean', 'std']
            ).reset_index()
            df_banda = df_banda.dropna()

            fig.add_trace(go.Scatter(
                x=pd.concat([df_banda['anio_fiscal'], df_banda['anio_fiscal'][::-1]]),
                y=pd.concat([
                    df_banda['mean'] + df_banda['std'],
                    (df_banda['mean'] - df_banda['std'])[::-1],
                ]),
                fill='toself',
                fillcolor='rgba(128,128,128,0.15)',
                line=dict(color='rgba(255,255,255,0)'),
                name='±1 Desv. Est.',
                hoverinfo='skip',
                showlegend=True,
            ))

    titulo = f"{NOMBRES_INDICADORES.get(campo, campo)} - Todas las Empresas"
    titulo += " (Ratio)" if campo in ES_RATIO else " (COP)"

    fig.update_layout(
        title=titulo,
        xaxis_title='Año Fiscal',
        yaxis_title=NOMBRES_INDICADORES.get(campo, campo),
        hovermode='x unified',
        template='plotly_white',
        height=550,
        legend=dict(
            yanchor="bottom", y=1.02, xanchor="left", x=0,
            orientation="h", font=dict(size=10),
        ),
        margin=dict(t=80),
    )

    if campo in ES_RATIO:
        fig.update_yaxes(tickformat='.0%')
    else:
        fig.update_yaxes(tickformat='$,.0f')

    return fig


def mostrar_tabla_comparativa(
    df_cons: pd.DataFrame,
    empresas: list[str],
    campo: str,
    anio: int,
) -> pd.DataFrame:
    """Tabla ranking de empresas para un indicador en un año especifico."""
    df_filt = df_cons[
        (df_cons['empresa'].isin(empresas)) &
        (df_cons['anio_fiscal'] == anio)
    ].copy()

    df_filt = df_filt.dropna(subset=[campo])
    df_filt = df_filt.sort_values(campo, ascending=False)
    df_filt['Ranking'] = range(1, len(df_filt) + 1)

    result = df_filt[['Ranking', 'empresa', campo]].reset_index(drop=True)
    return result


def mostrar_tabla_evolucion(
    df_cons: pd.DataFrame,
    empresas: list[str],
    campo: str,
    anios_rango: tuple[int, int],
) -> pd.DataFrame:
    """Tabla de evolucion interanual del indicador por empresa."""
    df_filt = df_cons[
        (df_cons['empresa'].isin(empresas)) &
        (df_cons['anio_fiscal'].between(anios_rango[0], anios_rango[1]))
    ].copy()

    # Pivot: empresas en filas, años en columnas
    df_pivot = df_filt.pivot_table(
        index='empresa',
        columns='anio_fiscal',
        values=campo,
        aggfunc='first',
    )

    # Reordenar años ascendentemente
    df_pivot = df_pivot[sorted(df_pivot.columns)]

    # Agregar crecimiento total
    if len(df_pivot.columns) >= 2:
        primero = df_pivot.iloc[:, 0]
        ultimo = df_pivot.iloc[:, -1]
        df_pivot['Crecimiento Total'] = np.where(
            primero != 0,
            (ultimo - primero) / primero.abs(),
            np.nan,
        )

    return df_pivot


def mostrar_pagina_comparacion(df_cons: pd.DataFrame):
    """Pagina de comparacion multi-empresa."""
    st.header("Comparacion Multi-Empresa")
    st.markdown("Visualiza la evolucion temporal de todas las empresas simultaneamente.")

    empresas = sorted(df_cons['empresa'].unique())
    anio_min = int(df_cons['anio_fiscal'].min())
    anio_max = int(df_cons['anio_fiscal'].max())

    with st.sidebar:
        st.markdown("### 🏢 Comparacion Global")

        # Selector de empresas: todas seleccionadas por defecto
        todas_seleccionadas = st.checkbox("Todas las empresas", value=True)
        if todas_seleccionadas:
            empresas_sel = empresas
        else:
            empresas_sel = st.multiselect(
                "Empresas",
                empresas,
                default=empresas[:5],
                help="Selecciona empresas para comparar",
            )

        if not empresas_sel:
            st.warning("Selecciona al menos una empresa.")
            st.stop()

        st.markdown("---")
        st.markdown("**Indicador**")

        # Categorias (reutilizando la logica de app.py)
        CATEGORIAS = {
            'Ingresos': ['ingresos_actividades_ordinarias', 'otros_ingresos', 'ingresos_financieros'],
            'Costos y Gastos': ['costo_ventas', 'gastos_ventas', 'gastos_administracion', 'otros_gastos', 'costos_financieros'],
            'Ganancias': ['ganancia_bruta', 'ganancia_operacion', 'ganancia_antes_impuestos', 'ganancia_operaciones_continuadas', 'ganancia_operaciones_discontinuadas', 'ganancia_neta'],
            'Impuestos': ['impuestos'],
            'Ratios': ['margen_bruto', 'margen_operacional', 'margen_neto', 'intensidad_gasto_comercial', 'intensidad_gasto_admin', 'carga_fiscal_efectiva'],
            'Otros': ['otras_ganancias_perdidas'],
        }

        cat_sel = st.selectbox("Categoria", list(CATEGORIAS.keys()), index=0)
        campos_disp = CATEGORIAS[cat_sel]
        labels = {c: NOMBRES_INDICADORES.get(c, c) for c in campos_disp}
        campo_sel = st.selectbox(
            "Indicador", campos_disp,
            format_func=lambda x: labels.get(x, x), index=0
        )

        st.markdown("---")
        anio_rango = st.slider(
            "Rango de Años",
            min_value=anio_min, max_value=anio_max,
            value=(anio_min, anio_max), step=1,
        )

        st.markdown("---")
        st.markdown("**Opciones de visualizacion**")
        mostrar_prom = st.checkbox("Mostrar promedio", value=True)
        mostrar_banda = st.checkbox("Mostrar banda ±1σ", value=True)

    # --- AREA PRINCIPAL ---
    tab_graf, tab_evol, tab_ranking = st.tabs([
        "📈 Lineas Temporales", "📋 Evolucion por Año", "🏆 Ranking por Año"
    ])

    with tab_graf:
        fig = grafico_todas_empresas(
            df_cons, empresas_sel, campo_sel,
            anio_rango, mostrar_prom, mostrar_banda,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tarjetas de resumen debajo del grafico
        df_resumen = df_cons[
            (df_cons['empresa'].isin(empresas_sel)) &
            (df_cons['anio_fiscal'].between(anio_rango[0], anio_rango[1]))
        ]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Promedio del periodo",
                f"${df_resumen[campo_sel].mean():,.0f}" if campo_sel not in ES_RATIO
                else f"{df_resumen[campo_sel].mean():.2%}",
            )
        with col2:
            mejor_emp = df_resumen.groupby('empresa')[campo_sel].mean().idxmax()
            st.metric("Mejor promedio", mejor_emp[:20] + "..." if len(mejor_emp) > 20 else mejor_emp)
        with col3:
            crecimiento = (
                df_resumen.groupby('empresa')[campo_sel].last() /
                df_resumen.groupby('empresa')[campo_sel].first() - 1
            )
            mayor_crec = crecimiento.idxmax()
            st.metric("Mayor crecimiento", f"{crecimiento.max():+.1%}" if pd.notna(crecimiento.max()) else "N/A")
        with col4:
            equidad = df_resumen.groupby('anio_fiscal')[campo_sel].std().mean()
            st.metric("Dispersion media", f"${equidad:,.0f}" if campo_sel not in ES_RATIO else f"{equidad:.2%}")

    with tab_evol:
        st.subheader(f"Evolucion de {NOMBRES_INDICADORES.get(campo_sel, campo_sel)}")

        if len(empresas_sel) <= 20:
            df_evol = mostrar_tabla_evolucion(df_cons, empresas_sel, campo_sel, anio_rango)
            if not df_evol.empty:
                st.dataframe(
                    df_evol.style.format(
                        lambda x: f"{x:,.0f}" if pd.notna(x) and campo_sel not in ES_RATIO
                        else (f"{x:.2%}" if pd.notna(x) else "-"),
                        na_rep="-",
                    ),
                    use_container_width=True,
                )
            else:
                st.info("No hay datos suficientes para mostrar la evolucion.")
        else:
            st.info("Selecciona menos empresas para ver la tabla detallada.")

    with tab_ranking:
        anio_rank = st.selectbox(
            "Año para ranking",
            options=list(range(anio_rango[0], anio_rango[1] + 1)),
            index=anio_rango[1] - anio_rango[0],
        )

        df_rank = mostrar_tabla_comparativa(df_cons, empresas_sel, campo_sel, anio_rank)
        if not df_rank.empty:
            st.subheader(
                f"Ranking {NOMBRES_INDICADORES.get(campo_sel, campo_sel)} - {anio_rank}"
            )

            col_rank, col_detalle = st.columns([1, 2])
            with col_rank:
                st.dataframe(
                    df_rank.style.format({
                        campo_sel: lambda x: f"${x:,.0f}" if campo_sel not in ES_RATIO
                        else f"{x:.2%}",
                    }),
                    use_container_width=True,
                    hide_index=True,
                )
            with col_detalle:
                # Grafico de barras del ranking
                fig_bar = go.Figure()
                df_rank_sorted = df_rank.sort_values(campo_sel, ascending=True)

                fig_bar.add_trace(go.Bar(
                    y=df_rank_sorted['empresa'],
                    x=df_rank_sorted[campo_sel],
                    orientation='h',
                    marker_color=['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf'][:len(df_rank_sorted)],
                    text=[f"${v:,.0f}" if campo_sel not in ES_RATIO else f"{v:.2%}"
                          for v in df_rank_sorted[campo_sel]],
                    textposition='outside',
                ))

                fig_bar.update_layout(
                    title=f"Ranking - {anio_rank}",
                    height=400,
                    template='plotly_white',
                    xaxis_title=NOMBRES_INDICADORES.get(campo_sel, campo_sel),
                    yaxis=dict(autorange="reversed"),
                    margin=dict(l=10, r=40),
                )

                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos para el ranking en este año.")
