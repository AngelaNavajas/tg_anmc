#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_aplicar_exclusiones.py


Criterios de exclusión aplicados:
    - Participante con edad en zona intermedia (33-64 años)
    - Participante que no completó el procedimiento
    - MoCA < 25 (deterioro cognitivo incompatible con la tarea)
"""

from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path("/Users/angelanavajas/Desktop/anmc")
RAW_DIR = PROJECT_ROOT / "datos" / "crudos" / "redcap"
CLEAN_DIR = PROJECT_ROOT / "datos" / "limpios"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

REDCAP_RAW_FILE = RAW_DIR / "TesisNavajasMcCormic_DATA_2026-06-29_1412.csv"

INCLUIDOS_OUT = CLEAN_DIR / "participantes_incluidos.csv"
EXCLUSIONES_OUT = CLEAN_DIR / "exclusiones_log.csv"
DEMOGRAFICOS_OUT = CLEAN_DIR / "demograficos_limpios.csv"

JOVEN_MIN, JOVEN_MAX = 18, 32
ADULTO_MIN, ADULTO_MAX = 65, 81

EXCLUIR_PROCEDIMIENTO = ["72"]
EXCLUIR_EDAD = ["20"]
MOCA_CUTOFF = 25  # excluye MoCA < 25 (MoCA = 25 se incluye)


def clasificar_grupo(edad):
    try:
        edad = float(edad)
    except (TypeError, ValueError):
        return None
    if JOVEN_MIN <= edad <= JOVEN_MAX:
        return "joven"
    elif ADULTO_MIN <= edad <= ADULTO_MAX:
        return "mayor"
    return "intermedio"


# ============================================================
# 1. APLICAR EXCLUSIONES
# ============================================================

print("=" * 70)
print("PASO 1 — EXCLUSIONES")
print("=" * 70)

redcap = pd.read_csv(REDCAP_RAW_FILE, dtype={"record_id": str})
redcap["record_id"] = redcap["record_id"].str.strip()
redcap["moca"] = pd.to_numeric(redcap["moca"], errors="coerce")
redcap["grupo"] = redcap["edad"].apply(clasificar_grupo)

exclusiones = []
for pid in EXCLUIR_PROCEDIMIENTO:
    exclusiones.append({"record_id": pid, "motivo": "no_completo_procedimiento",
                         "detalle": "No completó el experimento"})
for pid in EXCLUIR_EDAD:
    edad = redcap.loc[redcap["record_id"] == pid, "edad"].values
    edad = edad[0] if len(edad) else "?"
    exclusiones.append({"record_id": pid, "motivo": "edad_zona_intermedia",
                         "detalle": f"Edad {edad}, fuera de ambos grupos (18-32 / 65-81)"})

moca_excluidos = redcap.loc[redcap["moca"] < MOCA_CUTOFF, "record_id"].tolist()
for pid in moca_excluidos:
    moca_val = redcap.loc[redcap["record_id"] == pid, "moca"].values[0]
    exclusiones.append({"record_id": pid, "motivo": "moca_insuficiente",
                         "detalle": f"MoCA = {moca_val} (criterio: < {MOCA_CUTOFF})"})

excluidos_ids = set(EXCLUIR_PROCEDIMIENTO + EXCLUIR_EDAD + moca_excluidos)

incluidos = redcap.loc[~redcap["record_id"].isin(excluidos_ids)].copy()
incluidos = incluidos.loc[incluidos["grupo"].isin(["joven", "mayor"])]

cols_incluidos = [
    "record_id", "edad", "grupo", "genero", "moca",
    "a_edu", "mano", "ant_neuro", "trab_bin", "a_trab",
    "jubilado", "edad_jub", "act_jub", "h_act_jub", "h_ocu",
]
cols_presentes = [c for c in cols_incluidos if c in incluidos.columns]
incluidos = incluidos[cols_presentes].sort_values(
    "record_id", key=lambda x: x.astype(int)
).reset_index(drop=True)

excl_df = pd.DataFrame(exclusiones).sort_values(
    "record_id", key=lambda x: x.astype(int)
).reset_index(drop=True)

print(f"Participantes originales:      {len(redcap)}")
print(f"Total excluidos:                {len(excluidos_ids)}")
print(f"Participantes incluidos:        {len(incluidos)}")
print("\nPor grupo:")
print(incluidos["grupo"].value_counts().to_string())
print("\nNOTA: criterio de HADS pendiente de decisión de mentores "
      "(no aplicado como exclusión en esta versión).")

incluidos.to_csv(INCLUIDOS_OUT, index=False)
excl_df.to_csv(EXCLUSIONES_OUT, index=False)
print(f"\nGuardado: {INCLUIDOS_OUT}")
print(f"Guardado: {EXCLUSIONES_OUT}")


# ============================================================
# 2. VARIABLES DE ACTIVIDAD LABORAL (solo adultos mayores)
# ============================================================

print("\n" + "=" * 70)
print("PASO 2 — VARIABLES DE ACTIVIDAD LABORAL (adultos mayores)")
print("=" * 70)

for col in ["jubilado", "act_jub", "h_act_jub", "h_ocu"]:
    incluidos[col] = pd.to_numeric(incluidos[col], errors="coerce")

incluidos["horas_actividad_semanal"] = np.nan
incluidos["tipo_actividad"] = None

mayores = incluidos["grupo"] == "mayor"
mask_jub_inactivo = mayores & (incluidos["jubilado"] == 1) & (incluidos["act_jub"] == 0)
mask_jub_activo = mayores & (incluidos["jubilado"] == 1) & (incluidos["act_jub"] == 1)
mask_no_jub = mayores & (incluidos["jubilado"] == 0)

incluidos.loc[mask_jub_inactivo, "horas_actividad_semanal"] = 0.0
incluidos.loc[mask_jub_activo, "horas_actividad_semanal"] = incluidos.loc[mask_jub_activo, "h_act_jub"]
incluidos.loc[mask_no_jub, "horas_actividad_semanal"] = incluidos.loc[mask_no_jub, "h_ocu"]

incluidos.loc[mask_jub_inactivo, "tipo_actividad"] = "jubilado_inactivo"
incluidos.loc[mask_jub_activo, "tipo_actividad"] = "jubilado_activo"
incluidos.loc[mask_no_jub, "tipo_actividad"] = "no_jubilado"

print(incluidos.loc[mayores, "tipo_actividad"].value_counts().to_string())


# ============================================================
# 3. RENOMBRAR Y GUARDAR demograficos_limpios.csv
# ============================================================

demograficos = incluidos.rename(columns={
    "record_id": "participant_id",
    "a_edu": "anos_educacion",
    "mano": "mano_habil",
    "ant_neuro": "antecedente_neuro_psiq",
    "trab_bin": "trabajo_alguna_vez",
    "a_trab": "anos_trabajados",
    "edad_jub": "edad_jubilacion",
    "act_jub": "actividad_post_jubilacion",
    "h_act_jub": "horas_post_jubilacion",
})

demograficos.to_csv(DEMOGRAFICOS_OUT, index=False)
print(f"\nGuardado: {DEMOGRAFICOS_OUT}")
print(f"\nListo para 04_procesar_velocidad_procesamiento.py "
      f"(usa participant_id y grupo de este archivo).")
