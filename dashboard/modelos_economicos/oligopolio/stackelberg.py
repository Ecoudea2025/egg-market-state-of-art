import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ..base import ModeloEconomico


class Stackelberg(ModeloEconomico):
    """Modelo de Stackelberg: lider-seguidor.

    El líder elige su cantidad primero. El seguidor observa la
    decisión del líder y luego elige su cantidad óptima.
    El líder anticipa la respuesta del seguidor (backward induction).
    """

    def __init__(self):
        self._a = 100.0
        self._b = 1.0
        self._costo_lider = 8.0
        self._costo_seguidor = 10.0
        self._n_seguidores = 1

    @property
    def nombre(self) -> str:
        return "Stackelberg"

    @property
    def descripcion(self) -> str:
        return (
            "Una empresa lider elige su produccion primero. Las empresas "
            "seguidoras observan la decision del lider y luego eligen "
            "su cantidad optima. El lider anticipa esta respuesta, lo "
            "que le da una ventaja estrategica (first-mover advantage)."
        )

    @property
    def parametros(self) -> dict:
        return {
            'demanda_intercepto': {
                'valor': self._a, 'min': 10, 'max': 1000, 'step': 10,
                'descripcion': 'Intercepto de la demanda (a en P = a - bQ)'
            },
            'demanda_pendiente': {
                'valor': self._b, 'min': 0.1, 'max': 10, 'step': 0.1,
                'descripcion': 'Pendiente de la demanda (b en P = a - bQ)'
            },
            'costo_lider': {
                'valor': self._costo_lider, 'min': 0, 'max': 500, 'step': 1,
                'descripcion': 'Costo marginal del lider'
            },
            'costo_seguidor': {
                'valor': self._costo_seguidor, 'min': 0, 'max': 500, 'step': 1,
                'descripcion': 'Costo marginal del seguidor'
            },
            'n_seguidores': {
                'valor': self._n_seguidores, 'min': 1, 'max': 10, 'step': 1,
                'descripcion': 'Numero de empresas seguidoras'
            },
        }

    def actualizar_parametros(self, **kwargs):
        if 'demanda_intercepto' in kwargs:
            self._a = kwargs['demanda_intercepto']
        if 'demanda_pendiente' in kwargs:
            self._b = kwargs['demanda_pendiente']
        if 'costo_lider' in kwargs:
            self._costo_lider = kwargs['costo_lider']
        if 'costo_seguidor' in kwargs:
            self._costo_seguidor = kwargs['costo_seguidor']
        if 'n_seguidores' in kwargs:
            self._n_seguidores = int(kwargs['n_seguidores'])
        self._equilibrio_cache = None

    def calcular_equilibrio(self) -> dict:
        a = self._a
        b = self._b
        c_l = self._costo_lider
        c_s = self._costo_seguidor
        m = self._n_seguidores  # número de seguidores

        if c_l >= a or c_s >= a:
            return {
                'modelo': 'Stackelberg',
                'n_empresas': 1 + m,
                'precio': 0,
                'cantidad_total': 0,
                'cantidades_por_empresa': [0] * (1 + m),
                'ganancias_por_empresa': [0] * (1 + m),
                'ganancia_total': 0,
                'excedente_consumidor': 0,
                'excedente_productor': 0,
                'bienestar_total': 0,
                'indice_lerner': 0,
                'ventaja_primer_actor': 0,
            }

        # Backward induction:
        # 1. Dado q_l, el seguidor maximiza: max q_s*(a - b*(q_l + q_s)) - c_s*q_s
        #    BR_seguidor(q_l) = (a - c_s - b*q_l) / (2*b)
        # 2. El líder anticipa: q_s(q_l) = (a - c_s - b*q_l) / (2*b)
        #    Lider maximiza: q_l*(a - b*(q_l + q_s(q_l))) - c_l*q_l
        #    q_l* = (a - 2*c_l + c_s) / (2*b)
        # 3. Con m seguidores simétricos:
        #    BR_seguidor(q_l) = (a - c_s - b*q_l) / (b*(m+1))
        #    q_l* = (a + m*c_s - (m+1)*c_l) / (2*b)

        q_lider = (a + m * c_s - (m + 1) * c_l) / (2 * b)
        q_lider = max(q_lider, 0)

        # Cada seguidor produce
        q_seguidor = max((a - c_s - b * q_lider) / (b * (m + 1)), 0)

        cantidades = [q_lider] + [q_seguidor] * m
        Q_total = np.sum(cantidades)
        precio = max(a - b * Q_total, 0)

        # Ganancias
        ganancia_lider = max((precio - c_l) * q_lider, 0)
        ganancias_seguidores = [max((precio - c_s) * q_seguidor, 0)] * m
        ganancias = [ganancia_lider] + ganancias_seguidores
        ganancia_total = np.sum(ganancias)

        # Bienestar
        excedente_consumidor = 0.5 * (a - precio) * Q_total if a > precio else 0
        excedente_productor = ganancia_total
        bienestar_total = excedente_consumidor + excedente_productor

        lerner = (precio - (c_l + m * c_s) / (m + 1)) / precio if precio > 0 else 0

        # Ventaja del primer actor (comparación con Cournot simétrico)
        q_cournot_lider = (a - 2 * c_l + c_s) / (3 * b) if a > c_l and a > c_s else 0
        ventaja = (q_lider - q_cournot_lider) if q_cournot_lider > 0 else 0

        return {
            'modelo': 'Stackelberg',
            'n_empresas': 1 + m,
            'precio': precio,
            'cantidad_total': Q_total,
            'cantidad_lider': q_lider,
            'cantidad_seguidor': q_seguidor,
            'cantidades_por_empresa': cantidades,
            'ganancia_lider': ganancia_lider,
            'ganancia_seguidor': ganancias_seguidores[0] if m > 0 else 0,
            'ganancias_por_empresa': ganancias,
            'ganancia_total': ganancia_total,
            'excedente_consumidor': excedente_consumidor,
            'excedente_productor': excedente_productor,
            'bienestar_total': bienestar_total,
            'indice_lerner': lerner,
            'ventaja_primer_actor': ventaja,
        }

    def simular(self, periodos: int = 30) -> pd.DataFrame:
        a = self._a
        b = self._b
        c_l = self._costo_lider
        c_s = self._costo_seguidor
        m = self._n_seguidores

        # Simulación secuencial: líder mueve primero, seguidor responde
        data = []
        q_l_hist = np.linspace(0, max(a / b, 1), periodos)

        for t, q_l in enumerate(q_l_hist):
            q_s = max((a - c_s - b * q_l) / (b * (m + 1)), 0)
            Q_t = q_l + m * q_s
            p_t = max(a - b * Q_t, 0)

            row = {
                'periodo': t,
                'cantidad_lider': q_l,
                'cantidad_seguidor': q_s,
                'cantidad_total': Q_t,
                'precio': p_t,
                'ganancia_lider': max((p_t - c_l) * q_l, 0),
                'ganancia_seguidor': max((p_t - c_s) * q_s, 0),
            }
            data.append(row)

        return pd.DataFrame(data)

    def graficar(self) -> go.Figure:
        eq = self.calcular_equilibrio()
        m = self._n_seguidores

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Funcion de Reaccion del Seguidor',
                'Espacio de Estrategias',
                'Comparacion Cournot vs Stackelberg',
                'Distribucion de Ganancias'
            ),
            specs=[[{}, {}],
                   [{'type': 'bar'}, {'type': 'bar'}]],
            vertical_spacing=0.15,
            horizontal_spacing=0.12
        )

        # Gráfico 1: Función de reacción del seguidor
        q_l_range = np.linspace(0, self._a / self._b, 100)
        q_s_br = np.maximum(
            (self._a - self._costo_seguidor - self._b * q_l_range) /
            (self._b * (m + 1)), 0
        )

        fig.add_trace(
            go.Scatter(x=q_l_range, y=q_s_br, mode='lines',
                       name='BR Seguidor',
                       line=dict(color='red', dash='dash', width=3)),
            row=1, col=1
        )

        # Punto de equilibrio
        fig.add_trace(
            go.Scatter(x=[eq['cantidad_lider']], y=[eq['cantidad_seguidor']],
                       mode='markers',
                       name=f"Eq: L={eq['cantidad_lider']:.1f}, S={eq['cantidad_seguidor']:.1f}",
                       marker=dict(size=14, color='green', symbol='star')),
            row=1, col=1
        )

        fig.update_xaxes(title_text="q Lider", row=1, col=1)
        fig.update_yaxes(title_text="q Seguidor", row=1, col=1)

        # Gráfico 2: Espacio de estrategias
        q_max = self._a / self._b
        q_grid = np.linspace(0, q_max, 50)

        # Isoganancias del líder para distintos q_l, q_s
        z_l = np.zeros((len(q_grid), len(q_grid)))
        for i, ql in enumerate(q_grid):
            for j, qs in enumerate(q_grid):
                p = max(self._a - self._b * (ql + m * qs), 0)
                z_l[i, j] = max((p - self._costo_lider) * ql, 0)

        fig.add_trace(
            go.Contour(z=z_l, x=q_grid, y=q_grid,
                       colorscale='Viridis', opacity=0.6,
                       name='Ganancia Lider', showscale=False),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=[eq['cantidad_lider']], y=[eq['cantidad_seguidor']],
                       mode='markers',
                       marker=dict(size=12, color='red', symbol='x'),
                       name='Equilibrio'),
            row=1, col=2
        )
        fig.update_xaxes(title_text="q Lider", row=1, col=2)
        fig.update_yaxes(title_text="q Seguidor", row=1, col=2)

        # Gráfico 3: Comparación Cournot vs Stackelberg
        a, b = self._a, self._b
        c_l, c_s = self._costo_lider, self._costo_seguidor

        escenarios = ['Stackelberg\nLider', 'Stackelberg\nSeguidor']

        # Cournot equivalente
        if c_l == c_s:
            c = c_l
            q_c = max((a - c) / (b * (2 + m)), 0) if a > c else 0
            escenarios.extend(['Cournot\nAmbos', 'Monopolio', 'CP'])
            q_cournot = [q_c, q_c]
        else:
            q_c_l = max((a - 2 * c_l + c_s) / (3 * b), 0)
            q_c_s = max((a - 2 * c_s + c_l) / (3 * b), 0)
            escenarios.extend(['Cournot\nLider', 'Cournot\nSeguidor', 'Monopolio', 'CP'])
            q_cournot = [q_c_l, q_c_s]

        q_stackelberg = [eq['cantidad_lider'], eq['cantidad_seguidor']]

        fig.add_trace(
            go.Bar(name='Stackelberg', x=escenarios[:2], y=q_stackelberg,
                   marker_color='steelblue'),
            row=2, col=1
        )

        if len(escenarios) >= 4:
            fig.add_trace(
                go.Bar(name='Cournot', x=escenarios[2:4],
                       y=q_cournot if len(q_cournot) == 2 else q_cournot[:2],
                       marker_color='coral'),
                row=2, col=1
            )

        # Monopolio y CP
        c_medio = (c_l + m * c_s) / (m + 1)
        q_m = max((a - c_medio) / (2 * b), 0)
        q_cp = max((a - c_medio) / b, 0)

        fig.add_trace(
            go.Bar(name='Monopolio', x=['Monopolio'], y=[q_m],
                   marker_color='gold'),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(name='CP', x=['CP'], y=[q_cp],
                   marker_color='lightgreen'),
            row=2, col=1
        )

        # Gráfico 4: Ganancias
        labels = ['Lider'] + [f'Seguidor {i+1}' for i in range(m)]
        fig.add_trace(
            go.Bar(x=labels,
                   y=eq['ganancias_por_empresa'],
                   marker_color=['royalblue'] + ['orange'] * m,
                   text=[f"${g:,.0f}" for g in eq['ganancias_por_empresa']],
                   textposition='auto'),
            row=2, col=2
        )

        fig.update_layout(
            title_text=f"Modelo de Stackelberg - 1 Lider, {m} Seguidor(es)",
            height=700,
            showlegend=True,
            template='plotly_white'
        )

        return fig
