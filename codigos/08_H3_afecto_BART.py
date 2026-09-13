#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
08_H3_afecto_BART.py
@author: angelanavajas
"""
# ============================================================
# H3 — Afecto y comportamiento en BART
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, shapiro
import statsmodels.formula.api as smf
from statsmodels.stats.diagnostic import het_breuschpagan

# ============================================================
# 1. RUTAS
# ============================================================

PROJECT_ROOT = Path(
    "/Users/angelanavajas/Desktop/anmc/analisis"
)
CLEAN_DATA = PROJECT_ROOT / "datos" / "limpios"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "H3_afecto_BART"

INPUT_PATH = CLEAN_DATA / "base_maestra_final.csv"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 2. CARGAR BASE
# ============================================================

base = pd.read_csv(INPUT_PATH)


# ============================================================
# 3. CONTROL DE ESTRUCTURA
# ============================================================

print("\n")
print("=" * 80)
print("CONTROL DE BASE — H3")
print("=" * 80)


print("\nN participantes:")
print(len(base))


print("\nN por grupo:")
print(
    base["grupo"]
    .value_counts()
)


print("\nParticipant ID único:")
print(
    base["participant_id"].is_unique
)


if len(base) != 74:
    raise ValueError(
        f"Se esperaban 74 participantes y hay {len(base)}."
    )


if not base["participant_id"].is_unique:
    raise ValueError(
        "Hay participant_id duplicados."
    )


# ============================================================
# 4. VARIABLES H3
# ============================================================

OUTCOMES = [
    "adjusted_pumps",
    "total_money",
    "total_explosions",
]

VARIABLES_H3 = [
    "panas_pos_sum",
    "panas_neg_sum",
    "grupo",
    "genero",
    "edad_std_intragrupo",
] + OUTCOMES


faltantes = [
    var
    for var in VARIABLES_H3
    if var not in base.columns
]


if faltantes:
    raise ValueError(
        f"Faltan variables en la base: {faltantes}\n"
        "Si falta edad_std_intragrupo, correr primero "
        "21_construir_base_maestra_final.py actualizado."
    )


# ============================================================
# 5. CONTROL DE MISSING
# ============================================================

print("\n")
print("=" * 80)
print("MISSING — VARIABLES H3")
print("=" * 80)


missing_h3 = (
    base[VARIABLES_H3]
    .isna()
    .sum()
)

print(missing_h3)


if (missing_h3 > 0).any():
    raise ValueError(
        "Hay missing en variables de H3. Revisar antes de analizar."
    )


# ============================================================
# 6. CODIFICAR GRUPO Y GÉNERO
# ============================================================

base["grupo_code"] = base["grupo"].map(
    {
        "joven": 0,
        "mayor": 1,
    }
)


if base["grupo_code"].isna().any():
    raise ValueError(
        "Hay categorías de grupo que no pudieron codificarse."
    )


print("\nCodificación grupo:")
print(
    pd.crosstab(
        base["grupo"],
        base["grupo_code"]
    )
)


if not base["genero"].isin([1, 2]).all():
    raise ValueError(
        "La variable genero contiene valores distintos de 1 y 2."
    )

base["genero_code"] = base["genero"].map(
    {
        1: 0,
        2: 1,
    }
)

print("\nCodificación género:")
print(
    pd.crosstab(
        base["genero"],
        base["genero_code"]
    )
)


# ============================================================
# 7. VERIFICACIÓN DE NORMALIDAD (SHAPIRO-WILK)
#
# Se corre sobre las cinco variables usadas en correlaciones y
# regresiones de H3, antes de calcular cualquier r de Pearson.
# ============================================================

VARIABLES_NORMALIDAD = [
    "panas_pos_sum",
    "panas_neg_sum",
    "adjusted_pumps",
    "total_money",
    "total_explosions",
]

resultados_shapiro = []

for var in VARIABLES_NORMALIDAD:
    stat, p_shapiro = shapiro(base[var])
    resultados_shapiro.append({
        "variable": var,
        "N": len(base[var]),
        "shapiro_W": round(stat, 4),
        "shapiro_p": round(p_shapiro, 4),
        "normal_al_5pct": p_shapiro >= 0.05,
    })

tabla_shapiro = pd.DataFrame(resultados_shapiro)

tabla_shapiro.to_csv(
    OUTPUT_DIR / "H3_shapiro_normalidad.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\n")
print("=" * 80)
print("VERIFICACIÓN DE NORMALIDAD (SHAPIRO-WILK)")
print("=" * 80)
print(tabla_shapiro.to_string(index=False))
print("\nVariables con shapiro_p < .05 se apartan de la normalidad.")
print("Para esas, agregar correlación de Spearman como sensibilidad.\n")


# ============================================================
# 8. FUNCIÓN CORRELACIÓN PEARSON
# ============================================================

def correlacion_pearson(data, x, y, tipo):
    """
    Calcula correlación Pearson con IC95% mediante
    transformación z de Fisher.
    """

    datos = data[[x, y]].dropna()

    n = len(datos)

    r, p = pearsonr(
        datos[x],
        datos[y]
    )

    if n > 3 and abs(r) < 1:

        z = np.arctanh(r)

        se = 1 / np.sqrt(n - 3)

        z_low = z - 1.96 * se
        z_high = z + 1.96 * se

        ci_low = np.tanh(z_low)
        ci_high = np.tanh(z_high)

    else:

        ci_low = np.nan
        ci_high = np.nan


    return {
        "tipo": tipo,
        "predictor": x,
        "outcome": y,
        "N": n,
        "r": r,
        "IC95_low": ci_low,
        "IC95_high": ci_high,
        "p": p,
    }


def correlacion_spearman(data, x, y, tipo):
    """
    Correlación de Spearman, como sensibilidad para variables
    que no cumplen normalidad según Shapiro-Wilk.
    """
    from scipy.stats import spearmanr

    datos = data[[x, y]].dropna()
    n = len(datos)
    rho, p = spearmanr(datos[x], datos[y])

    return {
        "tipo": tipo,
        "predictor": x,
        "outcome": y,
        "N": n,
        "rho": rho,
        "p": p,
    }


# ============================================================
# 9. H3 PRINCIPAL — PANAS POSITIVO × BART
# ============================================================

resultados_pos = []

for outcome in OUTCOMES:
    resultado = correlacion_pearson(
        data=base,
        x="panas_pos_sum",
        y=outcome,
        tipo="H3_principal"
    )
    resultados_pos.append(resultado)

tabla_h3_principal = pd.DataFrame(resultados_pos)


# ============================================================
# 10. ANÁLISIS SECUNDARIO — PANAS NEGATIVO × BART
# ============================================================

resultados_neg = []

for outcome in OUTCOMES:
    resultado = correlacion_pearson(
        data=base,
        x="panas_neg_sum",
        y=outcome,
        tipo="Secundario_PANAS_negativo"
    )
    resultados_neg.append(resultado)

tabla_h3_negativo = pd.DataFrame(resultados_neg)


# ============================================================
# 11. SENSIBILIDAD — SPEARMAN PARA VARIABLES NO NORMALES
#
# Se corre para todo par predictor-outcome donde al menos una
# de las dos variables tiene shapiro_p < .05 en la sección 7.
# ============================================================

variables_no_normales = set(
    tabla_shapiro.loc[~tabla_shapiro["normal_al_5pct"], "variable"]
)

resultados_spearman = []

if variables_no_normales:
    print("\n")
    print("=" * 80)
    print("SENSIBILIDAD — SPEARMAN (variables que no cumplen normalidad)")
    print("=" * 80)
    print(f"Variables no normales: {sorted(variables_no_normales)}\n")

    for predictor in ["panas_pos_sum", "panas_neg_sum"]:
        for outcome in OUTCOMES:
            if predictor in variables_no_normales or outcome in variables_no_normales:
                resultado = correlacion_spearman(
                    data=base, x=predictor, y=outcome,
                    tipo="Sensibilidad_Spearman"
                )
                resultados_spearman.append(resultado)

tabla_h3_spearman = pd.DataFrame(resultados_spearman)

if not tabla_h3_spearman.empty:
    tabla_h3_spearman.to_csv(
        OUTPUT_DIR / "H3_spearman_sensibilidad.csv",
        index=False,
        encoding="utf-8-sig"
    )
    print(tabla_h3_spearman.round(4).to_string(index=False))
else:
    print("\nTodas las variables cumplen normalidad al 5% — no se requiere Spearman.\n")


# ============================================================
# 12. FUNCIÓN PARA REGRESIONES (con Breusch-Pagan)
# ============================================================

def extraer_modelo_ols(
    data,
    formula,
    outcome,
    modelo_nombre,
    termino_interes="panas_pos_sum"
):

    modelo = smf.ols(
        formula=formula,
        data=data
    ).fit()

    ic = modelo.conf_int().loc[
        termino_interes
    ]

    bp_stat, bp_p, _, _ = het_breuschpagan(
        modelo.resid, modelo.model.exog
    )

    return {
        "modelo": modelo_nombre,
        "outcome": outcome,
        "N": int(modelo.nobs),
        "B_PANAS_pos": modelo.params[termino_interes],
        "SE": modelo.bse[termino_interes],
        "t": modelo.tvalues[termino_interes],
        "p": modelo.pvalues[termino_interes],
        "IC95_low": ic.iloc[0],
        "IC95_high": ic.iloc[1],
        "R2": modelo.rsquared,
        "R2_ajustado": modelo.rsquared_adj,
        "breusch_pagan_stat": bp_stat,
        "breusch_pagan_p": bp_p,
        "homocedastico_al_5pct": bp_p >= 0.05,
    }


# ============================================================
# 13. EXTENSIÓN AJUSTADA POR GRUPO
#     BART ~ PANAS positivo + grupo
# ============================================================

resultados_ajustados = []

for outcome in OUTCOMES:
    formula = f"{outcome} ~ panas_pos_sum + grupo_code"
    resultado = extraer_modelo_ols(
        data=base,
        formula=formula,
        outcome=outcome,
        modelo_nombre="PANAS_pos + grupo"
    )
    resultados_ajustados.append(resultado)

tabla_h3_ajustada = pd.DataFrame(resultados_ajustados)


# ============================================================
# 14. SENSIBILIDAD
#     BART ~ PANAS positivo + PANAS negativo + grupo
# ============================================================

resultados_sensibilidad = []

for outcome in OUTCOMES:
    formula = f"{outcome} ~ panas_pos_sum + panas_neg_sum + grupo_code"
    resultado = extraer_modelo_ols(
        data=base,
        formula=formula,
        outcome=outcome,
        modelo_nombre="PANAS_pos + PANAS_neg + grupo"
    )
    resultados_sensibilidad.append(resultado)

tabla_h3_sensibilidad = pd.DataFrame(resultados_sensibilidad)


# ============================================================
# 15. EXTENSIÓN AJUSTADA POR GRUPO + SEXO + EDAD
# ============================================================

resultados_ajustados_completos = []

for outcome in OUTCOMES:
    formula = (
        f"{outcome} ~ panas_pos_sum + grupo_code + "
        "genero_code + edad_std_intragrupo"
    )
    resultado = extraer_modelo_ols(
        data=base,
        formula=formula,
        outcome=outcome,
        modelo_nombre="PANAS_pos + grupo + sexo + edad_std"
    )
    resultados_ajustados_completos.append(resultado)

tabla_h3_ajustada_completa = pd.DataFrame(resultados_ajustados_completos)


# ============================================================
# 16. REDONDEAR PARA PRESENTACIÓN
# ============================================================

def redondear_tabla(df):
    df = df.copy()
    columnas_numericas = df.select_dtypes(include=[np.number]).columns
    df[columnas_numericas] = df[columnas_numericas].round(4)
    return df


tabla_h3_principal = redondear_tabla(tabla_h3_principal)
tabla_h3_negativo = redondear_tabla(tabla_h3_negativo)
tabla_h3_ajustada = redondear_tabla(tabla_h3_ajustada)
tabla_h3_sensibilidad = redondear_tabla(tabla_h3_sensibilidad)
tabla_h3_ajustada_completa = redondear_tabla(tabla_h3_ajustada_completa)


# ============================================================
# 17. GUARDAR CSV
# ============================================================

tabla_h3_principal.to_csv(
    OUTPUT_DIR / "H3_correlaciones_PANAS_positivo_BART.csv",
    index=False, encoding="utf-8-sig"
)

tabla_h3_negativo.to_csv(
    OUTPUT_DIR / "H3_correlaciones_PANAS_negativo_BART.csv",
    index=False, encoding="utf-8-sig"
)

tabla_h3_ajustada.to_csv(
    OUTPUT_DIR / "H3_regresiones_ajustadas_grupo.csv",
    index=False, encoding="utf-8-sig"
)

tabla_h3_sensibilidad.to_csv(
    OUTPUT_DIR / "H3_sensibilidad_PANAS_pos_neg_grupo.csv",
    index=False, encoding="utf-8-sig"
)

tabla_h3_ajustada_completa.to_csv(
    OUTPUT_DIR / "H3_regresiones_ajustadas_grupo_sexo_edad.csv",
    index=False, encoding="utf-8-sig"
)


# ============================================================
# 18. MOSTRAR RESULTADOS EN CONSOLA
# ============================================================

print("\n")
print("=" * 80)
print("H3 PRINCIPAL — PANAS POSITIVO × BART")
print("=" * 80)
print(tabla_h3_principal.to_string(index=False))

print("\n")
print("=" * 80)
print("ANÁLISIS SECUNDARIO — PANAS NEGATIVO × BART")
print("=" * 80)
print(tabla_h3_negativo.to_string(index=False))

print("\n")
print("=" * 80)
print("H3 — REGRESIONES AJUSTADAS POR GRUPO (con Breusch-Pagan)")
print("=" * 80)
print(tabla_h3_ajustada.to_string(index=False))

print("\n")
print("=" * 80)
print("H3 — SENSIBILIDAD: POSITIVO + NEGATIVO + GRUPO (con Breusch-Pagan)")
print("=" * 80)
print(tabla_h3_sensibilidad.to_string(index=False))

print("\n")
print("=" * 80)
print("H3 — EXTENSIÓN: PANAS POSITIVO + GRUPO + SEXO + EDAD_STD (con Breusch-Pagan)")
print("=" * 80)
print(tabla_h3_ajustada_completa.to_string(index=False))

print("\nSi homocedastico_al_5pct es False en alguna fila, los SE/p de esa fila")
print("no son confiables bajo el supuesto de varianza constante -- revisar antes")
print("de reportar (opciones: errores robustos HC3, o transformar el outcome).\n")


# ============================================================
# 19. RESUMEN FINAL
# ============================================================

print("\n")
print("=" * 80)
print("H3 FINALIZADA")
print("=" * 80)

print(f"\nFuente: {INPUT_PATH}")
print(f"N: {len(base)}")
print(f"Outputs: {OUTPUT_DIR}")