"""
Prepara los datos extraídos para el dashboard:
1. Limpia RIBARCO SAS 206 (fusiona con RIBARCO SAS)
2. Elimina duplicados
3. Crea CSVs por empresa (formato ancho)
4. Crea métricas del sector
"""

import pandas as pd
import os

RUTA_ORIGEN = os.path.join('..', 'extractor', 'output', 'huevos_colombia_2016_2025.csv')
RUTA_DESTINO = os.path.join('data', 'consolidado_limpio.csv')
RUTA_EMPRESAS = os.path.join('data', 'empresas')
RUTA_METRICAS = os.path.join('data', 'metricas_sector.csv')

CAMPOS_FINANCIEROS = [
    'ingresos_actividades_ordinarias',
    'costo_ventas',
    'ganancia_bruta',
    'otros_ingresos',
    'gastos_ventas',
    'gastos_administracion',
    'otros_gastos',
    'otras_ganancias_perdidas',
    'ganancia_operacion',
    'ingresos_financieros',
    'costos_financieros',
    'ganancia_antes_impuestos',
    'impuestos',
    'ganancia_operaciones_continuadas',
    'ganancia_operaciones_discontinuadas',
    'ganancia_neta'
]

RATIOS = [
    'margen_bruto',
    'margen_operacional',
    'margen_neto',
    'intensidad_gasto_comercial',
    'intensidad_gasto_admin',
    'carga_fiscal_efectiva'
]

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

CATEGORIAS = {
    'Ingresos': ['ingresos_actividades_ordinarias', 'otros_ingresos', 'ingresos_financieros'],
    'Costos y Gastos': ['costo_ventas', 'gastos_ventas', 'gastos_administracion', 'otros_gastos', 'costos_financieros'],
    'Ganancias': ['ganancia_bruta', 'ganancia_operacion', 'ganancia_antes_impuestos', 'ganancia_operaciones_continuadas', 'ganancia_operaciones_discontinuadas', 'ganancia_neta'],
    'Impuestos': ['impuestos'],
    'Ratios': ['margen_bruto', 'margen_operacional', 'margen_neto', 'intensidad_gasto_comercial', 'intensidad_gasto_admin', 'carga_fiscal_efectiva'],
    'Otros': ['otras_ganancias_perdidas']
}


def cargar_datos(ruta):
    return pd.read_csv(ruta)


def limpiar_ribarco(df):
    """Fusiona RIBARCO SAS 206 en RIBARCO SAS (archivo corrupto 206.pdf = 2016)."""
    df_limpio = df.copy()

    ribarco_206 = df_limpio[df_limpio['empresa'] == 'RIBARCO SAS 206']
    ribarco_main = df_limpio[df_limpio['empresa'] == 'RIBARCO SAS']

    if not ribarco_206.empty and not ribarco_main.empty:
        for _, row_206 in ribarco_206.iterrows():
            anio = row_206['anio_fiscal']
            existe = ribarco_main[ribarco_main['anio_fiscal'] == anio]
            if existe.empty:
                nueva_fila = row_206.copy()
                nueva_fila['empresa'] = 'RIBARCO SAS'
                df_limpio = pd.concat([df_limpio, pd.DataFrame([nueva_fila])], ignore_index=True)

    df_limpio = df_limpio[df_limpio['empresa'] != 'RIBARCO SAS 206']
    return df_limpio


def eliminar_duplicados(df):
    """Elimina duplicados empresa-año, conservando el registro más completo."""
    df['_campos_no_nulos'] = df[CAMPOS_FINANCIEROS].notna().sum(axis=1)
    df = df.sort_values('_campos_no_nulos', ascending=False)
    df = df.drop_duplicates(subset=['empresa', 'anio_fiscal'], keep='first')
    df = df.drop(columns=['_campos_no_nulos'])
    return df


def calcular_metricas_sector(df):
    """Calcula IHH y Lerner ponderado por año."""
    filas = []
    for anio in sorted(df['anio_fiscal'].unique()):
        df_anio = df[df['anio_fiscal'] == anio].copy()
        ing_total = df_anio['ingresos_actividades_ordinarias'].sum()

        if ing_total and ing_total > 0:
            df_anio['cuota'] = df_anio['ingresos_actividades_ordinarias'] / ing_total
            ihh = (df_anio['cuota'] ** 2).sum()
            num_empresas = len(df_anio)
            df_anio['contribucion_lerner'] = df_anio['cuota'] * df_anio['margen_bruto'].fillna(0)
            lerner = df_anio['contribucion_lerner'].sum()
        else:
            ihh = None
            num_empresas = 0
            lerner = None

        filas.append({
            'anio_fiscal': anio,
            'num_empresas': num_empresas,
            'ingreso_total': ing_total if ing_total else 0,
            'ihh': round(ihh, 4) if ihh else None,
            'lerner_ponderado': round(lerner, 4) if lerner else None
        })

    return pd.DataFrame(filas)


def crear_csv_empresa(df, empresa, carpeta):
    """Crea un CSV en formato ancho (indicadores × años) para una empresa."""
    df_emp = df[df['empresa'] == empresa].copy()
    anios = sorted(df_emp['anio_fiscal'].unique())

    filas = []
    for campo in CAMPOS_FINANCIEROS + RATIOS:
        nombre_mostrar = NOMBRES_INDICADORES.get(campo, campo)
        categoria = next((cat for cat, campos in CATEGORIAS.items() if campo in campos), 'Otros')
        valores = {'indicador': campo, 'nombre': nombre_mostrar, 'categoria': categoria}
        for anio in anios:
            fila = df_emp[df_emp['anio_fiscal'] == anio]
            valores[str(anio)] = fila[campo].values[0] if not fila[campo].isna().all() else None
        filas.append(valores)

    df_wide = pd.DataFrame(filas)
    ruta = os.path.join(carpeta, f"{empresa}.csv")
    df_wide.to_csv(ruta, index=False, encoding='utf-8')
    return df_wide


def main():
    os.makedirs(RUTA_EMPRESAS, exist_ok=True)

    print("Cargando datos...")
    df = cargar_datos(RUTA_ORIGEN)
    print(f"  Registros iniciales: {len(df)}")
    print(f"  Empresas: {df['empresa'].nunique()}")

    print("\nLimpiando RIBARCO SAS 206...")
    df = limpiar_ribarco(df)
    print(f"  Registros: {len(df)}")
    print(f"  Empresas: {df['empresa'].nunique()}")

    print("\nEliminando duplicados...")
    df = eliminar_duplicados(df)
    print(f"  Registros finales: {len(df)}")

    df = df.sort_values(['empresa', 'anio_fiscal']).reset_index(drop=True)

    print("\nExportando consolidado limpio...")
    df.to_csv(RUTA_DESTINO, index=False, encoding='utf-8')
    print(f"  -> {RUTA_DESTINO}")

    print("\nCreando CSVs por empresa...")
    for empresa in sorted(df['empresa'].unique()):
        crear_csv_empresa(df, empresa, RUTA_EMPRESAS)
        print(f"  -> {empresa}")
    print(f"  {len(df['empresa'].unique())} empresas creadas")

    print("\nCalculando métricas del sector...")
    metricas = calcular_metricas_sector(df)
    metricas.to_csv(RUTA_METRICAS, index=False, encoding='utf-8')
    print(f"  -> {RUTA_METRICAS}")

    print("\nResumen por empresa:")
    for empresa in sorted(df['empresa'].unique()):
        df_emp = df[df['empresa'] == empresa]
        anios = sorted(df_emp['anio_fiscal'].unique())
        ing_prom = df_emp['ingresos_actividades_ordinarias'].mean()
        print(f"  {empresa}: {len(anios)} años ({min(anios)}-{max(anios)}), ingreso prom: ${ing_prom:,.0f}")

    print("\nMetricas del sector:")
    for _, row in metricas.iterrows():
        print(f"  {int(row['anio_fiscal'])}: {int(row['num_empresas'])} empresas, IHH={row['ihh']}, Lerner={row['lerner_ponderado']}")

    print("\nListo. Datos preparados para el dashboard.")


if __name__ == '__main__':
    main()
