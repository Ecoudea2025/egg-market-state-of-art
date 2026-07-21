"""Pagina de simulacion economica del dashboard.

Carga dinamicamente modelos economicos desde modelos_economicos/
y los renderiza en Streamlit. Para agregar un nuevo modelo:
1. Crear la clase en modelos_economicos/<area>/
2. Heredar de ModeloEconomico
3. El dashboard lo detectara automaticamente
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from modelos_economicos import Cournot, Bertrand, Stackelberg, CournotIncubadora
from modelos_economicos.base import ModeloEconomico


# Registro de modelos disponibles
# Para agregar un nuevo modelo, importalo y agregalo aqui
MODELOS_DISPONIBLES: dict[str, type[ModeloEconomico]] = {
    'Oligopolio - Cournot': Cournot,
    'Oligopolio - Bertrand': Bertrand,
    'Oligopolio - Stackelberg': Stackelberg,
    '📊 Cournot: Incubadora vs Resto': CournotIncubadora,
}


def _renderizar_parametros(modelo: ModeloEconomico) -> bool:
    """Renderiza los sliders/inputs de parametros en la sidebar.

    Returns:
        True si los parametros cambiaron
    """
    params = modelo.parametros
    cambios = {}

    for nombre, config in params.items():
        v = config['valor']
        mn = config['min']
        mx = config['max']
        stp = config['step']

        # Streamlit exige que value, min_value y max_value sean del mismo tipo
        if isinstance(v, float) or isinstance(mn, float) or isinstance(mx, float):
            v, mn, mx, stp = float(v), float(mn), float(mx), float(stp)
        else:
            v, mn, mx, stp = int(v), int(mn), int(mx), int(stp)

        nuevo_valor = st.slider(
            config['descripcion'],
            min_value=mn, max_value=mx, value=v, step=stp,
            key=f"sim_param_{nombre}_{id(modelo)}",
        )
        if nuevo_valor != config['valor']:
            cambios[nombre] = nuevo_valor

    if cambios:
        modelo.actualizar_parametros(**cambios)
        return True
    return False


def _renderizar_equilibrio(eq: dict):
    """Muestra las metricas clave del equilibrio."""
    if not eq:
        st.warning("No se pudo calcular el equilibrio con los parametros actuales.")
        return

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Precio de Equilibrio",
                  f"${eq.get('precio', 0):,.2f}")

    with col2:
        st.metric("Cantidad Total",
                  f"{eq.get('cantidad_total', 0):,.2f}")

    with col3:
        st.metric("Ganancia Total",
                  f"${eq.get('ganancia_total', 0):,.2f}")

    with col4:
        st.metric("Excedente Consumidor",
                  f"${eq.get('excedente_consumidor', 0):,.2f}")

    with col5:
        lerner = eq.get('indice_lerner', 0)
        st.metric("Indice Lerner",
                  f"{lerner:.4f}",
                  help="Mide poder de mercado (0=CP, 1=monopolio)")


def _renderizar_tabla_comparativa(modelo_actual: ModeloEconomico):
    """Tabla comparativa con otros modelos/escenarios."""
    st.subheader("Comparacion de Escenarios")

    try:
        eq = modelo_actual.calcular_equilibrio()
    except Exception:
        st.error("Error al calcular equilibrio.")
        return

    a = modelo_actual.parametros.get('demanda_intercepto', {}).get('valor', 100)
    b = modelo_actual.parametros.get('demanda_pendiente', {}).get('valor', 1)
    c = modelo_actual.parametros.get('costo_marginal', {}).get('valor', 10)

    filas = []
    etiquetas = []
    precios = []
    cantidades = []
    ganancias = []
    ec = []
    bienestar = []

    # Modelo actual
    etiquetas.append(eq.get('modelo', 'Actual'))
    precios.append(eq.get('precio', 0))
    cantidades.append(eq.get('cantidad_total', 0))
    ganancias.append(eq.get('ganancia_total', 0))
    ec.append(eq.get('excedente_consumidor', 0))
    bienestar.append(eq.get('bienestar_total', 0))

    # Cournot (si no es el actual)
    if 'Cournot' not in eq.get('modelo', ''):
        try:
            c_model = Cournot()
            if hasattr(modelo_actual, '_n_empresas'):
                c_model.actualizar_parametros(
                    demanda_intercepto=a,
                    demanda_pendiente=b,
                    n_empresas=modelo_actual.parametros.get('n_empresas', {}).get('valor', 2),
                    costo_marginal=c,
                )
            elif hasattr(modelo_actual, '_n_seguidores'):
                n_total = 1 + modelo_actual._n_seguidores
                c_model.actualizar_parametros(
                    demanda_intercepto=a,
                    demanda_pendiente=b,
                    n_empresas=n_total,
                    costo_marginal=c,
                )
            eq_c = c_model.calcular_equilibrio()
            etiquetas.append('Cournot')
            precios.append(eq_c['precio'])
            cantidades.append(eq_c['cantidad_total'])
            ganancias.append(eq_c['ganancia_total'])
            ec.append(eq_c['excedente_consumidor'])
            bienestar.append(eq_c['bienestar_total'])
        except Exception:
            pass

    # Competencia Perfecta
    p_cp = c
    q_cp = max((a - p_cp) / b, 0)
    ec_cp = 0.5 * (a - p_cp) * q_cp if a > p_cp else 0
    etiquetas.append('Competencia Perfecta')
    precios.append(p_cp)
    cantidades.append(q_cp)
    ganancias.append(0)
    ec.append(ec_cp)
    bienestar.append(ec_cp)

    # Monopolio
    q_m = max((a - c) / (2 * b), 0)
    p_m = max(a - b * q_m, 0)
    ec_m = 0.5 * (a - p_m) * q_m if a > p_m else 0
    pi_m = max((p_m - c) * q_m, 0)
    etiquetas.append('Monopolio')
    precios.append(p_m)
    cantidades.append(q_m)
    ganancias.append(pi_m)
    ec.append(ec_m)
    bienestar.append(ec_m + pi_m)

    df_comp = pd.DataFrame({
        'Escenario': etiquetas,
        'Precio': precios,
        'Cantidad': cantidades,
        'Ganancia Total': ganancias,
        'Excedente Consumidor': ec,
        'Bienestar Total': bienestar,
    })

    st.dataframe(
        df_comp.style.format({
            'Precio': '${:,.2f}',
            'Cantidad': '{:,.2f}',
            'Ganancia Total': '${:,.2f}',
            'Excedente Consumidor': '${:,.2f}',
            'Bienestar Total': '${:,.2f}',
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Gráfico de comparación
    fig_comp = go.Figure()
    metricas_graf = ['Precio', 'Cantidad', 'Ganancia Total']
    colores = ['royalblue', 'lightgreen', 'coral']

    for i, metrica in enumerate(metricas_graf):
        fig_comp.add_trace(go.Bar(
            name=metrica,
            x=etiquetas,
            y=df_comp[metrica].tolist(),
            marker_color=colores[i],
            yaxis='y' if i == 0 else 'y2',
            offsetgroup=i,
        ))

    fig_comp.update_layout(
        barmode='group',
        title='Comparacion entre Estructuras de Mercado',
        template='plotly_white',
        height=400,
        yaxis=dict(title='Valor'),
    )

    st.plotly_chart(fig_comp, use_container_width=True)


def _renderizar_detalle_empresas(modelo: ModeloEconomico):
    """Muestra detalle de cada empresa."""
    eq = modelo.calcular_equilibrio()
    if not eq:
        return

    cantidades = eq.get('cantidades_por_empresa', [])
    ganancias = eq.get('ganancias_por_empresa', [])

    if not cantidades:
        return

    df_emp = pd.DataFrame({
        'Empresa': [f'Empresa {i+1}' for i in range(len(cantidades))],
        'Cantidad': cantidades,
        'Ganancia': ganancias,
    })

    st.subheader("Detalle por Empresa")
    st.dataframe(
        df_emp.style.format({
            'Cantidad': '{:,.2f}',
            'Ganancia': '${:,.2f}',
        }),
        use_container_width=True,
        hide_index=True,
    )


def _renderizar_colusion(modelo: ModeloEconomico):
    """Analisis de colusion basico."""
    st.subheader("Analisis de Colusion")

    eq = modelo.calcular_equilibrio()
    if not eq:
        return

    ganancia_total = eq.get('ganancia_total', 0)
    n = eq.get('n_empresas', 2)

    # Ganancia de colusión (monopolio repartido)
    a = modelo.parametros.get('demanda_intercepto', {}).get('valor', 100)
    b = modelo.parametros.get('demanda_pendiente', {}).get('valor', 1)
    c = modelo.parametros.get('costo_marginal', {}).get('valor', 10) if 'costo_marginal' in modelo.parametros else \
        modelo.parametros.get('costo_lider', {}).get('valor', 10)

    q_monopolio = max((a - c) / (2 * b), 0)
    p_monopolio = max(a - b * q_monopolio, 0)
    pi_monopolio = max((p_monopolio - c) * q_monopolio, 0)
    pi_colusion = pi_monopolio / n
    pi_competencia = ganancia_total / n if ganancia_total > 0 and n > 0 else 0

    # Factor de descuento crítico para colusión
    # delta* = (pi_desvio - pi_colusion) / (pi_desvio - pi_competencia)
    # pi_desvio ≈ pi_monopolio (si una empresa se desvía y las otras mantienen cuota)
    pi_desvio = pi_monopolio
    if pi_desvio != pi_competencia:
        delta_critico = (pi_desvio - pi_colusion) / (pi_desvio - pi_competencia)
    else:
        delta_critico = 1.0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Ganancia en Colusion (c/u)",
            f"${pi_colusion:,.2f}",
            delta=f"+{(pi_colusion - pi_competencia) / abs(pi_competencia) * 100:.1f}%" if pi_competencia > 0 else "",
            delta_color="inverse" if pi_colusion > pi_competencia else "normal",
        )

    with col2:
        st.metric(
            "Ganancia en Competencia (c/u)",
            f"${pi_competencia:,.2f}"
        )

    with col3:
        st.metric(
            "δ Critico para Colusion",
            f"{delta_critico:.3f}",
            help="Factor de descuento minimo necesario para sostener colusion. "
                 "δ > δ* indica que la colusion es estable."
        )

    st.markdown(f"""
    **Interpretacion:**
    - Si el factor de descuento real **δ > {delta_critico:.3f}**: la colusion es estable
    - Si **δ < {delta_critico:.3f}**: las empresas prefieren desviarse
    - Una **δ* bajo** indica que la colusion es facil de sostener
    """)


def mostrar_pagina_simulacion():
    """Página principal de simulación económica."""
    st.header("Simulacion Economica")
    st.markdown("Explora modelos de teoria microeconomica de forma interactiva.")

    with st.sidebar:
        st.markdown("### ⚙️ Configuracion de Simulacion")

        modelo_nombre = st.selectbox(
            "Modelo Economico",
            list(MODELOS_DISPONIBLES.keys()),
            help="Selecciona el modelo economico a simular"
        )

        modelo_cls = MODELOS_DISPONIBLES[modelo_nombre]

        if 'modelo_sim' not in st.session_state or \
           st.session_state.get('modelo_sim_nombre') != modelo_nombre:
            st.session_state.modelo_sim = modelo_cls()
            st.session_state.modelo_sim_nombre = modelo_nombre

        modelo = st.session_state.modelo_sim

        st.markdown("---")
        st.markdown(f"**{modelo.descripcion}**")

        st.markdown("---")
        st.markdown("**Parametros del Modelo**")
        cambios = _renderizar_parametros(modelo)

    # Área principal
    tab_eq, tab_graf, tab_comp, tab_col, tab_info = st.tabs([
        "📊 Equilibrio",
        "📈 Grafico",
        "📋 Comparacion",
        "🤝 Colusion",
        "ℹ️ Informacion",
    ])

    with tab_eq:
        try:
            eq = modelo.calcular_equilibrio()
            _renderizar_equilibrio(eq)
            st.markdown("---")
            _renderizar_detalle_empresas(modelo)
        except Exception as e:
            st.error(f"Error al calcular equilibrio: {e}")

    with tab_graf:
        try:
            fig = modelo.graficar()
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error al generar grafico: {e}")

    with tab_comp:
        _renderizar_tabla_comparativa(modelo)

    with tab_col:
        try:
            _renderizar_colusion(modelo)
        except Exception as e:
            st.error(f"Error en analisis de colusion: {e}")

    with tab_info:
        st.markdown(f"""
        ### {modelo.nombre}

        **Descripcion:**
        {modelo.descripcion}

        **Parametros disponibles:**
        """)
        for nombre, config in modelo.parametros.items():
            st.markdown(f"- **{nombre}**: {config['descripcion']} "
                       f"(rango: {config['min']} - {config['max']}, "
                       f"actual: {config['valor']})")

        st.markdown("""
        **Como agregar nuevos modelos:**
        1. Crea un archivo en `modelos_economicos/<area>/`
        2. Hereda de `ModeloEconomico` e implementa sus metodos
        3. Importalo en `simulacion.py` y agrega al diccionario `MODELOS_DISPONIBLES`
        """)
