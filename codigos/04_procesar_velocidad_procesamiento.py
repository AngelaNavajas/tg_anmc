#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_procesar_velocidad_procesamiento.py

"""

from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path("/Users/angelanavajas/Desktop/anmc/analisis")
CLEAN_DIR = PROJECT_ROOT / "datos" / "limpios"
OUTPUTS_QC = PROJECT_ROOT / "outputs" / "control_calidad"
OUTPUTS_QC.mkdir(parents=True, exist_ok=True)

TRIALS_FILE = CLEAN_DIR / "processing_speed_trials_clean.csv"
INCLUIDOS_FILE = CLEAN_DIR / "participantes_incluidos.csv"
OUTPUT_FILE = CLEAN_DIR / "processing_speed_final.csv"

TASKS = ["SRT_TEST", "CRT_TEST", "DIGIT_SYMBOL"]
TASK_TO_MEDIAN = {"SRT_TEST": "median_srt", "CRT_TEST": "median_crt", "DIGIT_SYMBOL": "median_ds"}

RT_MIN = 100  # sin cutoff superior — ver nota en Método sobre esta decisión

ID_PARTICIPANTE_6 = "6"
ID_NO_INCLUIDOS_H2_SPEED = ["4"]

GROUP_COL = "grupo"
YOUNG_LABEL = "joven"

INDICATORS = {"median_srt": "z_srt", "median_crt": "z_crt", "median_ds": "z_digit_symbol"}


# ============================================================
# 1. CARGAR TRIALS Y PARTICIPANTES INCLUIDOS
# ============================================================

trials = pd.read_csv(TRIALS_FILE, dtype={"participant_id": str})
trials["participant_id"] = trials["participant_id"].str.strip()
trials["rt_ms"] = pd.to_numeric(trials["rt_ms"], errors="coerce")

incluidos = pd.read_csv(INCLUIDOS_FILE, dtype={"record_id": str})
incluidos["record_id"] = incluidos["record_id"].str.strip()
base_ids = (
    incluidos[["record_id", GROUP_COL]]
    .drop_duplicates(subset="record_id")
    .rename(columns={"record_id": "participant_id"})
)
ids_incluidos = set(base_ids["participant_id"])

trials = trials.loc[trials["participant_id"].isin(ids_incluidos)].copy()


# ============================================================
# 2. CORRECCIÓN DE RESPUESTAS — PARTICIPANTE 6
# ============================================================

trials["correct_answer_clean"] = trials["correct_answer"].astype("string").str.strip()
trials["response_clean"] = trials["response"].astype("string").str.strip()

mask_id6_crt = (
    (trials["participant_id"] == ID_PARTICIPANTE_6)
    & (trials["task"].isin(["CRT_TEST", "CRT_PRACTICE"]))
)

sub_id6 = trials.loc[mask_id6_crt, ["correct_answer_clean", "response_clean"]].dropna()

mapping_inversion = (
    sub_id6.groupby("correct_answer_clean")["response_clean"]
    .agg(lambda x: x.value_counts().idxmax())
    .to_dict()
)
mapping_correccion = {v: k for k, v in mapping_inversion.items()}

print("=" * 70)
print(f"CORRECCIÓN DE RESPUESTAS — PARTICIPANTE {ID_PARTICIPANTE_6}")
print("=" * 70)
print(f"Mapping de inversión inferido: {mapping_inversion}")
print(f"Mapping de corrección aplicado: {mapping_correccion}")

if len(mapping_correccion) != 2:
    raise ValueError(
        "El mapping de corrección no tiene exactamente 2 categorías. "
        "Revisar manualmente — puede haber más de dos teclas de respuesta posibles."
    )

trials["response_corregida"] = trials["response_clean"]
trials.loc[mask_id6_crt, "response_corregida"] = (
    trials.loc[mask_id6_crt, "response_clean"].map(mapping_correccion)
)

acc_antes = (
    trials.loc[mask_id6_crt & (trials["task"] == "CRT_TEST")]
    .eval("correct_answer_clean == response_clean").mean()
)
acc_despues = (
    trials.loc[mask_id6_crt & (trials["task"] == "CRT_TEST")]
    .assign(correcto=lambda d: d["correct_answer_clean"] == d["response_corregida"])
    ["correcto"].mean()
)

print(f"Exactitud CRT_TEST antes de la corrección:   {acc_antes:.3f}")
print(f"Exactitud CRT_TEST después de la corrección: {acc_despues:.3f}")

if acc_despues < 0.80:
    raise ValueError(
        "La corrección no elevó la exactitud por encima de .80. "
        "El patrón puede no ser una inversión simple de dos teclas."
    )

# A partir de acá, "response_corregida" reemplaza a "response" para
# todo el resto del pipeline (afecta únicamente al participante 6;
# para el resto de la muestra, response_corregida == response_clean).
trials["correct"] = trials["correct_answer_clean"] == trials["response_corregida"]

pd.DataFrame([{
    "participant_id": ID_PARTICIPANTE_6,
    "mapping_inversion": str(mapping_inversion),
    "mapping_correccion": str(mapping_correccion),
    "accuracy_antes": round(acc_antes, 4),
    "accuracy_despues": round(acc_despues, 4),
}]).to_csv(OUTPUTS_QC / "control_correccion_id6.csv", index=False)


# ============================================================
# 3. MEDIANA DE RT POR PARTICIPANTE Y TAREA
#
# Filtro: ensayos correctos (ya con ID6 corregido) y RT >= 100ms.
# Sin cutoff superior — la mediana es robusta a RT largos aislados.
# ============================================================

ps = trials.loc[trials["task"].isin(TASKS)].copy()
n_task_trials = len(ps)

ps = ps.loc[ps["correct"]].copy()
n_correct = len(ps)

ps = ps.loc[ps["rt_ms"].notna() & np.isfinite(ps["rt_ms"]) & (ps["rt_ms"] >= RT_MIN)].copy()
n_final = len(ps)

print("\n" + "=" * 70)
print("FILTROS PARA CÁLCULO DE MEDIANA")
print("=" * 70)
print(f"Trials en tareas TEST / participantes incluidos: {n_task_trials}")
print(f"Trials correctos (post-corrección ID6):          {n_correct}")
print(f"Trials correctos con RT >= {RT_MIN} ms:            {n_final}")
print("Cutoff superior aplicado:                        NINGUNO")

medianas_long = (
    ps.groupby(["participant_id", "task"], as_index=False)
    .agg(median_rt=("rt_ms", "median"), n_valid=("rt_ms", "count"))
)

medianas_wide = (
    medianas_long.pivot(index="participant_id", columns="task", values="median_rt")
    .rename(columns=TASK_TO_MEDIAN)
    .reset_index()
)
medianas_wide.columns.name = None

df = base_ids.merge(medianas_wide, on="participant_id", how="left")

faltantes = df[df[list(TASK_TO_MEDIAN.values())].isna().any(axis=1)]
if not faltantes.empty:
    raise ValueError(
        f"Hay valores faltantes en median_srt/median_crt/median_ds para: "
        f"{faltantes['participant_id'].tolist()}"
    )


# ============================================================
# 4. Z-SCORES RESPECTO DE JÓVENES + COMPOSITE
# ============================================================

reference_rows = []

for raw_col, z_col in INDICATORS.items():
    young_values = df.loc[df[GROUP_COL] == YOUNG_LABEL, raw_col]
    young_mean = young_values.mean()
    young_sd = young_values.std(ddof=1)

    if pd.isna(young_sd) or young_sd <= 0:
        raise ValueError(f"SD joven inválida para {raw_col}: {young_sd}")

    z_raw = (df[raw_col] - young_mean) / young_sd
    df[z_col] = -z_raw  # invertir: mayor score = mayor velocidad

    reference_rows.append({"indicator": raw_col, "young_mean": young_mean, "young_sd": young_sd})

z_cols = list(INDICATORS.values())
df["processing_speed"] = df[z_cols].mean(axis=1)


# ============================================================
# 5. COLUMNA DE VALIDEZ (incluido_h2_speed)
#
# Se mantienen los 74 participantes. Se marca 0 únicamente para
# el participante 4 (accuracy=.50, rendimiento a nivel de azar,
# sin patrón de inversión). El participante 6 ya está incluido
# con sus respuestas corregidas.
# ============================================================

incluido_bool = ~df["participant_id"].isin(ID_NO_INCLUIDOS_H2_SPEED)
df["incluido_h2_speed"] = incluido_bool.astype(int)  # 0/1 explícito, no booleano (compatibilidad con R)


# ============================================================
# 6. GUARDAR Y REPORTAR
# ============================================================

output_cols = ["participant_id", GROUP_COL, "median_srt", "median_crt", "median_ds",
               "z_srt", "z_crt", "z_digit_symbol", "processing_speed", "incluido_h2_speed"]

df[output_cols].to_csv(OUTPUT_FILE, index=False)

print("\n" + "=" * 70)
print("PROCESSING SPEED FINAL")
print("=" * 70)
print("\nReferencia de estandarización (grupo joven):")
print(pd.DataFrame(reference_rows).round(4).to_string(index=False))

print("\nDescriptivos del composite (TODOS, N=74):")
print(df.groupby(GROUP_COL)["processing_speed"].agg(["count", "mean", "std", "median", "min", "max"]).round(4).to_string())

print("\nDescriptivos del composite (solo incluido_h2_speed=1):")
print(df.loc[incluido_bool].groupby(GROUP_COL)["processing_speed"]
      .agg(["count", "mean", "std", "median", "min", "max"]).round(4).to_string())

print("\nParticipantes NO incluidos en H2 (processing speed):")
print(df.loc[~incluido_bool, ["participant_id", GROUP_COL, "median_crt", "processing_speed"]])

print("\nCorrelaciones entre los tres z-scores:")
print(df[z_cols].corr().round(4).to_string())

print(f"\nGuardado: {OUTPUT_FILE}")
print(f"Auditoría de corrección ID6: {OUTPUTS_QC / 'control_correccion_id6.csv'}")
