#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_H1_descriptivas_y_diferencias.py

Cinco tablas:

    Tabla 1 — Características de los participantes (N=74)
    Tabla 2 — H1: diferencias de grupo en medidas BART (t de Student)
    Tabla 3 — Processing Speed por grupo (N=73, incluido_h2_speed=1)
    Tabla 4 — Correlaciones entre variables principales (N=73)
    Tabla 5 — H1: modelo lineal complementario (+sexo, +edad_std)

Y tres figuras:

    Figura 1 — Medidas de BART por grupo (Tabla 2)
    Figura 2 — HADS ansiedad/depresión por grupo
    Figura 3 — Processing Speed: SRT, CRT y Digit Symbol por grupo
              
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path("/Users/angelanavajas/Desktop/anmc")
CLEAN_DIR = PROJECT_ROOT / "datos" / "limpios"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "tablas_h1"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FIGURAS_DIR = OUTPUT_DIR / "figuras"
FIGURAS_DIR.mkdir(parents=True, exist_ok=True)

BASE_PATH = CLEAN_DIR / "base_maestra_final.csv"

OUTCOMES = ["adjusted_pumps", "total_money", "total_explosions"]
OUTCOME_LABELS = {"adjusted_pumps": "Adjusted pumps", "total_money": "Money earned",
                   "total_explosions": "Total explosions"}


# ============================================================
# CARGAR Y CODIFICAR
# ============================================================

base = pd.read_csv(BASE_PATH, dtype={"participant_id": str})

if len(base) != 74:
    raise ValueError(f"Se esperaban 74 participantes y hay {len(base)}.")

base["grupo_code"] = base["grupo"].map({"joven": 0, "mayor": 1})
if base["grupo_code"].isna().any():
    raise ValueError("Hay categorías de grupo que no pudieron codificarse.")

if not base["genero"].isin([1, 2]).all():
    raise ValueError("La variable genero contiene valores distintos de 1 y 2.")
base["genero_code"] = base["genero"].map({1: 0, 2: 1})

jovenes = base.loc[base["grupo"] == "joven"]
mayores = base.loc[base["grupo"] == "mayor"]

base_73 = base.loc[base["incluido_h2_speed"] == 1].copy()
jovenes_ps = base_73.loc[base_73["grupo"] == "joven"]
mayores_ps = base_73.loc[base_73["grupo"] == "mayor"]

print(f"Muestra general: N = {len(base)} ({len(jovenes)} jóvenes, {len(mayores)} mayores)")
print(f"Muestra Processing Speed: N = {len(base_73)} ({len(jovenes_ps)} jóvenes, {len(mayores_ps)} mayores)")


# ============================================================
# FUNCIÓN: COMPARACIÓN DE GRUPOS (t de Student, pooled)
# ============================================================

def comparar_grupos(joven, mayor):
    """
    Prueba t de Student para muestras independientes, varianzas
    agrupadas. Devuelve también Hedges g y eta cuadrado parcial.
    """
    joven = pd.to_numeric(pd.Series(joven), errors="coerce").dropna()
    mayor = pd.to_numeric(pd.Series(mayor), errors="coerce").dropna()

    n_joven, n_mayor = len(joven), len(mayor)
    df_pooled = n_joven + n_mayor - 2

    t_stat, p_value = stats.ttest_ind(mayor, joven, equal_var=True, alternative="two-sided")

    diferencia = mayor.mean() - joven.mean()
    pooled_var = ((n_joven - 1) * joven.var(ddof=1) + (n_mayor - 1) * mayor.var(ddof=1)) / df_pooled
    pooled_sd = np.sqrt(pooled_var)
    se_diff = pooled_sd * np.sqrt(1 / n_mayor + 1 / n_joven)
    t_crit = stats.t.ppf(0.975, df_pooled)

    cohen_d = diferencia / pooled_sd
    correction_factor = 1 - (3 / (4 * df_pooled - 1))
    hedges_g = cohen_d * correction_factor
    eta_p2 = t_stat**2 / (t_stat**2 + df_pooled)

    return {
        "n_joven": n_joven, "n_mayor": n_mayor,
        "media_joven": joven.mean(), "sd_joven": joven.std(ddof=1),
        "media_mayor": mayor.mean(), "sd_mayor": mayor.std(ddof=1),
        "diferencia": diferencia,
        "ci_low": diferencia - t_crit * se_diff, "ci_high": diferencia + t_crit * se_diff,
        "t": t_stat, "df": df_pooled, "p": p_value,
        "hedges_g": hedges_g, "eta_p2": eta_p2,
    }


# ============================================================
# TABLA 1 — CARACTERÍSTICAS DE LOS PARTICIPANTES
# ============================================================

def fila(variable, jov, may):
    return {"Variable": variable, "Jóvenes": jov, "Mayores": may}

tabla1_rows = [
    fila("N", len(jovenes), len(mayores)),
    fila("Edad, M (SD)", f"{jovenes['edad'].mean():.2f} ({jovenes['edad'].std():.2f})",
         f"{mayores['edad'].mean():.2f} ({mayores['edad'].std():.2f})"),
    fila("Edad, rango (min-max)", f"{jovenes['edad'].min():.0f}-{jovenes['edad'].max():.0f}",
         f"{mayores['edad'].min():.0f}-{mayores['edad'].max():.0f}"),
    fila("Años de educación, M (SD)",
         f"{jovenes['anos_educacion'].mean():.2f} ({jovenes['anos_educacion'].std():.2f})",
         f"{mayores['anos_educacion'].mean():.2f} ({mayores['anos_educacion'].std():.2f})"),
    fila("Género: 1, n (%)",
         f"{(jovenes['genero']==1).sum()} ({(jovenes['genero']==1).mean()*100:.1f}%)",
         f"{(mayores['genero']==1).sum()} ({(mayores['genero']==1).mean()*100:.1f}%)"),
    fila("Género: 2, n (%)",
         f"{(jovenes['genero']==2).sum()} ({(jovenes['genero']==2).mean()*100:.1f}%)",
         f"{(mayores['genero']==2).sum()} ({(mayores['genero']==2).mean()*100:.1f}%)"),
    fila("PANAS positivo, M (SD)",
         f"{jovenes['panas_pos_sum'].mean():.2f} ({jovenes['panas_pos_sum'].std():.2f})",
         f"{mayores['panas_pos_sum'].mean():.2f} ({mayores['panas_pos_sum'].std():.2f})"),
    fila("PANAS negativo, M (SD)",
         f"{jovenes['panas_neg_sum'].mean():.2f} ({jovenes['panas_neg_sum'].std():.2f})",
         f"{mayores['panas_neg_sum'].mean():.2f} ({mayores['panas_neg_sum'].std():.2f})"),
    fila("HADS ansiedad, M (SD)",
         f"{jovenes['hads_ansiedad_total'].mean():.2f} ({jovenes['hads_ansiedad_total'].std():.2f})",
         f"{mayores['hads_ansiedad_total'].mean():.2f} ({mayores['hads_ansiedad_total'].std():.2f})"),
    fila("HADS depresión, M (SD)",
         f"{jovenes['hads_depresion_total'].mean():.2f} ({jovenes['hads_depresion_total'].std():.2f})",
         f"{mayores['hads_depresion_total'].mean():.2f} ({mayores['hads_depresion_total'].std():.2f})"),
    fila("MoCA, M (SD)", "-", f"{mayores['moca'].mean():.2f} ({mayores['moca'].std():.2f})"),
    fila("Jubilados, n (%)", "-",
         f"{(mayores['jubilado']==1).sum()} ({(mayores['jubilado']==1).mean()*100:.1f}%)"),
    fila("Edad de jubilación, M (SD)", "-",
         f"{mayores['edad_jubilacion'].mean():.2f} ({mayores['edad_jubilacion'].std():.2f})"),
]

tabla1 = pd.DataFrame(tabla1_rows)
tabla1.to_csv(OUTPUT_DIR / "tabla1_descriptivas.csv", index=False)


# ============================================================
# TABLA 2 — H1: DIFERENCIAS DE GRUPO EN BART (N=74)
# ============================================================

filas_h1 = []
for outcome in OUTCOMES:
    r = comparar_grupos(jovenes[outcome], mayores[outcome])
    filas_h1.append({
        "Medida": OUTCOME_LABELS[outcome],
        "Jóvenes N": r["n_joven"], "Jóvenes M": round(r["media_joven"], 2), "Jóvenes SD": round(r["sd_joven"], 2),
        "Mayores N": r["n_mayor"], "Mayores M": round(r["media_mayor"], 2), "Mayores SD": round(r["sd_mayor"], 2),
        "Diferencia M-J": round(r["diferencia"], 2),
        "IC 95% diferencia": f"[{r['ci_low']:.2f}, {r['ci_high']:.2f}]",
        "t": round(r["t"], 2), "df": r["df"], "p": round(r["p"], 3),
        "Hedges g": round(r["hedges_g"], 2), "eta_p2": round(r["eta_p2"], 3),
    })

tabla2 = pd.DataFrame(filas_h1)
tabla2.to_csv(OUTPUT_DIR / "tabla2_h1_bart_por_grupo.csv", index=False)


# ============================================================
# TABLA 3 — PROCESSING SPEED POR GRUPO (N=73)
# ============================================================

PS_VARS = {"median_srt": "SRT mediana (ms)", "median_crt": "CRT mediana (ms)",
           "median_ds": "Digit Symbol mediana (ms)", "processing_speed": "Processing Speed (composite)"}

filas_ps = []
for var, label in PS_VARS.items():
    r = comparar_grupos(jovenes_ps[var], mayores_ps[var])
    filas_ps.append({
        "Medida": label,
        "Jóvenes N": r["n_joven"], "Jóvenes M": round(r["media_joven"], 2), "Jóvenes SD": round(r["sd_joven"], 2),
        "Mayores N": r["n_mayor"], "Mayores M": round(r["media_mayor"], 2), "Mayores SD": round(r["sd_mayor"], 2),
    })

tabla3 = pd.DataFrame(filas_ps)
tabla3.to_csv(OUTPUT_DIR / "tabla3_processing_speed_por_grupo.csv", index=False)


# ============================================================
# TABLA 4 — CORRELACIONES (N=73)
# ============================================================

corr_variables = [
    ("1. Grupo etario", "grupo_code"),
    ("2. Processing Speed", "processing_speed"),
    ("3. Adjusted pumps", "adjusted_pumps"),
    ("4. Money earned", "total_money"),
    ("5. Total explosions", "total_explosions"),
    ("6. PANAS positivo", "panas_pos_sum"),
    ("7. PANAS negativo", "panas_neg_sum"),
    ("8. Años de educación", "anos_educacion"),
    ("9. Edad std. intragrupo", "edad_std_intragrupo"),
]

n_vars = len(corr_variables)
r_mat = np.full((n_vars, n_vars), np.nan)
p_mat = np.full((n_vars, n_vars), np.nan)

for i, (_, v1) in enumerate(corr_variables):
    for j, (_, v2) in enumerate(corr_variables):
        if i == j:
            r_mat[i, j] = 1.0
        elif i > j:
            r, p = stats.pearsonr(base_73[v1], base_73[v2])
            r_mat[i, j] = r
            p_mat[i, j] = p

def stars(p):
    if pd.isna(p):
        return ""
    if p < .001:
        return "***"
    if p < .01:
        return "**"
    if p < .05:
        return "*"
    return ""

filas_corr = []
for i, (label, _) in enumerate(corr_variables):
    fila_dict = {"Variable": label}
    for j in range(n_vars):
        if j >= i:
            fila_dict[str(j + 1)] = "—" if j == i else ""
        else:
            fila_dict[str(j + 1)] = f"{r_mat[i, j]:.2f}{stars(p_mat[i, j])}"
    filas_corr.append(fila_dict)

tabla4 = pd.DataFrame(filas_corr)
tabla4.to_csv(OUTPUT_DIR / "tabla4_correlaciones.csv", index=False)


# ============================================================
# TABLA 5 — H1: MODELO LINEAL COMPLEMENTARIO (+sexo, +edad_std)
# ============================================================

resultados_lineal = []
for outcome in OUTCOMES:
    modelo = smf.ols(f"{outcome} ~ grupo_code + genero_code + edad_std_intragrupo", data=base).fit()
    ic = modelo.conf_int().loc["grupo_code"]
    resultados_lineal.append({
        "outcome": OUTCOME_LABELS[outcome], "N": int(modelo.nobs),
        "B_grupo": modelo.params["grupo_code"], "SE": modelo.bse["grupo_code"],
        "t": modelo.tvalues["grupo_code"], "df": int(modelo.df_resid), "p": modelo.pvalues["grupo_code"],
        "IC95_low": ic.iloc[0], "IC95_high": ic.iloc[1],
        "R2": modelo.rsquared, "R2_ajustado": modelo.rsquared_adj,
    })

tabla5 = pd.DataFrame(resultados_lineal)
cols_num = tabla5.select_dtypes(include=[np.number]).columns
tabla5[cols_num] = tabla5[cols_num].round(4)
tabla5.to_csv(OUTPUT_DIR / "tabla5_h1_modelo_lineal.csv", index=False)


# ============================================================
# FIGURAS — POR GRUPO
# ============================================================

COLOR_JOVEN = "#4C72B0"
COLOR_MAYOR = "#C44E52"


def boxplot_por_grupo(ax, variable, etiqueta):
    """Dibuja un boxplot de una variable por grupo (joven/mayor) en el eje dado."""
    datos = [jovenes[variable].dropna(), mayores[variable].dropna()]
    bp = ax.boxplot(
        datos, labels=["Jóvenes", "Mayores"], patch_artist=True, widths=0.5
    )
    for patch, color in zip(bp["boxes"], [COLOR_JOVEN, COLOR_MAYOR]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_title(etiqueta, fontsize=10.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def barra_media_ee_por_grupo(ax, variable, etiqueta, df_joven=None, df_mayor=None):
    """Dibuja una barra de media ± error estándar por grupo en el eje dado."""
    dj = (df_joven if df_joven is not None else jovenes)[variable].dropna()
    dm = (df_mayor if df_mayor is not None else mayores)[variable].dropna()

    medias = [dj.mean(), dm.mean()]
    errores = [dj.std(ddof=1) / np.sqrt(len(dj)), dm.std(ddof=1) / np.sqrt(len(dm))]

    ax.bar(
        ["Jóvenes", "Mayores"], medias, yerr=errores, capsize=5, width=0.55,
        color=[COLOR_JOVEN, COLOR_MAYOR], edgecolor="black", linewidth=0.8
    )
    ax.set_title(etiqueta, fontsize=10.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


#Figura 1: medidas de BART por grupo (barras, media ± EE) 

fig, axes = plt.subplots(1, 3, figsize=(10, 4))
barra_media_ee_por_grupo(axes[0], "adjusted_pumps", "Bombeos ajustados")
barra_media_ee_por_grupo(axes[1], "total_money", "Dinero total ganado")
barra_media_ee_por_grupo(axes[2], "total_explosions", "Explosiones totales")
axes[0].set_ylabel("Media (± EE)", fontsize=10)
fig.suptitle("Figura 1. Medidas de BART por grupo etario (N=74)", fontsize=12, y=1.03)
plt.tight_layout()
plt.savefig(FIGURAS_DIR / "figura1_bart_por_grupo.png", dpi=200, bbox_inches="tight")
plt.close(fig)


#Figura 2: HADS ansiedad/depresión por grupo 

fig, axes = plt.subplots(1, 2, figsize=(7, 4))
boxplot_por_grupo(axes[0], "hads_ansiedad_total", "HADS ansiedad")
boxplot_por_grupo(axes[1], "hads_depresion_total", "HADS depresión")
fig.suptitle("Figura 2. HADS por grupo etario (N=74)", fontsize=12, y=1.03)
plt.tight_layout()
plt.savefig(FIGURAS_DIR / "figura2_hads_por_grupo.png", dpi=200, bbox_inches="tight")
plt.close(fig)


#Figura 3: Processing Speed — solo los 3 componentes crudos por grupo
# (se excluye el composite del gráfico a pedido; sigue disponible en Tabla 3)
# N=73 (incluido_h2_speed=1) — usa jovenes_ps/mayores_ps, no jovenes/mayores.

def boxplot_por_grupo_ps(ax, variable, etiqueta):
    datos = [jovenes_ps[variable].dropna(), mayores_ps[variable].dropna()]
    bp = ax.boxplot(
        datos, labels=["Jóvenes", "Mayores"], patch_artist=True, widths=0.5
    )
    for patch, color in zip(bp["boxes"], [COLOR_JOVEN, COLOR_MAYOR]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_title(etiqueta, fontsize=10.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


fig, axes = plt.subplots(1, 3, figsize=(10, 4))
boxplot_por_grupo_ps(axes[0], "median_srt", "SRT (ms)")
boxplot_por_grupo_ps(axes[1], "median_crt", "CRT (ms)")
boxplot_por_grupo_ps(axes[2], "median_ds", "Digit Symbol (ms)")
fig.suptitle("Figura 3. Processing Speed por grupo etario (N=73)", fontsize=12, y=1.03)
plt.tight_layout()
plt.savefig(FIGURAS_DIR / "figura3_processing_speed_por_grupo.png", dpi=200, bbox_inches="tight")
plt.close(fig)

print(f"\nFiguras guardadas en: {FIGURAS_DIR}")

print(f"\nTablas guardadas en: {OUTPUT_DIR}")