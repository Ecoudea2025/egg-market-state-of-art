"""Modulo de ingesta dinamica de PDFs.

Permite:
1. Subir PDFs individuales mediante boton en el dashboard
2. Monitorear una carpeta para procesamiento automatico
3. Fusionar nuevos datos con el consolidado existente
4. Re-ejecutar la extraccion completa

Arquitectura extensible: para soportar nuevos formatos de PDF,
agregar funciones de parseo en extractor/extractor.py.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import json
import time
from datetime import datetime
from threading import Thread, Event

# Agregar extractor al path
RUTA_EXTRACTOR = Path(__file__).parent.parent / 'extractor'
if str(RUTA_EXTRACTOR) not in sys.path:
    sys.path.insert(0, str(RUTA_EXTRACTOR))

RUTA_CONSOLIDADO = Path(__file__).parent / 'data' / 'consolidado_limpio.csv'
RUTA_HISTORIAL = Path(__file__).parent / 'data' / 'historial_ingesta.json'
RUTA_PDF = Path(__file__).parent.parent / 'PDF'


def _cargar_historial() -> list:
    """Carga el historial de ingesta."""
    if RUTA_HISTORIAL.exists():
        try:
            with open(RUTA_HISTORIAL, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _guardar_historial(historial: list):
    """Guarda el historial de ingesta."""
    with open(RUTA_HISTORIAL, 'w') as f:
        json.dump(historial[-100:], f, indent=2, default=str)


def _registrar_operacion(tipo: str, empresa: str, anio: str, estado: str, detalle: str = ""):
    """Registra una operacion en el historial."""
    historial = _cargar_historial()
    historial.append({
        'timestamp': datetime.now().isoformat(),
        'tipo': tipo,
        'empresa': empresa,
        'anio': anio,
        'estado': estado,
        'detalle': detalle,
    })
    _guardar_historial(historial)
    return historial


def procesar_pdf_unico(ruta_pdf: Path) -> pd.DataFrame | None:
    """Procesa un unico archivo PDF y retorna DataFrame con los registros extraidos.

    Args:
        ruta_pdf: Ruta al archivo PDF

    Returns:
        DataFrame con los registros extraidos, o None si falla
    """
    try:
        from extractor import procesar_archivo
        registros = procesar_archivo(ruta_pdf)
        if registros:
            return pd.DataFrame(registros)
        return None
    except Exception as e:
        st.error(f"Error al procesar {ruta_pdf.name}: {e}")
        return None


def fusionar_con_consolidado(df_nuevo: pd.DataFrame) -> pd.DataFrame:
    """Fusiona nuevos datos con el consolidado existente.

    - Agrega nuevas empresas/años
    - Sobrescribe si ya existe (empresa + año)
    - Rellena columnas faltantes con NaN

    Returns:
        DataFrame fusionado
    """
    if not RUTA_CONSOLIDADO.exists():
        return df_nuevo

    df_existente = pd.read_csv(RUTA_CONSOLIDADO)

    if df_nuevo.empty:
        return df_existente

    # Combinar y eliminar duplicados (empresa + año), priorizando nuevos datos
    df_combinado = pd.concat([df_existente, df_nuevo], ignore_index=True)
    df_combinado = df_combinado.drop_duplicates(
        subset=['empresa', 'anio_fiscal'],
        keep='last'
    )
    df_combinado = df_combinado.sort_values(
        ['empresa', 'anio_fiscal']
    ).reset_index(drop=True)

    # Rellenar columnas faltantes
    for col in df_existente.columns:
        if col not in df_combinado.columns:
            df_combinado[col] = None

    return df_combinado


def exportar_consolidado(df: pd.DataFrame):
    """Exporta el DataFrame consolidado a CSV."""
    RUTA_CONSOLIDADO.parent.mkdir(exist_ok=True)
    df.to_csv(RUTA_CONSOLIDADO, index=False, encoding='utf-8')


def detectar_empresa_anio(nombre_archivo: str) -> tuple[str, int | None]:
    """Extrae nombre de empresa y año del nombre del archivo PDF.

    Maneja casos como:
    - "EMPRESA 2017.pdf" -> ("EMPRESA", 2017)
    - "EMPRESA  2017.pdf" (doble espacio)
    - "EMPRESA 206.pdf" (año corrupto: 206 -> 2016, heuristico)
    - "EMPRESA SAS 2017-2025.pdf" -> ("EMPRESA SAS", None)
    """
    import re

    nombre = Path(nombre_archivo).stem

    # Detectar año(s) en el nombre
    anio_match = re.search(r'(\d{4})(?:\s*-\s*(\d{4}))?\s*$', nombre)
    if anio_match:
        anio = int(anio_match.group(1))
        nombre_empresa = nombre[:anio_match.start()].strip()
    else:
        # Intentar con año corrupto (3 dígitos)
        anio_corto = re.search(r'(\d{3})\s*$', nombre)
        if anio_corto:
            digits = anio_corto.group(1)
            if len(digits) == 3:
                anio = 2000 + int(digits) if int(digits) < 100 else int(digits)
                if 2015 <= anio <= 2030:
                    nombre_empresa = nombre[:anio_corto.start()].strip()
                else:
                    nombre_empresa = nombre
                    anio = None
            else:
                nombre_empresa = nombre
                anio = None
        else:
            nombre_empresa = nombre
            anio = None

    nombre_empresa = re.sub(r'\s+', ' ', nombre_empresa).strip()

    return nombre_empresa, anio


def re_ejecutar_extraccion(carpeta_pdf: Path) -> pd.DataFrame:
    """Re-ejecuta la extraccion completa de todos los PDFs."""
    try:
        from extractor import procesar_carpeta
        df = procesar_carpeta(carpeta_pdf)
        return df
    except Exception as e:
        st.error(f"Error al re-ejecutar extraccion: {e}")
        return pd.DataFrame()


class WatcherPDF:
    """Monitorea una carpeta de PDFs y procesa nuevos archivos automaticamente.

    Uso:
        watcher = WatcherPDF(carpeta_pdf, callback=mi_funcion)
        watcher.start()
        ...
        watcher.stop()
    """

    def __init__(self, carpeta: Path, callback=None, intervalo: int = 60):
        self.carpeta = carpeta
        self.callback = callback
        self.intervalo = intervalo
        self._procesados = set()
        self._stop_event = Event()
        self._thread = None

        # Cargar historial de procesados
        self._cargar_procesados()

    def _cargar_procesados(self):
        """Carga el historial de archivos ya procesados."""
        historial = _cargar_historial()
        for entry in historial:
            if entry.get('tipo') == 'auto_ingesta' and entry.get('estado') == 'exito':
                self._procesados.add(entry.get('detalle', ''))

    def start(self):
        """Inicia el monitoreo en un thread separado."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Detiene el monitoreo."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self):
        """Loop principal de monitoreo."""
        while not self._stop_event.is_set():
            try:
                if self.carpeta.exists():
                    for pdf in self.carpeta.glob('*.pdf'):
                        if pdf.name not in self._procesados:
                            df = procesar_pdf_unico(pdf)
                            if df is not None and not df.empty:
                                df_fusionado = fusionar_con_consolidado(df)
                                exportar_consolidado(df_fusionado)
                                _registrar_operacion(
                                    'auto_ingesta', pdf.stem, '',
                                    'exito', pdf.name
                                )
                                self._procesados.add(pdf.name)

                                if self.callback:
                                    self.callback(pdf.name, df)
            except Exception:
                pass

            self._stop_event.wait(self.intervalo)


def mostrar_pagina_ingesta():
    """Pagina de gestion de datos e ingesta."""
    st.header("Gestion de Datos")

    tab_subir, tab_estado, tab_watcher, tab_historial = st.tabs([
        "📤 Subir PDFs", "📊 Estado de Datos", "👁️ Monitoreo", "📜 Historial"
    ])

    with tab_subir:
        st.subheader("Subir Nuevos PDFs")

        pdfs_subidos = st.file_uploader(
            "Selecciona archivos PDF para procesar",
            type=['pdf'],
            accept_multiple_files=True,
            help="Puedes subir uno o varios PDFs a la vez"
        )

        if pdfs_subidos:
            if st.button("Procesar PDFs Subidos", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()

                resultados = []
                for i, pdf_file in enumerate(pdfs_subidos):
                    status_text.text(f"Procesando: {pdf_file.name}...")

                    # Guardar temporalmente
                    ruta_temp = RUTA_PDF / pdf_file.name
                    with open(ruta_temp, 'wb') as f:
                        f.write(pdf_file.getbuffer())

                    df = procesar_pdf_unico(ruta_temp)
                    if df is not None and not df.empty:
                        empresa = df['empresa'].iloc[0]
                        anios = df['anio_fiscal'].tolist()
                        resultados.append(df)

                        _registrar_operacion(
                            'subida', empresa,
                            f"{min(anios)}-{max(anios)}",
                            'exito', f"{len(df)} registros"
                        )
                        status_text.text(f"✅ {pdf_file.name}: {empresa} ({len(df)} registros)")
                    else:
                        _registrar_operacion(
                            'subida', pdf_file.stem, '',
                            'fallo', 'No se pudieron extraer datos'
                        )
                        status_text.text(f"❌ {pdf_file.name}: No se pudieron extraer datos")

                    progress_bar.progress((i + 1) / len(pdfs_subidos))

                if resultados:
                    df_combinado = pd.concat(resultados, ignore_index=True)
                    df_final = fusionar_con_consolidado(df_combinado)
                    exportar_consolidado(df_final)

                    status_text.text(f"✅ Procesados {len(resultados)} archivos exitosamente")
                    st.success("Datos fusionados con el consolidado!")
                    st.cache_data.clear()
                    st.rerun()

        st.markdown("---")
        st.subheader("Re-ejecutar Extraccion Completa")

        if st.button("Re-ejecutar desde todos los PDFs",
                     help="Vuelve a procesar los 150+ PDFs desde cero"):
            with st.spinner("Re-ejecutando extraccion completa..."):
                df = re_ejecutar_extraccion(RUTA_PDF)
                if not df.empty:
                    exportar_consolidado(df)
                    _registrar_operacion(
                        'reejecucion', 'todas', '',
                        'exito', f"{len(df)} registros"
                    )
                    st.success(f"Extraccion completa: {len(df)} registros generados")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("No se generaron datos")

    with tab_estado:
        st.subheader("Estado del Consolidado")

        if RUTA_CONSOLIDADO.exists():
            df = pd.read_csv(RUTA_CONSOLIDADO)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Empresas", df['empresa'].nunique())
            with col2:
                st.metric("Registros", len(df))
            with col3:
                st.metric("Años", f"{int(df['anio_fiscal'].min())}-{int(df['anio_fiscal'].max())}")
            with col4:
                completitud = df.notna().mean().mean() * 100
                st.metric("Completitud", f"{completitud:.1f}%")

            # Tabla de cobertura por empresa
            st.subheader("Cobertura por Empresa")
            cobertura = df.groupby('empresa').agg(
                anios=('anio_fiscal', lambda x: f"{int(x.min())}-{int(x.max())}"),
                registros=('anio_fiscal', 'count'),
                completitud=('ingresos_actividades_ordinarias',
                             lambda x: f"{x.notna().mean()*100:.0f}%"),
            ).reset_index()

            st.dataframe(cobertura, use_container_width=True, hide_index=True)
        else:
            st.warning("No hay datos consolidados. Sube PDFs o ejecuta la extraccion.")

    with tab_watcher:
        st.subheader("Monitoreo Automatico de Carpeta")

        st.markdown(f"""
        **Carpeta monitoreada:** `{RUTA_PDF}`

        El monitor detecta automaticamente nuevos PDFs agregados a la carpeta
        y los procesa sin intervencion manual.
        """)

        if 'watcher' not in st.session_state:
            st.session_state.watcher = None
            st.session_state.watcher_activo = False

        if not st.session_state.watcher_activo:
            if st.button("Iniciar Monitoreo", type="primary"):
                def callback(nombre, df):
                    st.toast(f"✅ Nuevo PDF procesado: {nombre}")

                st.session_state.watcher = WatcherPDF(
                    RUTA_PDF, callback=callback, intervalo=60
                )
                st.session_state.watcher.start()
                st.session_state.watcher_activo = True
                st.rerun()
        else:
            st.success("✅ Monitoreo activo - revisando cada 60 segundos")
            if st.button("Detener Monitoreo"):
                if st.session_state.watcher:
                    st.session_state.watcher.stop()
                st.session_state.watcher_activo = False
                st.rerun()

    with tab_historial:
        st.subheader("Historial de Operaciones")

        historial = _cargar_historial()
        if historial:
            df_hist = pd.DataFrame(historial)
            df_hist = df_hist.tail(50)  # Últimas 50 operaciones

            st.dataframe(
                df_hist.style.applymap(
                    lambda x: 'color: green' if x == 'exito'
                    else ('color: red' if x == 'fallo' else ''),
                    subset=['estado']
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No hay operaciones registradas.")
