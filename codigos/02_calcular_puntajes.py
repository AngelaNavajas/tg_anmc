#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  7 18:22:40 2026

@author: angelanavajas
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_calcular_puntajes.py

Cálculo de los tres instrumentos/tareas que no dependen
de la muestra analítica final: HADS, PANAS y BART. 
Cada uno se computa con todos los datos disponibles.

"""

from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================
# RUTAS — AJUSTAR el nombre del archivo REDCap crudo si cambió
# ============================================================

PROJECT_ROOT = Path("/Users/angelanavajas/Desktop/anmc")
RAW_DIR = PROJECT_ROOT / "datos" / "crudos" / "redcap"
CLEAN_DIR = PROJECT_ROOT / "datos" / "limpios"

REDCAP_RAW_FILE = RAW_DIR / "TesisNavajasMcCormic_DATA_2026-06-29_1412.csv"
PANAS_ITEMS_FILE = CLEAN_DIR / "panas_items_clean.csv"
BART_EVENTS_FILE = CLEAN_DIR / "bart_events_clean.csv"

HADS_OUT = CLEAN_DIR / "hads_scores.csv"
PANAS_OUT = CLEAN_DIR / "panas_scores.csv"
BART_OUT = CLEAN_DIR / "bart_scores.csv"

# ============================================================
# 1. HADS
# ============================================================
#
# Dirección de recodificación por ítem, según la adaptación al
# español de Serrano, Sorbara y Graviotto (2018):
#   "directa"   -> score = código - 1   (1->0, 2->1, 3->2, 4->3)
#   "invertida" -> score = 4 - código   (1->3, 2->2, 3->1, 4->0)


HADS_DIRECCION = {
    "ans1": "invertida", "dep1": "directa",
    "ans2": "invertida", "dep2": "directa",
    "ans3": "invertida", "dep3": "invertida",
    "ans4": "directa",   "dep4": "invertida",
    "ans5": "directa",   "dep5": "invertida",
    "ans6": "invertida", "dep6": "directa",
    "ans7": "invertida", "dep7": "directa",
}

ANSIEDAD_ITEMS = [c for c in HADS_DIRECCION if c.startswith("ans")]
DEPRESION_ITEMS = [c for c in HADS_DIRECCION if c.startswith("dep")]


def _recodificar_hads(serie, direccion, nombre_item):
    serie_num = pd.to_numeric(serie, errors="coerce")
    fuera_de_rango = serie_num[~serie_num.isin([1, 2, 3, 4]) & serie_num.notna()]
    if not fuera_de_rango.empty:
        print(f"AVISO [{nombre_item}]: valores fuera de {{1,2,3,4}}: {fuera_de_rango.tolist()}")
    if direccion == "directa":
        return serie_num - 1
    elif direccion == "invertida":
        return 4 - serie_num
    raise ValueError(f"Dirección desconocida: {direccion}")


def calcular_hads():
    print("=" * 70)
    print("HADS")
    print("=" * 70)

    df = pd.read_csv(REDCAP_RAW_FILE, dtype={"record_id": str})

    recodificados = {
        item: _recodificar_hads(df[item], direccion, item)
        for item, direccion in HADS_DIRECCION.items()
    }
    recod_df = pd.DataFrame(recodificados)

    df["hads_ansiedad_total"] = recod_df[ANSIEDAD_ITEMS].sum(axis=1, skipna=False)
    df["hads_depresion_total"] = recod_df[DEPRESION_ITEMS].sum(axis=1, skipna=False)

    for etiqueta, col in [("ANSIEDAD", "hads_ansiedad_total"), ("DEPRESIÓN", "hads_depresion_total")]:
        incompletos = df[df[col].isna()]
        if not incompletos.empty:
            print(f"AVISO: {len(incompletos)} participante(s) con al menos un ítem de "
                  f"{etiqueta} faltante -> {col} = NaN: {incompletos['record_id'].tolist()}")

    print("\nResumen hads_ansiedad_total:")
    print(df["hads_ansiedad_total"].describe())
    print("\nResumen hads_depresion_total:")
    print(df["hads_depresion_total"].describe())

    out_cols = ["record_id", "hads_ansiedad_total", "hads_depresion_total"]
    df[out_cols].to_csv(HADS_OUT, index=False)
    print(f"\nGuardado: {HADS_OUT}")


# ============================================================
# 2. PANAS
# ============================================================

PANAS_POS = [f"PA{i:02d}" for i in range(1, 11)]
PANAS_NEG = [f"NA{i:02d}" for i in range(1, 11)]


def calcular_panas():
    print("\n" + "=" * 70)
    print("PANAS")
    print("=" * 70)

    df = pd.read_csv(PANAS_ITEMS_FILE, dtype={"participant_id": str})
    df["response"] = pd.to_numeric(df["response"], errors="coerce")

    fuera = df[~df["response"].isin([1, 2, 3, 4, 5]) & df["response"].notna()]
    if not fuera.empty:
        print(f"AVISO: {len(fuera)} respuestas fuera del rango 1-5.")

    fases = df["phase"].unique()
    print(f"Fases encontradas: {fases}")

    sesiones_por_p = df.groupby("participant_id")["session_id"].nunique()
    multi = sesiones_por_p[sesiones_por_p > 1]
    if not multi.empty:
        print(f"\nParticipantes con más de una sesión en panas_items:\n{multi}")

    pos = (df[df["item_id"].isin(PANAS_POS)]
           .groupby(["participant_id", "session_id"])["response"]
           .sum(min_count=10).rename("panas_pos_sum"))
    neg = (df[df["item_id"].isin(PANAS_NEG)]
           .groupby(["participant_id", "session_id"])["response"]
           .sum(min_count=10).rename("panas_neg_sum"))

    scores = pd.concat([pos, neg], axis=1).reset_index()
    scores["panas_pos_sum"] = scores["panas_pos_sum"].astype("Int64")
    scores["panas_neg_sum"] = scores["panas_neg_sum"].astype("Int64")

    for col in ["panas_pos_sum", "panas_neg_sum"]:
        fuera_rango = scores[(scores[col] < 10) | (scores[col] > 50)]
        if not fuera_rango.empty:
            print(f"\nAVISO: puntajes fuera de rango 10-50 en {col}.")
        nan_ids = scores[scores[col].isna()]["participant_id"].tolist()
        if nan_ids:
            print(f"\nAVISO: {col} = NaN (ítems faltantes) para: {nan_ids}")

    print("\nResumen panas_pos_sum:")
    print(scores["panas_pos_sum"].describe())
    print("\nResumen panas_neg_sum:")
    print(scores["panas_neg_sum"].describe())

    scores.to_csv(PANAS_OUT, index=False)
    print(f"\nGuardado: {PANAS_OUT} ({len(scores)} filas)")


# ============================================================
# 3. BART
# ============================================================

EXPECTED_TOTAL = 30
PUMP_VALUE = 0.05


def calcular_bart():
    print("\n" + "=" * 70)
    print("BART")
    print("=" * 70)

    df = pd.read_csv(BART_EVENTS_FILE, dtype={"participant_id": str})
    df["participant_id"] = df["participant_id"].str.strip()
    df["pump_number"] = pd.to_numeric(df["pump_number"], errors="coerce")

    fases = df["phase"].unique()
    if not (len(fases) == 1 and fases[0] == "bart"):
        print(f"AVISO: fases inesperadas en bart_events: {fases}")

    # --------------------------------------------------------------
    # CONTROL DE SESIONES MÚLTIPLES
    # --------------------------------------------------------------

    sesiones_por_participante = df.groupby("participant_id")["session_id"].nunique()
    multi_sesion = sesiones_por_participante[sesiones_por_participante > 1].index.tolist()

    if multi_sesion:
        print(f"\nAVISO: {len(multi_sesion)} participante(s) con más de una sesión de BART: "
              f"{multi_sesion}")
        print("Se conserva únicamente la sesión con 30 globos completos (1-30, sin duplicados) "
              "por participante; las sesiones parciales se descartan.")

        outcomes_temp = df[df["event_type"].isin(["cashout", "explosion"])]

        resumen_sesion = (
            outcomes_temp.groupby(["participant_id", "session_id"])
            .agg(n_globos=("balloon_index", "size"),
                 idx_min=("balloon_index", "min"),
                 idx_max=("balloon_index", "max"),
                 duplicados=("balloon_index", lambda x: x.duplicated().sum()))
            .reset_index()
        )

        sesion_valida = resumen_sesion[
            (resumen_sesion["n_globos"] == EXPECTED_TOTAL)
            & (resumen_sesion["idx_min"] == 1)
            & (resumen_sesion["idx_max"] == EXPECTED_TOTAL)
            & (resumen_sesion["duplicados"] == 0)
        ]

        for pid in multi_sesion:
            candidatas = sesion_valida.loc[sesion_valida["participant_id"] == pid]
            if len(candidatas) != 1:
                raise ValueError(
                    f"Participante {pid}: no se encontró exactamente una sesión válida "
                    f"(30 globos, 1-30, sin duplicados). Candidatas encontradas: {len(candidatas)}. "
                    "Revisar manualmente antes de continuar — no se resuelve automáticamente."
                )

        session_valida_map = sesion_valida.set_index("participant_id")["session_id"].to_dict()

        mask_mantener = ~df["participant_id"].isin(multi_sesion) | (
            df.apply(lambda row: session_valida_map.get(row["participant_id"]) == row["session_id"], axis=1)
        )
        df = df.loc[mask_mantener].copy()

        print("Sesión conservada para participantes con reinicio:")
        for pid in multi_sesion:
            print(f"  Participante {pid}: {session_valida_map[pid]}")

    # --------------------------------------------------------------
    # RECLASIFICACIÓN DE GLOBOS SIN DESENLACE REGISTRADO
    #
    # Se reclasifican los globos que explotaron por tiempo
    # como explosión, usando el último pump_number registrado antes
    # del balloon_end (o 0 si no llegó a bombear).
    # --------------------------------------------------------------

    balloon_end = df[df["event_type"] == "balloon_end"][["participant_id", "balloon_index"]]
    tiene_outcome = df[df["event_type"].isin(["cashout", "explosion"])][["participant_id", "balloon_index"]]

    sin_outcome = balloon_end.merge(
        tiene_outcome, on=["participant_id", "balloon_index"], how="left", indicator=True
    )
    sin_outcome = sin_outcome[sin_outcome["_merge"] == "left_only"][["participant_id", "balloon_index"]]

    if not sin_outcome.empty:
        print(f"\nAVISO: {len(sin_outcome)} globo(s) con balloon_end pero sin cashout/explosion "
              f"registrado — reclasificando como explosión (timeout no logueado):")

        filas_reclasificadas = []
        for _, fila in sin_outcome.iterrows():
            pid, idx = fila["participant_id"], fila["balloon_index"]
            pumps_previos = df[
                (df["participant_id"] == pid) & (df["balloon_index"] == idx)
                & (df["event_type"] == "pump")
            ]["pump_number"]
            ultimo_pump = pumps_previos.max() if not pumps_previos.empty else 0
            print(f"  Participante {pid}, globo {idx}: último pump_number={ultimo_pump} -> explosion")

            filas_reclasificadas.append({
                "participant_id": pid, "session_id": df.loc[
                    (df["participant_id"] == pid) & (df["balloon_index"] == idx), "session_id"
                ].iloc[0],
                "phase": "bart", "balloon_index": idx, "event_type": "explosion",
                "event_index": -1, "timestamp": pd.NA, "rt_ms": pd.NA,
                "pump_number": ultimo_pump,
            })

        df = pd.concat([df, pd.DataFrame(filas_reclasificadas)], ignore_index=True)

    outcomes = (
        df[df["event_type"].isin(["cashout", "explosion"])]
        .copy()[["participant_id", "balloon_index", "event_type", "pump_number"]]
        .rename(columns={"event_type": "outcome"})
    )

    counts = (
        outcomes.groupby("participant_id")
        .agg(n_cashout=("outcome", lambda x: (x == "cashout").sum()),
             n_explosion=("outcome", lambda x: (x == "explosion").sum()))
        .reset_index()
    )
    counts["n_total"] = counts["n_cashout"] + counts["n_explosion"]

    desvios = counts[counts["n_total"] != EXPECTED_TOTAL]
    if not desvios.empty:
        print(f"\nAVISO: {len(desvios)} participante(s) siguen sin exactamente "
              f"{EXPECTED_TOTAL} globos con outcome tras la reclasificación:")
        print(desvios.to_string(index=False))
        if (desvios["n_total"] < EXPECTED_TOTAL - 2).any():
            raise ValueError(
                "Hay participante(s) con más de 2 globos faltantes — esto excede "
                "lo esperable por una falla puntual de logging. Revisar manualmente."
            )
        OUTPUTS_QC = PROJECT_ROOT / "outputs" / "control_calidad"
        OUTPUTS_QC.mkdir(parents=True, exist_ok=True)
        desvios.to_csv(OUTPUTS_QC / "control_bart_globos_faltantes.csv", index=False)
    else:
        print(f"Verificación OK: todos los participantes tienen exactamente "
              f"{EXPECTED_TOTAL} globos con outcome.")

    cashout = outcomes[outcomes["outcome"] == "cashout"]

    adjusted_pumps = cashout.groupby("participant_id")["pump_number"].mean().rename("adjusted_pumps").round(4)
    total_money = (cashout.groupby("participant_id")["pump_number"].sum()
                   .mul(PUMP_VALUE).rename("total_money").round(4))
    total_explosions = counts.set_index("participant_id")["n_explosion"].rename("total_explosions")

    scores = pd.concat([adjusted_pumps, total_money, total_explosions], axis=1).reset_index()
    scores["explosion_rate"] = (scores["total_explosions"] / EXPECTED_TOTAL).round(4)
    scores = scores.sort_values("participant_id", key=lambda x: x.astype(int)).reset_index(drop=True)

    print("\n--- Resumen estadístico ---")
    print(scores.drop(columns="participant_id").describe().round(3).to_string())

    scores.to_csv(BART_OUT, index=False)
    print(f"\nGuardado: {BART_OUT} ({len(scores)} filas)")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    calcular_hads()
    calcular_panas()
    calcular_bart()