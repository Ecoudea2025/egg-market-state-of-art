"""Dashboard Financiero - Sector Avicola Colombia
Plataforma de investigacion en microeconomia.

Arquitectura modular que permite agregar nuevas secciones sin
modificar el codigo existente. Cada seccion vive en su propio
modulo y se registra en SECCIONES.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

from comparacion import mostrar_pagina_comparacion
from simulacion import mostrar_pagina_simulacion
from ingesta import mostrar_pagina_ingesta
from mercado import mostrar_pagina_mercado

RUTA_CONSOLIDADO = Path('data') / 'consolidado_limpio.csv'
RUTA_EMPRESAS = Path('data') / 'empresas'
RUTA_METRICAS = Path('data') / 'metricas_sector.csv'

NOMBRES_INDICADORES = {
    'ingresos_actividades_ordinarias': 'Ingresos Operacionales',
    'costo_ventas': 'Costo de Ventas',
    'ganancia_bruta': 'Ganancia Bruta',
    'otros_ingresos': 'Otros Ingresos',
    'gastos_ventas': 'Gastos de Ventas',
    'gastos_administracion': 'Gastos de Administracion',
    'otros_gastos': 'Otros Gastos',
    'otras_ganancias_perdidas': 'Otras Ganancias/Perdidas',
    'ganancia_operacion': 'Ganancia Operacional (EBITDA proxy)',
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
    'carga_fiscal_efectiva': 'Carga Fiscal Efectiva (%)'
}

CAMPOS_ABS = [
    'ingresos_actividades_ordinarias', 'costo_ventas', 'ganancia_bruta',
    'otros_ingresos', 'gastos_ventas', 'gastos_administracion',
    'otros_gastos', 'otras_ganancias_perdidas', 'ganancia_operacion',
    'ingresos_financieros', 'costos_financieros', 'ganancia_antes_impuestos',
    'impuestos', 'ganancia_operaciones_continuadas',
    'ganancia_operaciones_discontinuadas', 'ganancia_neta'
]

CAMPOS_RATIOS = [
    'margen_bruto', 'margen_operacional', 'margen_neto',
    'intensidad_gasto_comercial', 'intensidad_gasto_admin',
    'carga_fiscal_efectiva'
]

CATEGORIAS = {
    'Ingresos': ['ingresos_actividades_ordinarias', 'otros_ingresos', 'ingresos_financieros'],
    'Costos y Gastos': ['costo_ventas', 'gastos_ventas', 'gastos_administracion', 'otros_gastos', 'costos_financieros'],
    'Ganancias': ['ganancia_bruta', 'ganancia_operacion', 'ganancia_antes_impuestos', 'ganancia_operaciones_continuadas', 'ganancia_operaciones_discontinuadas', 'ganancia_neta'],
    'Impuestos': ['impuestos'],
    'Ratios': CAMPOS_RATIOS,
    'Otros': ['otras_ganancias_perdidas'],
}

ES_RATIO = set(CAMPOS_RATIOS)

# Registro de secciones del dashboard
# Para agregar una nueva seccion:
# 1. Crear un modulo con una funcion mostrar_pagina_*()
# 2. Agregar tupla (icono, nombre, funcion) a este diccionario
SECCIONES = {
    "📈 Grafico Temporal": "graf",
    "🎯 Comparacion Multi-Empresa": "comp",
    "📊 Tabla de Datos": "tabla",
    "📊 Datos del Mercado": "mercado",
    "🧮 Simulacion Economica": "sim",
    "📥 Gestion de Datos": "data",
    "ℹ️ Acerca de": "info",
}


def formatear_valor(valor, campo):
    if pd.isna(valor):
        return '-'
    if campo in ES_RATIO:
        return f"{valor:.2%}"
    if abs(valor) >= 1_000_000:
        return f"${valor/1_000_000:,.2f}M"
    return f"${valor:,.0f}"


@st.cache_data
def cargar_consolidado():
    return pd.read_csv(RUTA_CONSOLIDADO)


@st.cache_data
def cargar_empresa(empresa):
    ruta = RUTA_EMPRESAS / f"{empresa}.csv"
    if ruta.exists():
        return pd.read_csv(ruta)
    return None


@st.cache_data
def cargar_metricas():
    return pd.read_csv(RUTA_METRICAS)


def graficar_indicador(df_cons, empresa_principal, empresas_comp, campo, anios_rango):
    df_graf = df_cons[df_cons['anio_fiscal'].between(anios_rango[0], anios_rango[1])]

    fig = go.Figure()

    colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    dash_styles = ['solid', 'dash', 'dot', 'dashdot', 'solid']

    # Empresa principal primero
    df_ppal = df_graf[df_graf['empresa'] == empresa_principal].sort_values('anio_fiscal')
    if not df_ppal.empty:
        fig.add_trace(go.Scatter(
            x=df_ppal['anio_fiscal'],
            y=df_ppal[campo],
            mode='lines+markers',
            name=empresa_principal,
            line=dict(width=3, color=colores[0]),
            marker=dict(size=8),
        ))

    # Empresas de comparación
    for i, emp in enumerate(empresas_comp):
        if emp == empresa_principal:
            continue
        color = colores[(i + 1) % len(colores)]
        dash = dash_styles[(i + 1) % len(dash_styles)]
        df_emp = df_graf[df_graf['empresa'] == emp].sort_values('anio_fiscal')
        if not df_emp.empty:
            fig.add_trace(go.Scatter(
                x=df_emp['anio_fiscal'],
                y=df_emp[campo],
                mode='lines+markers',
                name=emp,
                line=dict(width=2, dash=dash, color=color),
                marker=dict(size=6),
            ))

    titulo = f"{NOMBRES_INDICADORES.get(campo, campo)}"
    if campo in ES_RATIO:
        titulo += " (Ratio)"
    else:
        titulo += " (COP)"

    fig.update_layout(
        title=titulo,
        xaxis_title='Año Fiscal',
        yaxis_title=NOMBRES_INDICADORES.get(campo, campo),
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(yanchor="bottom", y=1.02, xanchor="left", x=0)
    )

    if campo in ES_RATIO:
        fig.update_yaxes(tickformat='.0%')
    else:
        fig.update_yaxes(tickformat='$,.0f')

    return fig


def mostrar_tabla_valores(df_cons, empresa, campo, anios_rango):
    df_tab = df_cons[(df_cons['empresa'] == empresa) &
                     (df_cons['anio_fiscal'].between(anios_rango[0], anios_rango[1]))]
    df_tab = df_tab.sort_values('anio_fiscal')

    data = []
    for _, row in df_tab.iterrows():
        anio = int(row['anio_fiscal'])
        valor = row[campo]
        data.append({'Año': anio, 'Valor': valor})

    df_show = pd.DataFrame(data)
    df_show['Año'] = df_show['Año'].astype(int)
    df_show['Valor'] = df_show['Valor'].apply(lambda x: formatear_valor(x, campo))

    if len(df_show) > 1 and not df_show['Valor'].eq('-').all():
        df_show['Var %'] = ''
        for i in range(1, len(df_show)):
            ant = df_tab.iloc[i-1][campo]
            act = df_tab.iloc[i][campo]
            if pd.notna(ant) and pd.notna(act) and ant != 0:
                var = (act - ant) / abs(ant)
                df_show.iloc[i, df_show.columns.get_loc('Var %')] = f"{var:+.2%}"
            else:
                df_show.iloc[i, df_show.columns.get_loc('Var %')] = '-'

    return df_show


def mostrar_tarjetas_resumen(df_cons, empresa, campo, anios_rango):
    df_res = df_cons[(df_cons['empresa'] == empresa) &
                     (df_cons['anio_fiscal'].between(anios_rango[0], anios_rango[1]))]

    valores = df_res[campo].dropna()
    if valores.empty:
        st.info(f"No hay datos disponibles para {empresa} en el rango seleccionado.")
        return

    ultimo = valores.iloc[-1]
    primero = valores.iloc[0]
    crecimiento = ((ultimo - primero) / abs(primero)) * 100 if primero != 0 else 0
    tendencia = "↑" if crecimiento > 0 else ("↓" if crecimiento < 0 else "→")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Promedio", formatear_valor(valores.mean(), campo))
    with col2:
        st.metric("Maximo", formatear_valor(valores.max(), campo))
    with col3:
        st.metric("Minimo", formatear_valor(valores.min(), campo))
    with col4:
        st.metric(f"Crecimiento {tendencia}",
                  f"{crecimiento:+.1f}%",
                  help=f"Variacion del {int(ultimo)} al {int(ultimo)}")


def main():
    st.set_page_config(
        page_title="Dashboard - Sector Avicola",
        page_icon="🥚",
        layout="wide"
    )

    st.title("🥚 Dashboard Financiero - Sector Avicola Colombia")
    st.markdown("*Plataforma de investigacion en microeconomia aplicada*")

    if not RUTA_CONSOLIDADO.exists():
        st.error("""
        Datos no encontrados. Ejecuta primero:
        ```bash
        cd dashboard
        python preparar_datos.py
        ```
        O usa la pestana 'Gestion de Datos' para subir PDFs.
        """)
        st.stop()

    df_cons = cargar_consolidado()
    metricas = cargar_metricas()
    empresas = sorted(df_cons['empresa'].unique())
    anio_min, anio_max = int(df_cons['anio_fiscal'].min()), int(df_cons['anio_fiscal'].max())

    # --- SIDEBAR: Configuracion comun ---
    with st.sidebar:
        st.header("Navegacion")

        seccion_activa = st.radio(
            "Seccion",
            list(SECCIONES.keys()),
            index=0,
            label_visibility="collapsed",
        )

        seccion_key = SECCIONES[seccion_activa]

        # Configuracion segun seccion activa
        if seccion_key in ("graf", "tabla"):
            st.markdown("---")
            st.markdown("### Configuracion")

            empresa_sel = st.selectbox("Empresa", empresas, index=0)

            empresas_comp = st.multiselect(
                "Comparar con",
                [e for e in empresas if e != empresa_sel],
                max_selections=4,
                help="Selecciona empresas adicionales para superponer",
            )

            st.markdown("---")
            st.subheader("Indicador")

            cat_sel = st.selectbox("Categoria", list(CATEGORIAS.keys()), index=0)
            campos_disponibles = CATEGORIAS[cat_sel]
            labels = {c: NOMBRES_INDICADORES.get(c, c) for c in campos_disponibles}
            campo_sel = st.selectbox(
                "Indicador", campos_disponibles,
                format_func=lambda x: labels.get(x, x), index=0
            )

            st.markdown("---")
            anio_rango = st.slider(
                "Rango de Años", min_value=anio_min, max_value=anio_max,
                value=(anio_min, anio_max), step=1
            )

            if seccion_key == "tabla":
                st.markdown("---")
                st.subheader("Metricas del Sector")
                st.dataframe(
                    metricas.style.format({
                        'anio_fiscal': '{:.0f}', 'num_empresas': '{:.0f}',
                        'ingreso_total': '${:,.0f}', 'ihh': '{:.4f}',
                        'lerner_ponderado': '{:.4f}'
                    }),
                    use_container_width=True, hide_index=True
                )

    # --- CONTENIDO PRINCIPAL segun seccion ---
    if seccion_key == "graf":
        col_graf, col_info = st.columns([3, 1])

        with col_graf:
            fig = graficar_indicador(
                df_cons, empresa_sel, empresas_comp, campo_sel, anio_rango
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_info:
            mostrar_tarjetas_resumen(df_cons, empresa_sel, campo_sel, anio_rango)

        if empresas_comp:
            st.markdown("---")
            st.subheader(f"Comparacion: {empresa_sel} vs {', '.join(empresas_comp)}")
            cols = st.columns(len(empresas_comp) + 1)
            with cols[0]:
                mostrar_tarjetas_resumen(df_cons, empresa_sel, campo_sel, anio_rango)
            for i, emp in enumerate(empresas_comp):
                with cols[i + 1]:
                    mostrar_tarjetas_resumen(df_cons, emp, campo_sel, anio_rango)

    elif seccion_key == "comp":
        mostrar_pagina_comparacion(df_cons)

    elif seccion_key == "mercado":
        mostrar_pagina_mercado(df_cons)

    elif seccion_key == "tabla":
        st.subheader(f"{NOMBRES_INDICADORES.get(campo_sel, campo_sel)} - {empresa_sel}")
        df_tabla = mostrar_tabla_valores(df_cons, empresa_sel, campo_sel, anio_rango)
        st.dataframe(df_tabla, use_container_width=True, hide_index=True)

        if empresas_comp:
            st.markdown("---")
            for emp in empresas_comp:
                st.subheader(f"{NOMBRES_INDICADORES.get(campo_sel, campo_sel)} - {emp}")
                df_tabla2 = mostrar_tabla_valores(df_cons, emp, campo_sel, anio_rango)
                st.dataframe(df_tabla2, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("Datos completos")
        st.dataframe(df_cons, use_container_width=True, hide_index=True)

    elif seccion_key == "sim":
        mostrar_pagina_simulacion()

    elif seccion_key == "data":
        mostrar_pagina_ingesta()

    elif seccion_key == "info":
        st.markdown("""
        ### Sobre el Dashboard

        **Fuente de datos:** Superintendencia de Sociedades de Colombia
        **Sector:** Avicola - Huevo (15 empresas)
        **Periodo:** 2015 - 2025
        **Archivos procesados:** 150 PDFs

        **Indicadores disponibles:**
        - **Ingresos:** Ventas totales, otros ingresos, ingresos financieros
        - **Costos y Gastos:** Costo de ventas, gastos operativos
        - **Ganancias:** Bruta, operacional, neta
        - **Ratios:** Margenes, intensidad de gastos, carga fiscal

        **Metricas de Mercado:**
        - **IHH (Herfindahl-Hirschman):** Mide concentracion de mercado
          - < 0.01: Mercado competitivo
          - 0.01 - 0.15: Mercado moderadamente concentrado
          - > 0.15: Mercado altamente concentrado
        - **Lerner Ponderado:** Proxy de poder de mercado

        ### Simulacion Economica
        - **Cournot:** Competencia por cantidades
        - **Bertrand:** Competencia por precios
        - **Stackelberg:** Lider-seguidor

        **Empresas analizadas:**
        """)

        for emp in empresas:
            df_emp = df_cons[df_cons['empresa'] == emp]
            anios = sorted(df_emp['anio_fiscal'].unique())
            ing_prom = df_emp['ingresos_actividades_ordinarias'].mean()
            st.markdown(
                f"- **{emp}**: {len(anios)} años ({min(anios)}-{max(anios)}), "
                f"ingreso prom: ${ing_prom:,.0f}"
            )

        st.markdown("---")
        st.caption(
            "Proyecto desarrollado para extraccion, visualizacion y "
            "simulacion de datos financieros."
        )


if __name__ == '__main__':
    main()
