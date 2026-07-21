import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ..base import ModeloEconomico


class Cournot(ModeloEconomico):
    """Modelo de Cournot: competencia por cantidades.

    Las empresas eligen simultáneamente cuánto producir.
    Demanda lineal: P = a - b*Q
    Costo marginal constante: C_i(q_i) = c_i * q_i
    """

    def __init__(self):
        self._a = 100.0
        self._b = 1.0
        self._n_empresas = 2
        self._costos = None
        self._equilibrio_cache = None

    @property
    def nombre(self) -> str:
        return "Cournot"

    @property
    def descripcion(self) -> str:
        return (
            "Las empresas compiten eligiendo cantidades de produccion "
            "simultaneamente. El precio de mercado se determina por "
            "la oferta total. Este modelo es apropiado cuando las "
            "empresas tienen restricciones de capacidad y compiten "
            "en volumen."
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
            'n_empresas': {
                'valor': self._n_empresas, 'min': 2, 'max': 20, 'step': 1,
                'descripcion': 'Numero de empresas en el mercado'
            },
            'costo_marginal': {
                'valor': 10.0, 'min': 0, 'max': 500, 'step': 1,
                'descripcion': 'Costo marginal simetrico (c)'
            },
        }

    def actualizar_parametros(self, **kwargs):
        if 'demanda_intercepto' in kwargs:
            self._a = kwargs['demanda_intercepto']
        if 'demanda_pendiente' in kwargs:
            self._b = kwargs['demanda_pendiente']
        if 'n_empresas' in kwargs:
            self._n_empresas = int(kwargs['n_empresas'])
        if 'costo_marginal' in kwargs:
            c = kwargs['costo_marginal']
            self._costos = np.full(self._n_empresas, c)
        self._equilibrio_cache = None

    def calcular_equilibrio(self) -> dict:
        if self._equilibrio_cache is not None:
            return self._equilibrio_cache

        n = self._n_empresas
        a = self._a
        b = self._b

        if self._costos is None:
            self._costos = np.full(n, 10.0)

        c = self._costos

        # Equilibrio Nash-Cournot
        # q_i = (a - sum(c_j) + n*c_i) / (b*(n+1))
        suma_costos = np.sum(c)
        cantidades = np.array([
            (a - suma_costos + n * c_i) / (b * (n + 1))
            for c_i in c
        ])
        cantidades = np.maximum(cantidades, 0)

        Q_total = np.sum(cantidades)
        precio = max(a - b * Q_total, 0)
        ganancias = np.array([
            (precio - c_i) * q_i
            for c_i, q_i in zip(c, cantidades)
        ])
        ganancias = np.maximum(ganancias, 0)

        # Bienestar
        excedente_consumidor = 0.5 * (a - precio) * Q_total if a > precio else 0
        excedente_productor = np.sum(ganancias)
        bienestar_total = excedente_consumidor + excedente_productor

        # Índice de Lerner implícito
        lerner = (precio - np.mean(c)) / precio if precio > 0 else 0

        eq = {
            'modelo': 'Cournot',
            'n_empresas': n,
            'precio': precio,
            'cantidad_total': Q_total,
            'cantidades_por_empresa': cantidades.tolist(),
            'ganancias_por_empresa': ganancias.tolist(),
            'ganancia_total': np.sum(ganancias),
            'excedente_consumidor': excedente_consumidor,
            'excedente_productor': excedente_productor,
            'bienestar_total': bienestar_total,
            'indice_lerner': lerner,
        }
        self._equilibrio_cache = eq
        return eq

    def simular(self, periodos: int = 50) -> pd.DataFrame:
        n = self._n_empresas
        a = self._a
        b = self._b
        c = self._costos if self._costos is not None else np.full(n, 10.0)

        # Simulación de best-response dynamics
        q_hist = np.zeros((periodos + 1, n))
        q_hist[0] = np.random.uniform(1, 5, n)

        for t in range(1, periodos + 1):
            q_prev = q_hist[t - 1]
            for i in range(n):
                q_otros = np.sum(q_prev) - q_prev[i]
                # Best response: q_i = (a - c_i - b*q_otros) / (2*b)
                q_br = (a - c[i] - b * q_otros) / (2 * b)
                q_hist[t, i] = max(q_br, 0)

        # Construir DataFrame
        data = []
        for t in range(periodos + 1):
            q_t = q_hist[t]
            Q_t = np.sum(q_t)
            p_t = max(a - b * Q_t, 0)
            row = {'periodo': t, 'precio': p_t, 'cantidad_total': Q_t}
            for i in range(n):
                row[f'empresa_{i+1}_cantidad'] = q_t[i]
                row[f'empresa_{i+1}_ganancia'] = max((p_t - c[i]) * q_t[i], 0)
            data.append(row)

        return pd.DataFrame(data)

    def graficar(self) -> go.Figure:
        eq = self.calcular_equilibrio()
        n = self._n_empresas
        a = self._a
        b = self._b
        c = self._costos

        sim = self.simular(30)

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Convergencia a Equilibrio',
                'Funciones de Reaccion (Duopolio)',
                'Comparacion de Escenarios',
                'Distribucion de Ganancias'
            ),
            specs=[[{'secondary_y': False}, {'secondary_y': False}],
                   [{'type': 'bar'}, {'type': 'bar'}]],
            vertical_spacing=0.15,
            horizontal_spacing=0.12
        )

        # Gráfico 1: Convergencia
        for i in range(min(n, 5)):
            col = f'empresa_{i+1}_cantidad'
            fig.add_trace(
                go.Scatter(x=sim['periodo'], y=sim[col],
                           mode='lines', name=f'Empresa {i+1}',
                           line=dict(width=2)),
                row=1, col=1
            )

        # Línea de equilibrio teórico
        if n >= 2:
            q_eq = eq['cantidades_por_empresa'][0]
            fig.add_hline(y=q_eq, line_dash="dash", line_color="gray",
                          annotation_text=f"Eq: {q_eq:.2f}",
                          row=1, col=1)

        # Gráfico 2: Funciones de reacción (solo para duopolio)
        if n == 2:
            q_max = a / b
            q_grid = np.linspace(0, q_max, 100)

            # BR1(q2) = (a - c1 - b*q2) / (2*b)
            br1 = np.maximum((a - c[0] - b * q_grid) / (2 * b), 0)
            # BR2(q1) = (a - c2 - b*q1) / (2*b)
            br2 = np.maximum((a - c[1] - b * q_grid) / (2 * b), 0)

            fig.add_trace(
                go.Scatter(x=q_grid, y=br1, mode='lines',
                           name='BR Empresa 1',
                           line=dict(color='blue', dash='dash')),
                row=1, col=2
            )
            fig.add_trace(
                go.Scatter(x=br2, y=q_grid, mode='lines',
                           name='BR Empresa 2',
                           line=dict(color='red', dash='dash')),
                row=1, col=2
            )

            # Punto de equilibrio
            q1_eq = eq['cantidades_por_empresa'][0]
            q2_eq = eq['cantidades_por_empresa'][1]
            fig.add_trace(
                go.Scatter(x=[q1_eq], y=[q2_eq], mode='markers',
                           name=f'Equilibrio ({q1_eq:.1f}, {q2_eq:.1f})',
                           marker=dict(size=12, color='green',
                                       symbol='star')),
                row=1, col=2
            )

            fig.update_xaxes(title_text="q Empresa 1", row=1, col=2)
            fig.update_yaxes(title_text="q Empresa 2", row=1, col=2)

        # Gráfico 3: Comparación de escenarios (barra)
        escenarios = ['Cournot']
        precios = [eq['precio']]
        cantidades = [eq['cantidad_total']]
        ganancias_totales = [eq['ganancia_total']]

        # Monopolio
        c_medio = np.mean(c)
        q_m = (a - c_medio) / (2 * b) if a > c_medio else 0
        p_m = a - b * q_m
        escenarios.extend(['Monopolio'])
        precios.append(max(p_m, 0))
        cantidades.append(max(q_m, 0))
        ganancias_totales.append(max((p_m - c_medio) * q_m, 0))

        # Competencia perfecta
        p_cp = c_medio
        q_cp = (a - p_cp) / b if a > p_cp else 0
        escenarios.extend(['Competencia Perfecta'])
        precios.append(p_cp)
        cantidades.append(max(q_cp, 0))
        ganancias_totales.append(0)

        fig.add_trace(
            go.Bar(name='Precio', x=escenarios, y=precios,
                   marker_color='royalblue'),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(name='Cantidad', x=escenarios, y=cantidades,
                   marker_color='lightgreen'),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(name='Ganancia Total', x=escenarios, y=ganancias_totales,
                   marker_color='coral'),
            row=2, col=1
        )

        # Gráfico 4: Ganancias por empresa
        empresas_labels = [f'Empresa {i+1}' for i in range(n)]
        fig.add_trace(
            go.Bar(x=empresas_labels,
                   y=eq['ganancias_por_empresa'],
                   marker_color='gold',
                   text=[f"${g:,.0f}" for g in eq['ganancias_por_empresa']],
                   textposition='auto'),
            row=2, col=2
        )

        fig.update_layout(
            title_text=f"Modelo de Cournot - {n} empresas",
            height=700,
            showlegend=True,
            template='plotly_white',
            hovermode='x unified'
        )
        fig.update_xaxes(title_text="Periodo", row=1, col=1)
        fig.update_yaxes(title_text="Cantidad", row=1, col=1)

        return fig
