"""Generate JSON data for the Cournot Incubadora model (2018-2024)
to be used in the static GitHub Pages site."""
import json, os, sys
base = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base, 'dashboard'))
os.chdir(os.path.join(base, 'dashboard'))

from modelos_economicos.oligopolio.cournot_incubadora import CournotIncubadora

model = CournotIncubadora()
all_data = []

for yr in range(2018, 2025):
    model.actualizar_parametros(anio=yr)
    eq = model.calcular_equilibrio()
    data_yr = model._cargar_datos()

    year_data = {
        "anio": yr,
        "modelo": "Cournot Incubadora vs Resto",
        "parametros": {
            "elasticidad": eq["elasticidad"],
            "demanda_a": eq["demanda_a"],
            "demanda_b": eq["demanda_b"],
            "costo_inc": eq["costo_inc"],
            "costo_resto": eq["costo_resto"],
        },
        "equilibrio_cournot": {
            "precio": eq["precio_eq"],
            "cantidad_total": eq["cantidad_total_eq"],
            "cantidad_inc": eq["cantidad_inc"],
            "cantidad_resto": eq["cantidad_resto"],
            "ganancia_inc": eq["ganancia_inc"],
            "ganancia_resto": eq["ganancia_resto"],
            "ganancia_total": eq["ganancia_total"],
            "share_inc": eq["share_inc_eq"],
            "share_resto": eq["share_resto_eq"],
        },
        "datos_reales": {
            "cantidad_total": eq["cantidad_total_real"],
            "cantidad_inc": eq["cantidad_inc_real"],
            "cantidad_resto": eq["cantidad_resto_real"],
            "ganancia_inc": eq["ganancia_inc_real"],
            "ganancia_resto": eq["ganancia_resto_real"],
            "ganancia_total": eq["ganancia_total_real"],
            "share_inc": eq["share_inc_real"],
            "share_resto": eq["share_resto_real"],
            "margen_inc": eq["margen_inc_real"],
            "margen_resto": eq["margen_resto_real"],
        },
        "comparacion": {
            "dif_precio_pct": eq["dif_precio_pct"],
            "dif_cantidad_total_pct": eq["dif_cantidad_total_pct"],
            "dif_cantidad_inc_pct": eq["dif_cantidad_inc_pct"],
            "dif_cantidad_resto_pct": eq["dif_cantidad_resto_pct"],
        }
    }

    # Add monopoly and perfect competition scenarios
    a, b = eq["demanda_a"], eq["demanda_b"]
    c_medio = (eq["costo_inc"] + eq["costo_resto"]) / 2

    q_m = max((a - c_medio) / (2 * b), 0)
    p_m = max(a - b * q_m, 0)
    pi_m = max((p_m - c_medio) * q_m, 0)
    ec_m = 0.5 * (a - p_m) * q_m if a > p_m else 0

    q_cp = max((a - c_medio) / b, 0)
    p_cp = c_medio
    ec_cp = 0.5 * (a - p_cp) * q_cp if a > p_cp else 0

    year_data["escenarios"] = {
        "Cournot": {"cantidad": eq["cantidad_total_eq"], "precio": eq["precio_eq"], "ganancia": eq["ganancia_total"]},
        "Real": {"cantidad": eq["cantidad_total_real"], "precio": 1.0, "ganancia": eq["ganancia_total_real"]},
        "Monopolio": {"cantidad": q_m, "precio": p_m, "ganancia": pi_m},
        "Comp_Perfecta": {"cantidad": q_cp, "precio": p_cp, "ganancia": 0, "excedente_consumidor": ec_cp},
    }

    all_data.append(year_data)

docs_dir = os.path.join(base, "docs", "data")
os.makedirs(docs_dir, exist_ok=True)

output_path = os.path.join(docs_dir, "cournot_data.js")
with open(output_path, "w", encoding="utf-8") as f:
    f.write("window.COURNOT_DATA = ")
    json.dump(all_data, f, ensure_ascii=False, indent=2)
    f.write(";")

print(f"Generated {len(all_data)} years of Cournot data -> {output_path}")

json_path = os.path.join(docs_dir, "cournot_data.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)
print(f"Generated JSON -> {json_path}")
