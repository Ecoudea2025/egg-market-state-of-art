from abc import ABC, abstractmethod
import pandas as pd
import plotly.graph_objects as go
import numpy as np


class ModeloEconomico(ABC):
    """Clase base para todos los modelos económicos.

    Cualquier modelo económico (oligopolio, competencia, macro, etc.)
    debe heredar de esta clase e implementar sus métodos abstractos.
    Esto garantiza que la página de simulación pueda cargar cualquier
    modelo de forma dinámica sin conocer su implementación interna.
    """

    @abstractmethod
    def calcular_equilibrio(self) -> dict:
        """Calcula el equilibrio del modelo.

        Returns:
            dict con los valores de equilibrio (precios, cantidades, ganancias, etc.)
        """
        pass

    @abstractmethod
    def simular(self, periodos: int) -> pd.DataFrame:
        """Ejecuta una simulación dinámica del modelo.

        Args:
            periodos: Número de períodos a simular

        Returns:
            DataFrame con la evolución temporal de las variables
        """
        pass

    @abstractmethod
    def graficar(self) -> go.Figure:
        """Genera la visualización principal del modelo.

        Returns:
            Figure de Plotly lista para renderizar en Streamlit
        """
        pass

    @property
    @abstractmethod
    def parametros(self) -> dict:
        """Retorna los parámetros editables del modelo.

        Returns:
            dict con nombre -> {tipo, valor_default, min, max, step, descripcion}
        """
        pass

    @abstractmethod
    def actualizar_parametros(self, **kwargs):
        """Actualiza los parámetros del modelo."""
        pass

    @property
    def nombre(self) -> str:
        """Nombre legible del modelo."""
        return self.__class__.__name__

    @property
    def descripcion(self) -> str:
        """Descripción del modelo económico."""
        return ""

    def resumen(self) -> str:
        """Resumen textual del resultado del equilibrio."""
        eq = self.calcular_equilibrio()
        if not eq:
            return "No se pudo calcular el equilibrio."
        return '\n'.join(f"{k}: {v}" for k, v in eq.items())

    @staticmethod
    def _formatear_moneda(valor) -> str:
        if pd.isna(valor) or valor is None:
            return "-"
        return f"${valor:,.2f}"

    @staticmethod
    def _crear_tabla_comparativa(resultados: dict) -> pd.DataFrame:
        """Crea tabla de comparación entre distintos escenarios."""
        return pd.DataFrame(resultados)
