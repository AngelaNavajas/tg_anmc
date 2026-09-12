#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 08:59:53 2026
@author: angelanavajas
"""
# ============================================================
# 31_H3_afecto_BART.py
#
# H3 — Afecto y comportamiento en BART
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
import statsmodels.formula.api as smf

# ============================================================
# 1. RUTAS
# ============================================================


PROJECT_ROOT = Path(
    "/Users/angelanavajas/Desktop/anmc"
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
    "genero",                 # NUEVO
    "edad_std_intragrupo",    # NUEVO
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

# 0 = joven
# 1 = mayor

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


# NUEVO — codificación de género, consistente con H1/H2:
# 1 = mujer -> 0
# 2 = varón -> 1

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
# 7. FUNCIÓN CORRELACIÓN PEARSON
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

    # IC95% de r mediante transformación z de Fisher

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

# ============================================================
# 8. H3 PRINCIPAL
#    PANAS POSITIVO × BART
# ============================================================

resultados_pos = []


for outcome in OUTCOMES:

    resultado = correlacion_pearson(
        data=base,
        x="panas_pos_sum",
        y=outcome,
        tipo="H3_principal"
    )

    resultados_pos.append(
        resultado
    )


tabla_h3_principal = pd.DataFrame(
    resultados_pos
)

# ============================================================
# 9. ANÁLISIS SECUNDARIO
#    PANAS NEGATIVO × BART
# ============================================================

resultados_neg = []


for outcome in OUTCOMES:

    resultado = correlacion_pearson(
        data=base,
        x="panas_neg_sum",
        y=outcome,
        tipo="Secundario_PANAS_negativo"
    )

    resultados_neg.append(
        resultado
    )


tabla_h3_negativo = pd.DataFrame(
    resultados_neg
)

# ============================================================
# 10. FUNCIÓN PARA REGRESIONES
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
    }

# ============================================================
# 11. EXTENSIÓN AJUSTADA POR GRUPO
#
# BART ~ PANAS positivo + grupo
# ============================================================

resultados_ajustados = []


for outcome in OUTCOMES:

    formula = (
        f"{outcome} ~ "
        "panas_pos_sum + "
        "grupo_code"
    )


    resultado = extraer_modelo_ols(
        data=base,
        formula=formula,
        outcome=outcome,
        modelo_nombre="PANAS_pos + grupo"
    )


    resultados_ajustados.append(
        resultado
    )


tabla_h3_ajustada = pd.DataFrame(
    resultados_ajustados
)

# ============================================================
# 12. SENSIBILIDAD
#
# BART ~ PANAS positivo + PANAS negativo + grupo
# ============================================================

resultados_sensibilidad = []


for outcome in OUTCOMES:

    formula = (
        f"{outcome} ~ "
        "panas_pos_sum + "
        "panas_neg_sum + "
        "grupo_code"
    )


    resultado = extraer_modelo_ols(
        data=base,
        formula=formula,
        outcome=outcome,
        modelo_nombre="PANAS_pos + PANAS_neg + grupo"
    )


    resultados_sensibilidad.append(
        resultado
    )


tabla_h3_sensibilidad = pd.DataFrame(
    resultados_sensibilidad
)

# ============================================================
# 12bis. NUEVO — EXTENSIÓN AJUSTADA POR GRUPO + SEXO + EDAD
# ============================================================


resultados_ajustados_completos = []


for outcome in OUTCOMES:

    formula = (
        f"{outcome} ~ "
        "panas_pos_sum + "
        "grupo_code + "
        "genero_code + "
        "edad_std_intragrupo"
    )

    resultado = extraer_modelo_ols(
        data=base,
        formula=formula,
        outcome=outcome,
        modelo_nombre="PANAS_pos + grupo + sexo + edad_std"
    )

    resultados_ajustados_completos.append(
        resultado
    )


tabla_h3_ajustada_completa = pd.DataFrame(
    resultados_ajustados_completos
)

# ============================================================
# 13. REDONDEAR PARA PRESENTACIÓN
# ============================================================

def redondear_tabla(df):

    df = df.copy()

    columnas_numericas = df.select_dtypes(
        include=[np.number]
    ).columns

    df[columnas_numericas] = (
        df[columnas_numericas]
        .round(4)
    )

    return df


tabla_h3_principal = redondear_tabla(
    tabla_h3_principal
)

tabla_h3_negativo = redondear_tabla(
    tabla_h3_negativo
)

tabla_h3_ajustada = redondear_tabla(
    tabla_h3_ajustada
)

tabla_h3_sensibilidad = redondear_tabla(
    tabla_h3_sensibilidad
)

tabla_h3_ajustada_completa = redondear_tabla(   # NUEVO
    tabla_h3_ajustada_completa
)

# ============================================================
# 14. GUARDAR CSV
# ============================================================

tabla_h3_principal.to_csv(
    OUTPUT_DIR / "H3_correlaciones_PANAS_positivo_BART.csv",
    index=False,
    encoding="utf-8-sig"
)


tabla_h3_negativo.to_csv(
    OUTPUT_DIR / "H3_correlaciones_PANAS_negativo_BART.csv",
    index=False,
    encoding="utf-8-sig"
)


tabla_h3_ajustada.to_csv(
    OUTPUT_DIR / "H3_regresiones_ajustadas_grupo.csv",
    index=False,
    encoding="utf-8-sig"
)


tabla_h3_sensibilidad.to_csv(
    OUTPUT_DIR / "H3_sensibilidad_PANAS_pos_neg_grupo.csv",
    index=False,
    encoding="utf-8-sig"
)


tabla_h3_ajustada_completa.to_csv(   # NUEVO
    OUTPUT_DIR / "H3_regresiones_ajustadas_grupo_sexo_edad.csv",
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 15. MOSTRAR RESULTADOS EN CONSOLA
# ============================================================

print("\n")
print("=" * 80)
print("H3 PRINCIPAL — PANAS POSITIVO × BART")
print("=" * 80)

print(
    tabla_h3_principal
    .to_string(index=False)
)


print("\n")
print("=" * 80)
print("ANÁLISIS SECUNDARIO — PANAS NEGATIVO × BART")
print("=" * 80)

print(
    tabla_h3_negativo
    .to_string(index=False)
)


print("\n")
print("=" * 80)
print("H3 — REGRESIONES AJUSTADAS POR GRUPO")
print("=" * 80)

print(
    tabla_h3_ajustada
    .to_string(index=False)
)


print("\n")
print("=" * 80)
print("H3 — SENSIBILIDAD: POSITIVO + NEGATIVO + GRUPO")
print("=" * 80)

print(
    tabla_h3_sensibilidad
    .to_string(index=False)
)


print("\n")   # NUEVO
print("=" * 80)
print("H3 — EXTENSIÓN: PANAS POSITIVO + GRUPO + SEXO + EDAD_STD")
print("=" * 80)

print(
    tabla_h3_ajustada_completa
    .to_string(index=False)
)


# ============================================================
# 16. RESUMEN FINAL
# ============================================================

print("\n")
print("=" * 80)
print("H3 FINALIZADA")
print("=" * 80)

print(f"\nFuente: {INPUT_PATH}")
print(f"N: {len(base)}")
print(f"Outputs: {OUTPUT_DIR}")
