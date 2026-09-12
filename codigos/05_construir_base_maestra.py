#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_construir_base_maestra.py

Arma la base maestra final a partir de los outputs de los scripts
anteriores y calcula edad_std_intragrupo.

"""

from pathlib import Path

import pandas as pd

# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path("/Users/angelanavajas/Desktop/anmc")
CLEAN_DIR = PROJECT_ROOT / "datos" / "limpios"

DEMOGRAFICOS_FILE = CLEAN_DIR / "demograficos_limpios.csv"
PROCESSING_SPEED_FILE = CLEAN_DIR / "processing_speed_final.csv"
BART_FILE = CLEAN_DIR / "bart_scores.csv"
HADS_FILE = CLEAN_DIR / "hads_scores.csv"
PANAS_FILE = CLEAN_DIR / "panas_scores.csv"

BASE_MAESTRA_OUT = CLEAN_DIR / "base_maestra_final.csv"


def verificar_ids_unicos(df, nombre_base):
    if "participant_id" not in df.columns:
        raise ValueError(f"{nombre_base}: falta la columna participant_id.")
    if df["participant_id"].isna().any():
        raise ValueError(f"{nombre_base}: hay participant_id faltantes.")
    if not df["participant_id"].is_unique:
        raise ValueError(f"{nombre_base}: hay participant_id duplicados.")


def verificar_cobertura(base_referencia, base_secundaria, nombre_base):
    faltantes = set(base_referencia["participant_id"]) - set(base_secundaria["participant_id"])
    if faltantes:
        raise ValueError(f"{nombre_base}: faltan participantes de la muestra analítica: {sorted(faltantes)}")


# ============================================================
# 1. CARGAR BASES
# ============================================================

print("=" * 70)
print("CONSTRUIR BASE MAESTRA")
print("=" * 70)

demograficos = pd.read_csv(DEMOGRAFICOS_FILE, dtype={"participant_id": str})
processing_speed = pd.read_csv(PROCESSING_SPEED_FILE, dtype={"participant_id": str})
bart = pd.read_csv(BART_FILE, dtype={"participant_id": str})
hads = pd.read_csv(HADS_FILE, dtype={"record_id": str}).rename(columns={"record_id": "participant_id"})
panas = pd.read_csv(PANAS_FILE, dtype={"participant_id": str})

for nombre, df in {
    "demograficos_limpios": demograficos,
    "processing_speed_final": processing_speed,
    "bart_scores": bart,
    "hads_scores": hads,
    "panas_scores": panas,
}.items():
    verificar_ids_unicos(df, nombre)

muestra = demograficos[["participant_id", "moca"]].copy()

for nombre, df in {
    "processing_speed_final": processing_speed,
    "bart_scores": bart,
    "hads_scores": hads,
    "panas_scores": panas,
}.items():
    verificar_cobertura(muestra, df, nombre)

# Control de consistencia de grupo entre demográficos y processing speed
control_grupo = demograficos[["participant_id", "grupo"]].merge(
    processing_speed[["participant_id", "grupo"]],
    on="participant_id", how="left", suffixes=("_demog", "_ps"), validate="one_to_one",
)
inconsistencias = control_grupo[control_grupo["grupo_demog"] != control_grupo["grupo_ps"]]
if not inconsistencias.empty:
    raise ValueError("Hay inconsistencias de grupo entre demograficos_limpios y processing_speed_final.")

processing_speed = processing_speed.drop(columns="grupo")
bart = bart[["participant_id", "adjusted_pumps", "total_money", "total_explosions", "explosion_rate"]]
hads = hads[["participant_id", "hads_ansiedad_total", "hads_depresion_total"]]
panas = panas[["participant_id", "panas_pos_sum", "panas_neg_sum"]]


# ============================================================
# 2. MERGE FINAL
# ============================================================

base_maestra = (
    muestra
    .merge(demograficos.drop(columns="moca"), on="participant_id", how="left", validate="one_to_one")
    .merge(processing_speed, on="participant_id", how="left", validate="one_to_one")
    .merge(bart, on="participant_id", how="left", validate="one_to_one")
    .merge(hads, on="participant_id", how="left", validate="one_to_one")
    .merge(panas, on="participant_id", how="left", validate="one_to_one")
)


# ============================================================
# 3. VARIABLE DERIVADA: EDAD ESTANDARIZADA INTRAGRUPO
# ============================================================

edad_media_grupo = base_maestra.groupby("grupo")["edad"].transform("mean")
edad_sd_grupo = base_maestra.groupby("grupo")["edad"].transform("std")
base_maestra["edad_std_intragrupo"] = (base_maestra["edad"] - edad_media_grupo) / edad_sd_grupo

verificacion_edad_std = base_maestra.groupby("grupo")["edad_std_intragrupo"].mean()
if (verificacion_edad_std.abs() > 1e-8).any():
    raise ValueError(f"edad_std_intragrupo no tiene media ~0 dentro de cada grupo:\n{verificacion_edad_std}")


# ============================================================
# 4. ORDENAR, VALIDAR Y GUARDAR
# ============================================================

orden_columnas = [
    "participant_id", "grupo", "edad", "edad_std_intragrupo", "genero",
    "anos_educacion", "mano_habil", "antecedente_neuro_psiq",
    "trabajo_alguna_vez", "anos_trabajados", "jubilado", "edad_jubilacion",
    "actividad_post_jubilacion", "horas_post_jubilacion",
    "horas_actividad_semanal", "tipo_actividad", "moca",
    "hads_ansiedad_total", "hads_depresion_total",
    "panas_pos_sum", "panas_neg_sum",
    "median_srt", "median_crt", "median_ds", "z_srt", "z_crt", "z_digit_symbol",
    "processing_speed", "incluido_h2_speed",
    "adjusted_pumps", "total_money", "total_explosions", "explosion_rate",
]
base_maestra = base_maestra[orden_columnas]

if len(base_maestra) != len(muestra):
    raise ValueError("El número de participantes cambió durante los merges.")
if not base_maestra["participant_id"].is_unique:
    raise ValueError("La base maestra contiene participant_id duplicados.")

variables_principales = ["edad", "edad_std_intragrupo", "genero", "anos_educacion",
                          "processing_speed", "adjusted_pumps"]
missing_principales = base_maestra[variables_principales].isna().sum()

print(f"\nN participantes: {len(base_maestra)}")
print(f"N variables: {len(base_maestra.columns)}")
print("\nPor grupo:")
print(base_maestra["grupo"].value_counts(dropna=False).to_string())
print("\nMissing en variables principales:")
print(missing_principales.to_string())
print("\nVerificación edad_std_intragrupo (media por grupo, debe ser ~0):")
print(verificacion_edad_std.to_string())
print("\nParticipantes NO incluidos en H2 (processing speed):")
print(base_maestra.loc[base_maestra["incluido_h2_speed"] == 0,
                        ["participant_id", "grupo", "processing_speed"]])

base_maestra.to_csv(BASE_MAESTRA_OUT, index=False)
print(f"\nGuardado: {BASE_MAESTRA_OUT}")
