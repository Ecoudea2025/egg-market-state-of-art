"""
Script de consolidación y exportación de datos para el Observatorio del Mercado del Huevo (UdeA).
Unifica datos financieros (SuperSociedades), IPC DANE (2015-2025), precios/elasticidades (FENAVI/DANE)
y citas académicas en formato JSON/JS y CSVs limpios en docs/data/ y docs/csv/.
"""

import csv
import json
import math
import os
import shutil
from pathlib import Path
from collections import defaultdict

# Rutas base
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_DIR = SCRIPT_DIR.parent
ROOT_DIR = REPO_DIR.parent

DOCS_DIR = REPO_DIR / "docs"
DATA_DIR = DOCS_DIR / "data"
CSV_DIR = DOCS_DIR / "csv"

# Rutas de fuentes
PATH_CONSOLIDADO = ROOT_DIR / "Proyecto extractor PDF" / "dashboard" / "data" / "consolidado_limpio.csv"
PATH_IPC_GLOBAL = ROOT_DIR / "IPC DANE" / "ipc_dane_extractor" / "output_final" / "ipc_serie_global_2015_2025.csv"
PATH_IPC_DIV = ROOT_DIR / "IPC DANE" / "ipc_dane_extractor" / "output_final" / "ipc_divisiones_2015_2025.csv"
PATH_DATO_ECON = ROOT_DIR / "Proyecto extractor PDF" / "Dato economía.csv"
PATH_DATOS_GEN = ROOT_DIR / "Proyecto extractor PDF" / "Datos en general.csv"
PATH_CONSUMO = ROOT_DIR / "Proyecto extractor PDF" / "consumo huevo.csv"
PATH_PRODUCCION = ROOT_DIR / "Proyecto extractor PDF" / "Producción huevo anual.csv"
PATH_CITATIONS_JSON = DATA_DIR / "citations.json"


def read_lines_safe(path: Path):
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.readlines()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"No se pudo decodificar {path}")


def parse_float(val, default=None):
    if val is None:
        return default
    s = str(val).strip()
    if s == "" or s.lower() in ("nan", "null", "none", "-"):
        return default
    # Formato colombiano/europeo con puntos de miles y coma decimal si aplica
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        v = float(s)
        return None if math.isnan(v) else v
    except ValueError:
        return default


def parse_int(val, default=None):
    f = parse_float(val)
    return int(round(f)) if f is not None else default


def write_json_and_js(name: str, var_name: str, payload):
    json_path = DATA_DIR / f"{name}.json"
    js_path = DATA_DIR / f"{name}.js"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(f"window.{var_name} = ")
        json.dump(payload, f, ensure_ascii=False)
        f.write(";\n")
    print(f"  [OK] Generado {json_path.name} y {js_path.name}")


def process_market_data():
    print("Procesando datos financieros y concentración (SuperSociedades)...")
    firms_data = []
    by_year = defaultdict(list)
    by_firm = defaultdict(list)

    with open(PATH_CONSOLIDADO, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            anio = parse_int(row.get("anio_fiscal"))
            ing = parse_float(row.get("ingresos_actividades_ordinarias"), 0.0) or 0.0
            rec = {
                "empresa": row["empresa"].strip(),
                "nit": row["nit"].strip(),
                "anio_fiscal": anio,
                "ingresos_actividades_ordinarias": ing,
                "costo_ventas": parse_float(row.get("costo_ventas")),
                "ganancia_bruta": parse_float(row.get("ganancia_bruta")),
                "ganancia_operacion": parse_float(row.get("ganancia_operacion")),
                "ganancia_neta": parse_float(row.get("ganancia_neta")),
                "impuestos": parse_float(row.get("impuestos")),
                "margen_bruto": parse_float(row.get("margen_bruto")),
                "margen_operacional": parse_float(row.get("margen_operacional")),
                "margen_neto": parse_float(row.get("margen_neto")),
                "intensidad_gasto_comercial": parse_float(row.get("intensidad_gasto_comercial")),
                "intensidad_gasto_admin": parse_float(row.get("intensidad_gasto_admin")),
                "carga_fiscal_efectiva": parse_float(row.get("carga_fiscal_efectiva")),
                "cuota_mercado": 0.0,
            }
            firms_data.append(rec)
            by_year[anio].append(rec)
            by_firm[rec["empresa"]].append(rec)

    yearly_metrics = []
    for anio in sorted(by_year.keys()):
        records = by_year[anio]
        ing_total = sum(r["ingresos_actividades_ordinarias"] for r in records)
        for r in records:
            r["cuota_mercado"] = round(r["ingresos_actividades_ordinarias"] / ing_total, 6) if ing_total > 0 else 0.0

        sorted_recs = sorted(records, key=lambda x: x["cuota_mercado"], reverse=True)
        shares = [r["cuota_mercado"] for r in sorted_recs]

        ihh_norm = sum(s ** 2 for s in shares)
        ihh_pts = ihh_norm * 10000.0
        cr1 = sum(shares[:1]) * 100.0
        cr3 = sum(shares[:3]) * 100.0
        cr4 = sum(shares[:4]) * 100.0
        cr8 = sum(shares[:8]) * 100.0

        lerner = sum(r["cuota_mercado"] * (r["margen_bruto"] or 0.0) for r in records)
        margen_op = sum(r["cuota_mercado"] * (r["margen_operacional"] or 0.0) for r in records)

        top_empresas = [
            {
                "empresa": r["empresa"],
                "cuota_pct": round(r["cuota_mercado"] * 100.0, 2),
                "ingresos": r["ingresos_actividades_ordinarias"],
                "contribucion_ihh": round((r["cuota_mercado"] * 100.0) ** 2, 2),
            }
            for r in sorted_recs
        ]

        yearly_metrics.append({
            "anio": anio,
            "num_empresas": len(records),
            "ingreso_total": ing_total,
            "ihh_norm": round(ihh_norm, 4),
            "ihh_pts": round(ihh_pts, 1),
            "cr1": round(cr1, 2),
            "cr3": round(cr3, 2),
            "cr4": round(cr4, 2),
            "cr8": round(cr8, 2),
            "lerner_ponderado": round(lerner, 4),
            "margen_op_ponderado": round(margen_op, 4),
            "top_empresas": top_empresas,
        })

    firms_list = []
    for emp, recs in sorted(by_firm.items()):
        ing_acum = sum(r["ingresos_actividades_ordinarias"] for r in recs)
        cuota_prom = sum(r["cuota_mercado"] for r in recs) / len(recs)
        firms_list.append({
            "empresa": emp,
            "nit": recs[0]["nit"],
            "anios_activos": len(recs),
            "ingreso_acumulado": ing_acum,
            "cuota_promedio_pct": round(cuota_prom * 100.0, 2),
        })
    firms_list.sort(key=lambda x: x["ingreso_acumulado"], reverse=True)

    payload = {
        "yearly_metrics": yearly_metrics,
        "firms_data": firms_data,
        "firms_list": firms_list,
    }
    write_json_and_js("market_data", "MARKET_DATA", payload)

    # Exportar CSVs limpios de mercado
    shutil.copy2(PATH_CONSOLIDADO, CSV_DIR / "consolidado_15_empresas_2015_2025.csv")
    with open(CSV_DIR / "metricas_concentracion_ihh_cr_2015_2025.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["anio", "num_empresas", "ingreso_total_cop", "ihh_escala_0_1", "ihh_puntos_10000", "cr1_pct", "cr3_pct", "cr4_pct", "cr8_pct", "lerner_ponderado", "margen_op_ponderado"])
        for m in yearly_metrics:
            writer.writerow([m["anio"], m["num_empresas"], m["ingreso_total"], m["ihh_norm"], m["ihh_pts"], m["cr1"], m["cr3"], m["cr4"], m["cr8"], m["lerner_ponderado"], m["margen_op_ponderado"]])

    print(f"  [OK] {len(firms_list)} empresas, {len(yearly_metrics)} años procesados.")


def process_ipc_and_macro():
    print("Procesando IPC DANE, precios del huevo y macroeconomía...")
    # 1. IPC Global
    ipc_mensual = []
    with open(PATH_IPC_GLOBAL, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            ipc_mensual.append({
                "fecha": row["fecha"].strip(),
                "anio": parse_int(row["anio"]),
                "mes": parse_int(row["mes"]),
                "indice": round(parse_float(row["indice"], 0.0), 4),
                "var_mensual": parse_float(row["var_mensual"]),
                "var_acumulado": parse_float(row["var_acumulado"]),
                "var_anual": parse_float(row["var_anual"]),
                "base": parse_int(row.get("base"), 2018),
            })

    # Calcular variación anual si falta (p. ej. transición Base 2018 durante 2019)
    by_ym = {(r["anio"], r["mes"]): r for r in ipc_mensual}
    for r in ipc_mensual:
        if r.get("var_anual") is None:
            prev = by_ym.get((r["anio"] - 1, r["mes"]))
            if prev and prev.get("indice") and r.get("indice"):
                r["var_anual"] = round(((r["indice"] / prev["indice"]) - 1.0) * 100.0, 2)

    # 2. IPC Divisiones (fusionando columnas duplicadas por capitalización)
    DIV_MAP = {
        "alimentos": "Alimentos",
        "alojamiento, agua, electricidad, gas y otros combustibles": "Alojamiento y Servicios Públicos",
        "bebidas alcohólicas y tabaco": "Bebidas Alcohólicas y Tabaco",
        "bienes y servicios diversos": "Bienes y Servicios Diversos",
        "comunicaciones": "Comunicaciones",
        "información y comunicación": "Información y Comunicación",
        "diversión": "Diversión / Recreación",
        "recreación y cultura": "Recreación y Cultura",
        "educación": "Educación",
        "muebles, artículos para el hogar y para la conservación ordinaria del hogar": "Muebles y Hogar",
        "otros gastos": "Otros Gastos",
        "prendas de vestir y calzado": "Prendas de Vestir y Calzado",
        "vestuario": "Vestuario",
        "restaurantes y hoteles": "Restaurantes y Hoteles",
        "salud": "Salud",
        "total": "Total Nacional",
        "transporte": "Transporte",
        "vivienda": "Vivienda",
    }

    ipc_divisiones = []
    div_keys = set()
    with open(PATH_IPC_DIV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entry = {"fecha": row["fecha"].strip()}
            for raw_col, raw_val in row.items():
                if raw_col == "fecha":
                    continue
                val = parse_float(raw_val)
                if val is not None:
                    norm_name = DIV_MAP.get(raw_col.strip().lower(), raw_col.strip())
                    entry[norm_name] = val
                    div_keys.add(norm_name)
            ipc_divisiones.append(entry)

    # 3. Precios mensuales huevo (Dato economía.csv)
    precios_huevo_mensual = []
    meses_nombre = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    lines = [l.strip().split(";") for l in read_lines_safe(PATH_DATO_ECON) if l.strip()]
    headers = lines[0]
    years = [parse_int(h) for h in headers[1:] if parse_int(h)]
    month_rows = {}
    for row in lines[1:13]:
        m_name = row[0].strip().lower()
        if m_name in meses_nombre:
            m_idx = meses_nombre.index(m_name) + 1
            for i, y in enumerate(years):
                val = parse_float(row[i + 1]) if i + 1 < len(row) else None
                if val is not None:
                    month_rows[(y, m_idx)] = val

    for (y, m_idx) in sorted(month_rows.keys()):
        precios_huevo_mensual.append({
            "fecha": f"{y}-{m_idx:02d}-01",
            "anio": y,
            "mes": m_idx,
            "mes_nombre": meses_nombre[m_idx - 1].capitalize(),
            "precio_cop": month_rows[(y, m_idx)],
        })

    # 4. Producción y consumo anual (2017-2025)
    c_lines = [l.strip().split(";") for l in read_lines_safe(PATH_CONSUMO) if l.strip()]
    c_years = [parse_int(x) for x in c_lines[0]]
    c_vals = [parse_int(x) for x in c_lines[1]]

    p_lines = [l.strip().split(";") for l in read_lines_safe(PATH_PRODUCCION) if l.strip()]
    p_years = [parse_int(x) for x in p_lines[0]]
    p_vals = [parse_int(x.replace(".", "")) for x in p_lines[1]]

    produccion_consumo_anual = []
    for y in c_years:
        c_v = c_vals[c_years.index(y)] if y in c_years else None
        p_v = p_vals[p_years.index(y)] if y in p_years else None
        produccion_consumo_anual.append({
            "anio": y,
            "consumo_per_capita": c_v,
            "produccion_millones": p_v,
        })

    # 5. Datos en general.csv (macro_anual y elasticidades)
    g_lines = [l.strip().split(";") for l in read_lines_safe(PATH_DATOS_GEN) if l.strip()]

    macro_anual = []
    for row in g_lines[1:8]:
        macro_anual.append({
            "anio": parse_int(row[0]),
            "p_huevo_nom": parse_float(row[1]),
            "prod_huevo": parse_float(row[2].replace(".", "")),
            "consumo_huevo": parse_float(row[3]),
            "p_cerdo_nom": parse_float(row[4].replace(".", "")),
            "consumo_cerdo": parse_float(row[5]),
            "prod_cerdo": parse_float(row[6].replace(".", "")),
            "p_maiz_nom": parse_float(row[7].replace(".", "").replace(",", ".")),
            "ipc_var": parse_float(row[8]),
            "indice_base": parse_float(row[10]),
            "p_huevo_real": parse_float(row[11]),
            "p_cerdo_real": parse_float(row[12].replace(".", "").replace(",", ".")),
            "p_maiz_real": parse_float(row[13].replace(".", "").replace(",", ".")),
            "sal_min_nom": parse_float(row[14].replace(".", "").replace(",", ".")),
            "sal_min_real": parse_float(row[15].replace(".", "").replace(",", ".")),
        })

    elasticidades_anuales = []
    for row in g_lines[9:15]:
        if len(row) >= 14 and parse_int(row[0]):
            elasticidades_anuales.append({
                "anio": parse_int(row[0]),
                "delta_q_huevo": parse_float(row[1]),
                "delta_pr_huevo": parse_float(row[2]),
                "elast_precio": parse_float(row[3]),
                "delta_pr_cerdo": parse_float(row[7]),
                "elast_cruzada_cerdo": parse_float(row[8]),
                "delta_sal_min_real": parse_float(row[12]),
                "elast_ingreso": parse_float(row[13]),
            })

    payload = {
        "ipc_mensual": ipc_mensual,
        "ipc_divisiones": ipc_divisiones,
        "divisiones_lista": sorted(list(div_keys)),
        "precios_huevo_mensual": precios_huevo_mensual,
        "produccion_consumo_anual": produccion_consumo_anual,
        "macro_anual": macro_anual,
        "elasticidades": {
            "anuales": elasticidades_anuales,
            "promedios": {
                "precio": -0.13,
                "cruzada_cerdo": -1.15,
                "ingreso_salario": 0.56,
            },
        },
    }
    write_json_and_js("ipc_macro_data", "IPC_MACRO_DATA", payload)

    # Exportar CSVs limpios de IPC y Macro
    shutil.copy2(PATH_IPC_GLOBAL, CSV_DIR / "ipc_nacional_mensual_2015_2025.csv")
    shutil.copy2(PATH_IPC_DIV, CSV_DIR / "ipc_divisiones_gasto_2015_2025.csv")

    with open(CSV_DIR / "precios_mensuales_huevo_2017_2025.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fecha", "anio", "mes", "mes_nombre", "precio_cop_unidad"])
        for p in precios_huevo_mensual:
            w.writerow([p["fecha"], p["anio"], p["mes"], p["mes_nombre"], p["precio_cop"]])

    with open(CSV_DIR / "macro_insumos_elasticidades_2018_2024.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["anio", "p_huevo_nom", "p_huevo_real", "prod_huevo_millones", "consumo_huevo_hab", "p_cerdo_nom", "p_cerdo_real", "p_maiz_nom", "p_maiz_real", "ipc_var_pct", "sal_min_nom", "sal_min_real"])
        for m in macro_anual:
            w.writerow([m["anio"], m["p_huevo_nom"], m["p_huevo_real"], m["prod_huevo"], m["consumo_huevo"], m["p_cerdo_nom"], m["p_cerdo_real"], m["p_maiz_nom"], m["p_maiz_real"], m["ipc_var"], m["sal_min_nom"], m["sal_min_real"]])

    print(f"  [OK] {len(ipc_mensual)} meses IPC, {len(precios_huevo_mensual)} meses precios huevo, {len(macro_anual)} años macro.")


def export_citations_csv():
    if not PATH_CITATIONS_JSON.exists():
        return
    with open(PATH_CITATIONS_JSON, "r", encoding="utf-8") as f:
        cits = json.load(f)
    with open(CSV_DIR / "citas_literatura_verificadas.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "score", "calidad", "documento", "tema", "cita", "contexto"])
        for i, c in enumerate(cits, 1):
            w.writerow([
                i,
                c.get("score", ""),
                c.get("quality", ""),
                c.get("document", ""),
                c.get("topic", ""),
                c.get("text", ""),
                c.get("context", ""),
            ])
    print(f"  [OK] {len(cits)} citas exportadas a CSV.")


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    process_market_data()
    process_ipc_and_macro()
    export_citations_csv()
    print("\n=== Exportación completa finalizada con éxito ===")


if __name__ == "__main__":
    main()
