#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_importar_datos_crudos.py

Limpia los cuatro archivos crudos exportados desde PsychoPy y produce
las versiones "_clean".

"""

from pathlib import Path

import pandas as pd

# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path("/Users/angelanavajas/Desktop/anmc")
RAW_DIR = PROJECT_ROOT / "datos" / "crudos" / "psychopy"
CLEAN_DIR = PROJECT_ROOT / "datos" / "limpios"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

PS_TRIALS_RAW = RAW_DIR / "processing_speed_trials.csv"
BART_EVENTS_RAW = RAW_DIR / "bart_events.csv"
PANAS_ITEMS_RAW = RAW_DIR / "panas_items.csv"
PARTICIPANTS_RAW = RAW_DIR / "participants.csv"


# ============================================================
# LECTOR ROBUSTO — DELIMITADOR MIXTO (';' y ',')
# ============================================================

def leer_csv_delimitador_mixto(path, n_columnas_esperadas):
    df = pd.read_csv(path, sep=";", dtype=str)

    if len(df.columns) != n_columnas_esperadas:
        raise ValueError(
            f"{path}: se esperaban {n_columnas_esperadas} columnas al separar "
            f"por ';' y se encontraron {len(df.columns)}. Revisar el header."
        )

    primera_col = df.columns[0]
    resto_cols = df.columns[1:]

    corrupta = df[resto_cols].isna().all(axis=1) & df[primera_col].str.contains(",", na=False)
    n_corruptas = corrupta.sum()

    if n_corruptas > 0:
        print(f"  {path.name}: {n_corruptas} filas con delimitador ',' en vez de ';' — corrigiendo.")
        reparsed = df.loc[corrupta, primera_col].str.split(",", expand=True)
        if reparsed.shape[1] != n_columnas_esperadas:
            raise ValueError(
                f"{path}: al re-separar por ',' se obtuvieron {reparsed.shape[1]} campos, "
                f"se esperaban {n_columnas_esperadas}. Revisar manualmente las filas afectadas."
            )
        reparsed.columns = df.columns
        df.loc[corrupta, :] = reparsed.values

    return df


# ============================================================
# LÍMITE DE ARCHIVO ENTRE PARTICIPANTE 78 Y 79
#
# En los tres archivos (processing_speed_trials, bart_events,
# panas_items), al último registro del participante 78 (delimitado
# por ';') le falta el salto de línea que lo separa del primer
# registro del participante 79 (delimitado por ',').
# ============================================================

PARCHE_PS_TRIALS_79 = {
    "participant_id": "79", "session_id": "2026-06-15_14h46m43s", "task": "SRT_PRACTICE",
    "trial_index": "1", "stimulus": "circle", "correct_answer": "space", "response": "space",
    "rt_ms": "626.06", "timestamp": "2026-06-15T14:59:14", "stim_onset_time": "775.1915",
    "resp_time": "775.8175", "foreperiod_ms": "", "digit": "", "mapping_id": "",
}
PS_TRIALS_COLUMNAS_ORDEN = ["participant_id", "session_id", "task", "trial_index", "stimulus",
                            "correct_answer", "response", "rt_ms", "timestamp", "stim_onset_time",
                            "resp_time", "foreperiod_ms", "digit", "mapping_id"]

PARCHE_BART_EVENTS_79 = {
    "participant_id": "79", "session_id": "2026-06-15_14h46m43s", "phase": "bart",
    "balloon_index": "1", "event_type": "balloon_start", "event_index": "0",
    "timestamp": "2026-06-15T14:50:50", "rt_ms": "", "pump_number": "0",
}
BART_EVENTS_COLUMNAS_ORDEN = ["participant_id", "session_id", "phase", "balloon_index",
                              "event_type", "event_index", "timestamp", "rt_ms", "pump_number"]

PARCHE_PANAS_ITEMS_79 = {
    "participant_id": "79", "session_id": "2026-06-15_14h46m43s", "phase": "panas",
    "item_id": "PA05", "response": "3",  # forma cruda; queda 3.0 tras la coerción numérica
}
PANAS_ITEMS_COLUMNAS_ORDEN = ["participant_id", "session_id", "phase", "item_id", "response"]


def _texto_crudo_de_parche(parche, orden_columnas):
    """Reconstruye cómo se ve una fila del parche en su forma cruda
    separada por comas, tal como quedó pegada al campo corrupto."""
    return ",".join(str(parche[c]) for c in orden_columnas)


def _recortar_campo_corrupto(serie, parche, orden_columnas):
    """
    Quita, del final de cada valor de la serie, el texto crudo del
    parche (si está presente), dejando solo el valor legítimo que
    precedía a la corrupción. No modifica filas donde el patrón no
    aparece.
    """
    sufijo = _texto_crudo_de_parche(parche, orden_columnas)
    contiene = serie.astype(str).str.contains(sufijo, regex=False, na=False)
    if contiene.any():
        serie = serie.astype(str)
        serie.loc[contiene] = serie.loc[contiene].str.replace(sufijo, "", regex=False)
    return serie, contiene


# ============================================================
# 1. PROCESSING SPEED TRIALS
# ============================================================

def limpiar_processing_speed_trials():
    print("\n" + "=" * 70)
    print("PROCESSING SPEED TRIALS")
    print("=" * 70)

    df = leer_csv_delimitador_mixto(PS_TRIALS_RAW, 14)

    df["mapping_id"], corregidas = _recortar_campo_corrupto(
        df["mapping_id"], PARCHE_PS_TRIALS_79, PS_TRIALS_COLUMNAS_ORDEN
    )
    if corregidas.any():
        print(f"  {corregidas.sum()} fila(s) con mapping_id corrupto (límite de archivo "
              f"78/79) — recortado a su valor legítimo.")

    df = pd.concat([pd.DataFrame([PARCHE_PS_TRIALS_79]), df], ignore_index=True)
    print("  + fila restituida: participante 79, SRT_PRACTICE, trial_index=1 "
          "(recuperada del campo corrupto de arriba, no es una reconstrucción manual)")

    df["participant_id"] = pd.to_numeric(df["participant_id"], errors="raise").astype(int)
    df["trial_index"] = pd.to_numeric(df["trial_index"], errors="coerce").astype("Int64")
    for col in ["rt_ms", "stim_onset_time", "resp_time", "foreperiod_ms", "digit"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values(["participant_id", "session_id", "task", "trial_index"]).reset_index(drop=True)

    out_path = CLEAN_DIR / "processing_speed_trials_clean.csv"
    df.to_csv(out_path, index=False)
    print(f"  N filas: {len(df)} | N participantes: {df['participant_id'].nunique()}")
    print(f"  Guardado: {out_path}")
    return df


# ============================================================
# 2. BART EVENTS
# ============================================================

def limpiar_bart_events():
    print("\n" + "=" * 70)
    print("BART EVENTS")
    print("=" * 70)

    df = leer_csv_delimitador_mixto(BART_EVENTS_RAW, 9)

    df["pump_number"], corregidas = _recortar_campo_corrupto(
        df["pump_number"], PARCHE_BART_EVENTS_79, BART_EVENTS_COLUMNAS_ORDEN
    )
    if corregidas.any():
        print(f"  {corregidas.sum()} fila(s) con pump_number corrupto (límite de archivo "
              f"78/79) — recortado a su valor legítimo.")

    df = pd.concat([pd.DataFrame([PARCHE_BART_EVENTS_79]), df], ignore_index=True)
    print("  + fila restituida: participante 79, balloon_start, balloon_index=1 "
          "(recuperada del campo corrupto de arriba, no es una reconstrucción manual)")

    df["participant_id"] = pd.to_numeric(df["participant_id"], errors="raise").astype(int)
    df["balloon_index"] = pd.to_numeric(df["balloon_index"], errors="coerce").astype("Int64")
    df["event_index"] = pd.to_numeric(df["event_index"], errors="coerce").astype("Int64")
    df["rt_ms"] = pd.to_numeric(df["rt_ms"], errors="coerce")
    df["pump_number"] = pd.to_numeric(df["pump_number"], errors="coerce").astype("Int64")

    df = df.sort_values(["participant_id", "session_id", "balloon_index", "event_index"]).reset_index(drop=True)

    out_path = CLEAN_DIR / "bart_events_clean.csv"
    df.to_csv(out_path, index=False)
    print(f"  N filas: {len(df)} | N participantes: {df['participant_id'].nunique()}")
    print(f"  Guardado: {out_path}")
    print("  NOTA: este archivo puede tener participantes con más de una "
          "session_id (reinicios de tarea). La selección de la sesión válida "
          "se resuelve en 02_calcular_puntajes.py, no acá.")
    return df


# ============================================================
# 3. PANAS ITEMS
# ============================================================

def limpiar_panas_items():
    print("\n" + "=" * 70)
    print("PANAS ITEMS")
    print("=" * 70)

    df = leer_csv_delimitador_mixto(PANAS_ITEMS_RAW, 5)

    df["response"], corregidas = _recortar_campo_corrupto(
        df["response"], PARCHE_PANAS_ITEMS_79, PANAS_ITEMS_COLUMNAS_ORDEN
    )
    if corregidas.any():
        print(f"  {corregidas.sum()} fila(s) con response corrupto (límite de archivo "
              f"78/79) — recortado a su valor legítimo.")

    df = pd.concat([pd.DataFrame([PARCHE_PANAS_ITEMS_79]), df], ignore_index=True)
    print("  + fila restituida: participante 79, item PA05 "
          "(recuperada del campo corrupto de arriba, no es una reconstrucción manual)")

    df["participant_id"] = pd.to_numeric(df["participant_id"], errors="raise").astype(int)
    df["response"] = pd.to_numeric(df["response"], errors="coerce")

    df = df.sort_values(["participant_id", "session_id", "item_id"]).reset_index(drop=True)

    out_path = CLEAN_DIR / "panas_items_clean.csv"
    df.to_csv(out_path, index=False)
    print(f"  N filas: {len(df)} | N participantes: {df['participant_id'].nunique()}")
    print(f"  Guardado: {out_path}")
    return df


# ============================================================
# 4. PARTICIPANTS (auditoría cruzada — no alimenta el pipeline principal)
# ============================================================

def limpiar_participants():
    print("\n" + "=" * 70)
    print("PARTICIPANTS")
    print("=" * 70)

    df = pd.read_csv(PARTICIPANTS_RAW, sep=";", header=None, dtype=str, skiprows=1)
    df.columns = ["participant_id", "group", "session_id", "date_time_start", "date_time_end",
                  "experiment_version", "bart_money", "rifas", "panas_pos_sum", "panas_neg_sum"]

    dup = df[df["participant_id"].duplicated(keep=False)]
    if not dup.empty:
        print(f"  AVISO: participante(s) con filas duplicadas: {dup['participant_id'].unique().tolist()}")
        print("  Se conserva la primera fila de cada participante duplicado "
              "(la(s) siguiente(s) contienen datos corruptos de un reinicio de sesión).")
        df = df.drop_duplicates(subset="participant_id", keep="first")

    df["participant_id"] = pd.to_numeric(df["participant_id"], errors="raise").astype(int)
    for col in ["bart_money", "rifas", "panas_pos_sum", "panas_neg_sum"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values("participant_id").reset_index(drop=True)

    out_path = CLEAN_DIR / "participants_clean.csv"
    df.to_csv(out_path, index=False)
    print(f"  N filas: {len(df)}")
    print(f"  Guardado: {out_path}")
    return df


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    limpiar_processing_speed_trials()
    limpiar_bart_events()
    limpiar_panas_items()
    limpiar_participants()
