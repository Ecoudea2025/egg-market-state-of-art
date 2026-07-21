import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ..base import ModeloEconomico


class Bertrand(ModeloEconomico):
    """Modelo de Bertrand: competencia por precios.

    Las empresas eligen simultáneamente el precio de su producto.
    Con productos homogéneos, el equilibrio lleva a P = CMg
    (Paradoja de Bertrand). Con productos diferenciados, las
    empresas tienen poder de mercado.
    """

    def __init__(self):
        self._a = 100.0
        self._b = 1.0
        self._diferenciacion = 0.5  # grado de diferenciación (0=homogéneo, 1=muy diferenciado)
        self._n_empresas = 2
        self._costos = None

    @property
    def nombre(self) -> str:
        return "Bertrand"

    @property
    def descripcion(self) -> str:
        return (
            "Las empresas compiten eligiendo precios simultaneamente. "
            "Con productos homogeneos, el precio baja al costo marginal "
            "(Paradoja de Bertrand). Con productos diferenciados, las "
            "empresas pueden cobrar precios mayores y obtener ganancias "
            "positivas."
        )

    @property
    def parametros(self) -> dict:
        return {
            'demanda_intercepto': {
                'valor': self._a, 'min': 10, 'max': 1000, 'step': 10,
                'descripcion': 'Intercepto de la demanda (a)'
            },
            'sensibilidad_precio': {
                'valor': self._b, 'min': 0.1, 'max': 10, 'step': 0.1,
                'descripcion': 'Sensibilidad de la demanda al precio (b)'
            },
            'diferenciacion': {
                'valor': self._diferenciacion, 'min': 0.0, 'max': 1.0, 'step': 0.05,
                'descripcion': 'Grado de diferenciacion (0=homogeneo, 1=altamente diferenciado)'
            },
            'n_empresas': {
                'valor': self._n_empresas, 'min': 2, 'max': 10, 'step': 1,
                'descripcion': 'Numero de empresas'
            },
            'costo_marginal': {
                'valor': 10.0, 'min': 0, 'max': 500, 'step': 1,
                'descripcion': 'Costo marginal simetrico (c)'
            },
        }

    def actualizar_parametros(self, **kwargs):
        if 'demanda_intercepto' in kwargs:
            self._a = kwargs['demanda_intercepto']
        if 'sensibilidad_precio' in kwargs:
            self._b = kwargs['sensibilidad_precio']
        if 'diferenciacion' in kwargs:
            self._diferenciacion = kwargs['diferenciacion']
        if 'n_empresas' in kwargs:
            self._n_empresas = int(kwargs['n_empresas'])
        if 'costo_marginal' in kwargs:
            c = kwargs['costo_marginal']
            self._costos = np.full(self._n_empresas, c)
        self._equilibrio_cache = None

    def calcular_equilibrio(self) -> dict:
        n = self._n_empresas
        a = self._a
        b = self._b
        d = self._diferenciacion  # 0 = homogéneo, 1 = diferenciado
        c = self._costos if self._costos is not None else np.full(n, 10.0)
        c_medio = np.mean(c)

        if d < 0.01:
            # Productos homogéneos: P = MC (Bertrand paradox)
            precio_eq = c_medio
            cantidades = np.array([
                max((a - precio_eq) / (b * n), 0) for _ in range(n)
            ]) if a > precio_eq else np.zeros(n)
        else:
            # Productos diferenciados: modelo lineal simplificado
            # q_i = a - b*p_i + d*b*p_j (para duopolio)
            # Extendido para n empresas
            precio_eq = (a * d + b * c_medio * (1 + d * (n - 1))) / \
                        (d * n + b * (1 + d * (n - 1))) if a > c_medio else c_medio

            if n == 2:
                # Solución exacta duopolio diferenciado
                precio_eq = (a * (1 + d) + b * c_medio * (1 - d)) / \
                            (2 + b * (1 - d)) if a > c_medio else c_medio

            precio_eq = max(precio_eq, c_medio)
            cantidades = np.array([
                max((a - precio_eq + d * precio_eq) / b, 0) for _ in range(n)
            ]) if a > precio_eq else np.zeros(n)

        Q_total = np.sum(cantidades)
        ganancias = np.array([
            (precio_eq - c[i]) * cantidades[i]
            for i in range(n)
        ])
        ganancias = np.maximum(ganancias, 0)

        excedente_consumidor = 0.5 * (a - precio_eq) * Q_total if a > precio_eq else 0
        excedente_productor = np.sum(ganancias)
        bienestar_total = excedente_consumidor + excedente_productor

        lerner = (precio_eq - c_medio) / precio_eq if precio_eq > 0 else 0

        return {
            'modelo': 'Bertrand',
            'n_empresas': n,
            'precio': precio_eq,
            'cantidad_total': Q_total,
            'cantidades_por_empresa': cantidades.tolist(),
            'ganancias_por_empresa': ganancias.tolist(),
            'ganancia_total': np.sum(ganancias),
            'excedente_consumidor': excedente_consumidor,
            'excedente_productor': excedente_productor,
            'bienestar_total': bienestar_total,
            'indice_lerner': lerner,
            'productos_homogeneos': d < 0.01,
            'grado_diferenciacion': d,
        }

    def simular(self, periodos: int = 50) -> pd.DataFrame:
        n = self._n_empresas
        a = self._a
        b = self._b
        d = self._diferenciacion
        c = self._costos if self._costos is not None else np.full(n, 10.0)

        # Simulación de ajuste de precios
        p_hist = np.zeros((periodos + 1, n))
        p_hist[0] = np.random.uniform(20, 50, n)

        for t in range(1, periodos + 1):
            p_prev = p_hist[t - 1]
            for i in range(n):
                if d < 0.01:
                    # Under-cutting en Bertrand homogéneo
                    p_min = min(p_prev)
                    p_br = max(p_min - 0.5, c[i])
                else:
                    # Best response con diferenciación
                    p_prom_otros = (np.sum(p_prev) - p_prev[i]) / (n - 1) if n > 1 else 0
                    p_br = (a + d * b * p_prom_otros + b * c[i]) / (2 * b)
                p_hist[t, i] = max(p_br, c[i])

        data = []
        for t in range(periodos + 1):
            p_t = p_hist[t]
            p_prom = np.mean(p_t)
            q_t = np.array([
                max((a - p_t[i] + d * np.mean([p for j, p in enumerate(p_t) if j != i])) / b, 0)
                for i in range(n)
            ])
            row = {'periodo': t, 'precio_promedio': p_prom, 'cantidad_total': np.sum(q_t)}
            for i in range(n):
                row[f'empresa_{i+1}_precio'] = p_t[i]
                row[f'empresa_{i+1}_ganancia'] = max((p_t[i] - c[i]) * q_t[i], 0)
            data.append(row)

        return pd.DataFrame(data)

    def graficar(self) -> go.Figure:
        eq = self.calcular_equilibrio()
        n = self._n_empresas
        d = self._diferenciacion
        homogeneo = d < 0.01

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Convergencia de Precios',
                'Efecto de la Diferenciacion',
                'Comparacion de Escenarios',
                'Ganancias por Empresa'
            ),
            specs=[[{}, {}],
                   [{'type': 'bar'}, {'type': 'bar'}]],
            vertical_spacing=0.15,
            horizontal_spacing=0.12
        )

        # Gráfico 1: Convergencia
        sim = self.simular(30)
        for i in range(min(n, 5)):
            col = f'empresa_{i+1}_precio'
            fig.add_trace(
                go.Scatter(x=sim['periodo'], y=sim[col],
                           mode='lines', name=f'Empresa {i+1}',
                           line=dict(width=2)),
                row=1, col=1
            )
        fig.add_hline(y=eq['precio'], line_dash="dash", line_color="gray",
                      annotation_text=f"Eq: ${eq['precio']:.2f}",
                      row=1, col=1)
        fig.update_xaxes(title_text="Periodo", row=1, col=1)
        fig.update_yaxes(title_text="Precio", row=1, col=1)

        # Gráfico 2: Efecto de la diferenciación
        d_vals = np.linspace(0, 1, 20)
        p_vals = []
        for dd in d_vals:
            old_d = self._diferenciacion
            self._diferenciacion = dd
            e = self.calcular_equilibrio()
            p_vals.append(e['precio'])
            self._diferenciacion = old_d
        self._equilibrio_cache = None

        fig.add_trace(
            go.Scatter(x=d_vals, y=p_vals, mode='lines+markers',
                       name='Precio equilibrio',
                       line=dict(color='purple', width=3)),
            row=1, col=2
        )
        fig.add_vline(x=eq.get('grado_diferenciacion', d),
                      line_dash="dash", line_color="gray",
                      annotation_text="Actual", row=1, col=2)
        fig.add_hline(y=np.mean(self._costos if self._costos is not None else [10]),
                      line_dash="dot", line_color="red",
                      annotation_text="CMg", row=1, col=2)
        fig.update_xaxes(title_text="Grado de Diferenciacion", row=1, col=2)
        fig.update_yaxes(title_text="Precio de Equilibrio", row=1, col=2)

        # Gráfico 3: Comparación escenarios
        escenarios = ['Bertrand']
        if homogeneo:
            escenarios[0] = 'Bertrand (Homogeneo)'
        else:
            escenarios[0] = f'Bertrand (d={d:.2f})'

        precios = [eq['precio']]
        cantidades = [eq['cantidad_total']]
        ganancias_totales = [eq['ganancia_total']]

        # Competencia perfecta
        c_medio = np.mean(self._costos) if self._costos is not None else 10
        p_cp = c_medio
        q_cp = max((self._a - p_cp) / self._b, 0)
        escenarios.append('Competencia Perfecta')
        precios.append(p_cp)
        cantidades.append(q_cp)
        ganancias_totales.append(0)

        # Monopolio
        q_m = max((self._a - c_medio) / (2 * self._b), 0)
        p_m = max(self._a - self._b * q_m, 0)
        escenarios.append('Monopolio')
        precios.append(p_m)
        cantidades.append(q_m)
        ganancias_totales.append(max((p_m - c_medio) * q_m, 0))

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

        # Gráfico 4: Ganancias
        fig.add_trace(
            go.Bar(x=[f'Empresa {i+1}' for i in range(n)],
                   y=eq['ganancias_por_empresa'],
                   marker_color='gold',
                   text=[f"${g:,.0f}" for g in eq['ganancias_por_empresa']],
                   textposition='auto'),
            row=2, col=2
        )

        fig.update_layout(
            title_text=f"Modelo de Bertrand - {n} empresas",
            height=700,
            showlegend=True,
            template='plotly_white'
        )

        return fig
