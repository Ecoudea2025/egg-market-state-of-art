"""Modelo de Cournot: Incubadora Santander vs Resto del Mercado Agregado.

Calibrado con datos reales del consolidado financiero y precios de mercado.
Demanda lineal P = a - bQ calibrada con elasticidad precio.
Costos asimetricos estimados de los estados financieros.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from ..base import ModeloEconomico

RUTA_CONSOLIDADO = Path(__file__).parent.parent.parent / 'data' / 'consolidado_limpio.csv'
RUTA_MERCADO = Path(__file__).parent.parent.parent.parent / 'Datos en general.csv'


class CournotIncubadora(ModeloEconomico):
    EMPRESA_FOCO = 'INCUBADORA SANTANDER S.A'

    def __init__(self):
        self._anio = 2023
        self._elasticidad = -0.13
        self._data_cache = None

    @property
    def nombre(self):
        return "Cournot: Incubadora Santander vs Resto"

    @property
    def descripcion(self):
        return (
            "Duopolio de Cournot calibrado con datos reales. "
            "Incubadora Santander compite por cantidades contra el "
            "resto del mercado (14 empresas agregadas). La demanda "
            "se calibra con la elasticidad precio del sector."
        )

    @property
    def parametros(self):
        params = {
            'anio': {
                'valor': self._anio, 'min': 2018, 'max': 2024, 'step': 1,
                'descripcion': 'Año de calibracion'
            },
            'elasticidad_precio': {
                'valor': self._elasticidad, 'min': -2.0, 'max': -0.01, 'step': 0.01,
                'descripcion': 'Elasticidad precio de la demanda (ε)'
            },
        }
        try:
            data = self._cargar_datos()
            params['demanda_intercepto'] = {
                'valor': data['a'], 'min': data['a']*0.5, 'max': data['a']*2,
                'step': data['a']*0.05, 'descripcion': 'Intercepto de demanda (calibrado)'
            }
            params['demanda_pendiente'] = {
                'valor': data['b'], 'min': 0, 'max': float(data['b']*10),
                'step': float(data['b']*0.1), 'descripcion': 'Pendiente de demanda (calibrado)'
            }
            params['costo_marginal'] = {
                'valor': (data['c_inc'] + data['c_resto']) / 2,
                'min': 0, 'max': 1, 'step': 0.01,
                'descripcion': 'Costo marginal medio (calibrado)'
            }
        except Exception:
            pass
        return params

    def actualizar_parametros(self, **kwargs):
        for k in ['demanda_intercepto', 'demanda_pendiente', 'costo_marginal']:
            kwargs.pop(k, None)
        if 'anio' in kwargs:
            self._anio = int(kwargs['anio'])
            self._data_cache = None
        if 'elasticidad_precio' in kwargs:
            self._elasticidad = kwargs['elasticidad_precio']
            self._data_cache = None

    def _cargar_datos(self):
        if self._data_cache is not None:
            return self._data_cache

        df = pd.read_csv(RUTA_CONSOLIDADO)

        def obtener_firma(empresa, anio):
            r = df[(df['empresa'] == empresa) & (df['anio_fiscal'] == anio)]
            if r.empty:
                return None
            r = r.iloc[0]
            return {
                'ingresos': r['ingresos_actividades_ordinarias'],
                'costo_ventas': r['costo_ventas'],
            }

        inc = obtener_firma(self.EMPRESA_FOCO, self._anio)
        if inc is None:
            raise ValueError(f"No hay datos de {self.EMPRESA_FOCO} para {self._anio}")

        rest = df[(df['empresa'] != self.EMPRESA_FOCO) & (df['anio_fiscal'] == self._anio)]
        if rest.empty:
            raise ValueError(f"No hay datos del resto del mercado para {self._anio}")

        ingresos_resto = rest['ingresos_actividades_ordinarias'].sum()
        costo_resto = rest['costo_ventas'].sum()

        ing_inc = inc['ingresos']
        cost_inc = inc['costo_ventas']

        Q_total = ing_inc + ingresos_resto

        data = {
            'anio': self._anio,
            'ingreso_inc': ing_inc,
            'costo_inc': cost_inc,
            'ingreso_resto': ingresos_resto,
            'costo_resto': costo_resto,
            'q_total': Q_total,
            'share_inc': ing_inc / Q_total,
            'share_resto': ingresos_resto / Q_total,
            'margen_inc': (ing_inc - cost_inc) / ing_inc,
            'margen_resto': (ingresos_resto - costo_resto) / ingresos_resto,
            'ganancia_inc_real': ing_inc - cost_inc,
            'ganancia_resto_real': ingresos_resto - costo_resto,
            'ganancia_total_real': (ing_inc - cost_inc) + (ingresos_resto - costo_resto),
        }

        # Costos marginales normalizados (P=1 en el equilibrio observado)
        # Con P=1, c_i = costo_ventas_i / ingresos_i
        # (fraccion del ingreso que es costo)
        data['c_inc'] = cost_inc / ing_inc if ing_inc > 0 else 0
        data['c_resto'] = costo_resto / ingresos_resto if ingresos_resto > 0 else 0

        # Calibracion de demanda P = a - bQ
        # Dada elasticidad ε = -0.13 en el equilibrio observado:
        # ε = -1/b * P/Q
        # Con P=1 (normalizado): ε = -1/(b*Q)
        # b = -1/(ε*Q)
        # a = P + bQ = 1 + bQ
        b = -1.0 / (self._elasticidad * Q_total)
        a = 1.0 + b * Q_total

        data['a'] = a
        data['b'] = b

        self._data_cache = data
        return data

    def calcular_equilibrio(self):
        data = self._cargar_datos()
        a, b = data['a'], data['b']
        c1, c2 = data['c_inc'], data['c_resto']

        # Equilibrio Nash-Cournot duopolio asimetrico
        # q1 = (a - 2c1 + c2) / (3b)
        # q2 = (a - 2c2 + c1) / (3b)
        q1_eq = max((a - 2 * c1 + c2) / (3 * b), 0)
        q2_eq = max((a - 2 * c2 + c1) / (3 * b), 0)
        Q_eq = q1_eq + q2_eq
        P_eq = max(a - b * Q_eq, 0)

        pi1 = max((P_eq - c1) * q1_eq, 0)
        pi2 = max((P_eq - c2) * q2_eq, 0)
        pi_total = pi1 + pi2

        share1_eq = q1_eq / Q_eq if Q_eq > 0 else 0
        share2_eq = q2_eq / Q_eq if Q_eq > 0 else 0

        # Valores observados (reales)
        q_inc_real = data['ingreso_inc']  # en unidades monetarias
        q_resto_real = data['ingreso_resto']
        Q_real = data['q_total']
        share_inc_real = data['share_inc']
        margen_inc_real = data['margen_inc']
        margen_resto_real = data['margen_resto']

        # Diferencia entre Cournot y realidad
        dif_q1 = (q1_eq - q_inc_real) / q_inc_real * 100 if q_inc_real > 0 else 0
        dif_q2 = (q2_eq - q_resto_real) / q_resto_real * 100 if q_resto_real > 0 else 0
        dif_Q = (Q_eq - Q_real) / Q_real * 100 if Q_real > 0 else 0
        dif_P = (P_eq - 1.0) * 100  # P real normalizado a 1

        # Excedente del consumidor y Lerner
        if P_eq > 0:
            excedente_consumidor = 0.5 * (a - P_eq) * Q_eq if a > P_eq else 0
            lerner = (P_eq - c1) / P_eq
        else:
            excedente_consumidor = 0
            lerner = 0

        eq = {
            'modelo': 'Cournot (Incubadora vs Resto)',
            'anio': data['anio'],
            # Keys compatibles con visualizacion generica
            'precio': P_eq,
            'cantidad_total': Q_eq,
            'excedente_consumidor': excedente_consumidor,
            'indice_lerner': lerner,
            # Equilibrio Nash-Cournot
            'precio_eq': P_eq,
            'cantidad_total_eq': Q_eq,
            'cantidad_inc': q1_eq,
            'cantidad_resto': q2_eq,
            'ganancia_inc': pi1,
            'ganancia_resto': pi2,
            'ganancia_total': pi_total,
            'share_inc_eq': share1_eq,
            'share_resto_eq': share2_eq,
            # Valores reales observados
            'precio_real': 1.0,
            'cantidad_total_real': Q_real,
            'cantidad_inc_real': q_inc_real,
            'cantidad_resto_real': q_resto_real,
            'share_inc_real': share_inc_real,
            'share_resto_real': 1 - share_inc_real,
            'ganancia_inc_real': data['ganancia_inc_real'],
            'ganancia_resto_real': data['ganancia_resto_real'],
            'ganancia_total_real': data['ganancia_total_real'],
            'margen_inc_real': margen_inc_real,
            'margen_resto_real': margen_resto_real,
            # Diferencias
            'dif_cantidad_inc_pct': dif_q1,
            'dif_cantidad_resto_pct': dif_q2,
            'dif_cantidad_total_pct': dif_Q,
            'dif_precio_pct': dif_P,
            # Parametros de demanda
            'demanda_a': a,
            'demanda_b': b,
            'elasticidad': self._elasticidad,
            'costo_inc': c1,
            'costo_resto': c2,
        }
        return eq

    def _get_share2(self, data):
        return 1 - data['share_inc']

    def simular(self, periodos=50):
        data = self._cargar_datos()
        a, b = data['a'], data['b']
        c1, c2 = data['c_inc'], data['c_resto']

        q_hist = np.zeros((periodos + 1, 2))
        q_hist[0] = [data['share_inc'] * data['q_total'] * 0.8,
                     data['share_resto'] * data['q_total'] * 0.8]

        for t in range(1, periodos + 1):
            q_prev = q_hist[t - 1]
            # Best response: q_i = (a - c_i - b*q_j) / (2*b)
            q1_br = max((a - c1 - b * q_prev[1]) / (2 * b), 0)
            q2_br = max((a - c2 - b * q_prev[0]) / (2 * b), 0)
            q_hist[t] = [q1_br, q2_br]

        df = pd.DataFrame(q_hist, columns=['inc_cantidad', 'resto_cantidad'])
        df['periodo'] = range(periodos + 1)
        df['q_total'] = df['inc_cantidad'] + df['resto_cantidad']
        df['precio'] = df['q_total'].apply(lambda q: max(a - b * q, 0))
        df['inc_ganancia'] = (df['precio'] - c1) * df['inc_cantidad']
        df['resto_ganancia'] = (df['precio'] - c2) * df['resto_cantidad']
        df['inc_share'] = df['inc_cantidad'] / df['q_total'].replace(0, np.nan)
        return df

    def graficar(self):
        eq = self.calcular_equilibrio()
        data = self._cargar_datos()
        sim = self.simular(40)

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Convergencia a Equilibrio Nash-Cournot',
                'Funciones de Reaccion',
                'Real vs Cournot',
                f'Distribucion del Mercado {data["anio"]}'
            ),
            specs=[[{}, {}],
                   [{'secondary_y': True}, {'type': 'bar'}]],
            vertical_spacing=0.15,
            horizontal_spacing=0.12,
        )

        # Grafico 1: Convergencia
        fig.add_trace(
            go.Scatter(x=sim['periodo'], y=sim['inc_cantidad'],
                       mode='lines', name='Incubadora Santander',
                       line=dict(width=2, color='#1f77b4')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=sim['periodo'], y=sim['resto_cantidad'],
                       mode='lines', name='Resto del Mercado',
                       line=dict(width=2, color='#d62728')),
            row=1, col=1
        )

        q_eq = eq['cantidad_inc']
        fig.add_hline(y=q_eq, line_dash='dash', line_color='#1f77b4',
                      annotation_text=f"Eq Inc: {q_eq:,.0f}M",
                      row=1, col=1)
        q_resto_eq = eq['cantidad_resto']
        fig.add_hline(y=q_resto_eq, line_dash='dash', line_color='#d62728',
                      annotation_text=f"Eq Resto: {q_resto_eq:,.0f}M",
                      row=1, col=1)

        # Grafico 2: Funciones de reaccion
        c1, c2 = data['c_inc'], data['c_resto']
        a, b = data['a'], data['b']

        q_max = a / b * 1.2
        q_grid = np.linspace(0, q_max, 100)

        br1 = np.maximum((a - c1 - b * q_grid) / (2 * b), 0)
        br2 = np.maximum((a - c2 - b * q_grid) / (2 * b), 0)

        fig.add_trace(
            go.Scatter(x=q_grid, y=br1, mode='lines',
                       name='BR Incubadora',
                       line=dict(color='#1f77b4', dash='dash')),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=br2, y=q_grid, mode='lines',
                       name='BR Resto',
                       line=dict(color='#d62728', dash='dash')),
            row=1, col=2
        )

        q1_star = eq['cantidad_inc']
        q2_star = eq['cantidad_resto']
        fig.add_trace(
            go.Scatter(x=[q1_star], y=[q2_star], mode='markers',
                       name=f'Equilibrio Nash ({q1_star:,.0f}, {q2_star:,.0f})',
                       marker=dict(size=14, color='green', symbol='star')),
            row=1, col=2
        )

        # Punto real
        q1_real = eq['cantidad_inc_real']
        q2_real = eq['cantidad_resto_real']
        fig.add_trace(
            go.Scatter(x=[q1_real], y=[q2_real], mode='markers',
                       name=f'Real ({q1_real:,.0f}, {q2_real:,.0f})',
                       marker=dict(size=12, color='orange', symbol='x')),
            row=1, col=2
        )

        fig.update_xaxes(title_text='q Incubadora', row=1, col=2)
        fig.update_yaxes(title_text='q Resto', row=1, col=2)

        # Grafico 3: Real vs Cournot
        escenarios = ['Real', 'Cournot', 'Monopolio', 'Competencia\nPerfecta']

        # Real
        q_r = eq['cantidad_total_real']
        p_r = 1.0
        pi_r = eq['ganancia_total_real']

        # Cournot
        q_c = eq['cantidad_total_eq']
        p_c = eq['precio_eq']
        pi_c = eq['ganancia_total']

        # Monopolio (multi-producto): Q_m = (a - c_medio) / (2b)
        c_medio = (data['c_inc'] + data['c_resto']) / 2
        q_m = max((a - c_medio) / (2 * b), 0)
        p_m = max(a - b * q_m, 0)
        pi_m = max((p_m - c_medio) * q_m, 0)

        # Competencia perfecta
        p_cp = c_medio
        q_cp = max((a - p_cp) / b, 0)
        pi_cp = 0

        vals_q = [q_r, q_c, q_m, q_cp]
        vals_p = [p_r, p_c, p_m, p_cp]
        vals_pi = [pi_r, pi_c, pi_m, pi_cp]

        fig.add_trace(
            go.Bar(name='Cantidad (M COP)', x=escenarios, y=vals_q,
                   marker_color='lightgreen'),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(name='Precio (indice)', x=escenarios, y=vals_p,
                       mode='lines+markers',
                       marker=dict(size=10, color='royalblue'),
                       line=dict(color='royalblue', width=2)),
            secondary_y=True, row=2, col=1
        )

        fig.update_yaxes(title_text='Cantidad (M COP)', row=2, col=1)
        fig.update_yaxes(title_text='Precio (indice, P=1 real)',
                         secondary_y=True, row=2, col=1)

        # Grafico 4: Distribucion de mercado
        categorias = ['Incubadora\nSantander', 'Resto del\nMercado']
        real_vals = [eq['cantidad_inc_real'], eq['cantidad_resto_real']]
        cournot_vals = [eq['cantidad_inc'], eq['cantidad_resto']]

        fig.add_trace(
            go.Bar(name='Real', x=categorias, y=real_vals,
                   marker_color='orange', opacity=0.8),
            row=2, col=2
        )
        fig.add_trace(
            go.Bar(name='Cournot', x=categorias, y=cournot_vals,
                   marker_color='green', opacity=0.6),
            row=2, col=2
        )

        fig.update_layout(
            title_text=f"Modelo de Cournot Calibrado - {data['anio']}",
            height=750,
            showlegend=True,
            template='plotly_white',
            hovermode='x unified',
            barmode='group',
        )
        fig.update_xaxes(title_text='Periodo', row=1, col=1)
        fig.update_yaxes(title_text='Cantidad (M COP)', row=1, col=1)

        return fig

    def _calcular_ganancia_real(self, data):
        return (1 - data['c_inc']) * data['ingreso_inc'] + (1 - data['c_resto']) * data['ingreso_resto']
