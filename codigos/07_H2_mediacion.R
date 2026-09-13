# =====================================================================
# 07_H2_mediacion.R
#
# H2 — Mediación con PROCESS v4.3.1 (Hayes, 2022), Modelo 4
#
# X = grupo etario (0 = joven, 1 = mayor)
# M = processing_speed (Modelo A) / hads_ansiedad_total (Modelo B)
# Outcomes: adjusted_pumps (principal), total_money, total_explosions
#
# Modelo A se estima con errores estándar HC3 (heterocedasticidad
# consistente). Modelo B se estima con errores estándar convencionales.
#
# Muestra:
#   Base maestra = N 74
#   Modelo A      = N 73 (excluido ID 4)
#
# Bootstrap: percentil, 10.000 remuestras, seed = 33333
# =====================================================================

# =====================================================================
# 1. CARGAR PROCESS Y PAQUETE mediation
# =====================================================================

source(file.choose())

if (!exists("process")) {
  stop("PROCESS no se cargó correctamente.")
}

if (!requireNamespace("mediation", quietly = TRUE)) {
  install.packages("mediation")
}
library(mediation)

# =====================================================================
# 2. PARÁMETROS GENERALES
# =====================================================================

PROJECT_ROOT <- "/Users/angelanavajas/Desktop/anmc/analisis"

DATA_PATH <- file.path(PROJECT_ROOT, "datos", "limpios", "base_maestra_final.csv")

OUTPUT_DIR <- file.path(PROJECT_ROOT, "outputs", "H2_PROCESS_hc3")

dir.create(OUTPUT_DIR, recursive = TRUE, showWarnings = FALSE)

N_BOOT <- 10000
SEED_PROCESS <- 33333

options(width = 300)


# =====================================================================
# 3. CARGAR BASE MAESTRA
# =====================================================================

base <- read.csv(DATA_PATH, stringsAsFactors = FALSE)

if (nrow(base) != 74) {
  stop(paste("Se esperaban 74 participantes en la base maestra y hay", nrow(base)))
}

if (anyDuplicated(base$participant_id)) {
  stop("Hay participant_id duplicados en la base maestra.")
}

if (!"edad_std_intragrupo" %in% names(base)) {
  stop(
    "Falta la columna edad_std_intragrupo. ",
    "Correr primero el script que la construye (edad estandarizada ",
    "por la media y DE del propio grupo etario)."
  )
}


# =====================================================================
# 4. DEFINIR MUESTRA H2 (Modelo A)
# =====================================================================

if (!"incluido_h2_speed" %in% names(base)) {
  stop(
    "Falta la columna incluido_h2_speed en base_maestra_final.csv. ",
    "Correr primero 20_crear_processing_speed_final.py y ",
    "21_construir_base_maestra_final.py actualizados."
  )
}

datos_h2 <- base[base$incluido_h2_speed == 1, , drop = FALSE]

datos_h2$grupo_code <- ifelse(datos_h2$grupo == "joven", 0,
                              ifelse(datos_h2$grupo == "mayor", 1, NA))

if (any(is.na(datos_h2$grupo_code))) {
  stop("Hay categorías de grupo que no pudieron codificarse.")
}

if (!all(datos_h2$genero %in% c(1, 2))) {
  stop("La variable genero contiene valores distintos de 1 y 2.")
}

datos_h2$genero_code <- ifelse(datos_h2$genero == 1, 0, 1)

cat("\nMuestra H2 (Modelo A):", nrow(datos_h2),
    "-- jóvenes:", sum(datos_h2$grupo_code == 0),
    "-- mayores:", sum(datos_h2$grupo_code == 1), "\n")

if (nrow(datos_h2) != 73) {
  stop(paste("Se esperaban 73 participantes para H2 (Modelo A) y hay", nrow(datos_h2)))
}


# =====================================================================
# 5. VARIABLES Y CHEQUEO DE MISSING
# =====================================================================

variables_h2 <- c("grupo_code", "processing_speed", "adjusted_pumps",
                  "total_money", "total_explosions")

variables_sensibilidad <- c(variables_h2, "genero_code", "edad_std_intragrupo")

faltantes <- setdiff(variables_sensibilidad, names(datos_h2))
if (length(faltantes) > 0) {
  stop(paste("Faltan variables en la base:", paste(faltantes, collapse = ", ")))
}

if (any(colSums(is.na(datos_h2[variables_sensibilidad])) > 0)) {
  stop("Hay missing en variables necesarias para los modelos. No se ejecutará PROCESS.")
}


# =====================================================================
# 6. FUNCIONES DE EXTRACCIÓN DE RESULTADOS
# =====================================================================

extraer_numeros <- function(linea) {
  partes <- strsplit(trimws(linea), "\\s+")[[1]]
  numeros <- suppressWarnings(as.numeric(partes[-1]))
  numeros[!is.na(numeros)]
}

extraer_resultados_process <- function(salida, modelo, outcome, tipo_modelo,
                                       controles, x_var, m_var, n_muestra) {
  
  patron_x <- paste0("^\\s*", x_var, "\\s+")
  lineas_x <- grep(patron_x, salida, value = TRUE)
  
  if (length(lineas_x) < 3) {
    stop(paste("No se pudieron extraer los coeficientes de", x_var, "en", modelo))
  }
  
  a_vals      <- extraer_numeros(lineas_x[1])
  cprime_vals <- extraer_numeros(lineas_x[2])
  c_vals      <- extraer_numeros(lineas_x[3])
  
  patron_m <- paste0("^\\s*", m_var, "\\s+")
  lineas_m <- grep(patron_m, salida, value = TRUE)
  numeros_m <- lapply(lineas_m, extraer_numeros)
  
  idx_b <- which(lengths(numeros_m) == 6)
  idx_indirecto <- which(lengths(numeros_m) == 4)
  
  if (length(idx_b) == 0 || length(idx_indirecto) == 0) {
    stop(paste("No se pudo extraer path b o efecto indirecto en", modelo))
  }
  
  b_vals <- numeros_m[[idx_b[1]]]
  indirecto_vals <- numeros_m[[idx_indirecto[1]]]
  
  paths <- data.frame(
    modelo = modelo, outcome = outcome, tipo_modelo = tipo_modelo,
    controles = controles, N = n_muestra,
    
    a = a_vals[1], SE_a = a_vals[2], t_a = a_vals[3], p_a = a_vals[4],
    LLCI_a = a_vals[5], ULCI_a = a_vals[6],
    
    b = b_vals[1], SE_b = b_vals[2], t_b = b_vals[3], p_b = b_vals[4],
    LLCI_b = b_vals[5], ULCI_b = b_vals[6],
    
    c_total = c_vals[1], SE_c = c_vals[2], t_c = c_vals[3], p_c = c_vals[4],
    LLCI_c = c_vals[5], ULCI_c = c_vals[6],
    
    c_directo = cprime_vals[1], SE_c_directo = cprime_vals[2],
    t_c_directo = cprime_vals[3], p_c_directo = cprime_vals[4],
    LLCI_c_directo = cprime_vals[5], ULCI_c_directo = cprime_vals[6],
    
    stringsAsFactors = FALSE
  )
  
  boot_llci <- indirecto_vals[3]
  boot_ulci <- indirecto_vals[4]
  
  evidencia <- ifelse(boot_llci > 0 | boot_ulci < 0,
                      "IC 95% no incluye 0", "IC 95% incluye 0")
  
  indirecto <- data.frame(
    modelo = modelo, outcome = outcome, tipo_modelo = tipo_modelo,
    controles = controles, N = n_muestra,
    efecto_indirecto = indirecto_vals[1], BootSE = indirecto_vals[2],
    BootLLCI = boot_llci, BootULCI = boot_ulci,
    evidencia_indirecta = evidencia,
    stringsAsFactors = FALSE
  )
  
  return(list(paths = paths, indirecto = indirecto))
}


# =====================================================================
# 7. EJECUTAR MODELO PROCESS
# =====================================================================

ejecutar_modelo <- function(modelo, datos, x_var, m_var, outcome,
                            tipo_modelo, covariables = NULL, usar_hc3 = TRUE) {
  
  cat("\n", strrep("=", 70), "\n", modelo, "\nOutcome:", outcome,
      "\nX:", x_var, " M:", m_var, "\nTipo:", tipo_modelo,
      "\nHC3:", usar_hc3, "\n", strrep("=", 70), "\n")
  
  argumentos <- list(
    data = datos, y = outcome, x = x_var, m = m_var,
    model = 4, total = 1, boot = N_BOOT, seed = SEED_PROCESS
  )
  
  if (usar_hc3) {
    argumentos$hc <- 3
  }
  
  if (!is.null(covariables)) {
    argumentos$cov <- covariables
    controles_texto <- paste(covariables, collapse = " + ")
  } else {
    controles_texto <- "ninguno"
  }
  
  salida <- capture.output(do.call(process, argumentos))
  cat(paste(salida, collapse = "\n"), "\n")
  
  archivo_txt <- file.path(OUTPUT_DIR, paste0(modelo, ".txt"))
  writeLines(salida, archivo_txt)
  
  resultados <- extraer_resultados_process(
    salida = salida, modelo = modelo, outcome = outcome,
    tipo_modelo = tipo_modelo, controles = controles_texto,
    x_var = x_var, m_var = m_var, n_muestra = nrow(datos)
  )
  
  return(resultados)
}


# =====================================================================
# 8. MODELO A — PROCESSING SPEED (principal + sensibilidad)
# =====================================================================

M1 <- ejecutar_modelo("M1_adjusted_pumps_hc3", datos_h2, "grupo_code",
                      "processing_speed", "adjusted_pumps", "Principal",
                      usar_hc3 = TRUE)

M2 <- ejecutar_modelo("M2_total_money_hc3", datos_h2, "grupo_code",
                      "processing_speed", "total_money", "Secundario",
                      usar_hc3 = TRUE)

M3 <- ejecutar_modelo("M3_total_explosions_hc3", datos_h2, "grupo_code",
                      "processing_speed", "total_explosions",
                      "Secundario_exploratorio", usar_hc3 = TRUE)

COVARIABLES <- c("genero_code", "edad_std_intragrupo")

M1_S <- ejecutar_modelo("M1S_adjusted_pumps_controles_hc3", datos_h2, "grupo_code",
                        "processing_speed", "adjusted_pumps", "Sensibilidad",
                        covariables = COVARIABLES, usar_hc3 = TRUE)

M2_S <- ejecutar_modelo("M2S_total_money_controles_hc3", datos_h2, "grupo_code",
                        "processing_speed", "total_money", "Sensibilidad",
                        covariables = COVARIABLES, usar_hc3 = TRUE)

M3_S <- ejecutar_modelo("M3S_total_explosions_controles_hc3", datos_h2, "grupo_code",
                        "processing_speed", "total_explosions",
                        "Sensibilidad_exploratorio", covariables = COVARIABLES,
                        usar_hc3 = TRUE)


# =====================================================================
# 9. MODELO B — HADS-ANSIEDAD COMO MEDIADOR COMPETIDOR
# =====================================================================

datos_h2b <- base
datos_h2b$grupo_code <- ifelse(datos_h2b$grupo == "joven", 0,
                               ifelse(datos_h2b$grupo == "mayor", 1, NA))
datos_h2b$genero_code <- ifelse(datos_h2b$genero == 1, 0, 1)

MB <- ejecutar_modelo("MB_hads_ansiedad_explosiones", datos_h2b, "grupo_code",
                      "hads_ansiedad_total", "total_explosions",
                      "Modelo_B_mediador_competidor", usar_hc3 = FALSE)

MB_S <- ejecutar_modelo("MBS_hads_ansiedad_explosiones_controles", datos_h2b, "grupo_code",
                        "hads_ansiedad_total", "total_explosions",
                        "Modelo_B_sensibilidad", covariables = COVARIABLES,
                        usar_hc3 = FALSE)


# =====================================================================
# 10. EFECTO TOTAL (c) DEL MODELO A SIN COVARIABLES
#
# Regresión OLS independiente de grupo_code sobre cada outcome, sin
# mediador. Equivalente al t de Student de dos muestras con varianzas
# iguales.
# =====================================================================

calcular_efecto_total_ols <- function(outcome, datos) {
  formula_txt <- paste(outcome, "~ grupo_code")
  modelo_lm <- lm(as.formula(formula_txt), data = datos)
  s <- summary(modelo_lm)
  ci <- confint(modelo_lm, "grupo_code", level = 0.95)
  
  data.frame(
    outcome = outcome,
    c_total = round(s$coefficients["grupo_code", "Estimate"], 4),
    SE_c = round(s$coefficients["grupo_code", "Std. Error"], 4),
    t_c = round(s$coefficients["grupo_code", "t value"], 4),
    p_c = round(s$coefficients["grupo_code", "Pr(>|t|)"], 4),
    LLCI_c = round(ci[1], 4),
    ULCI_c = round(ci[2], 4)
  )
}

efecto_total <- rbind(
  calcular_efecto_total_ols("adjusted_pumps", datos_h2b),
  calcular_efecto_total_ols("total_money", datos_h2b),
  calcular_efecto_total_ols("total_explosions", datos_h2b)
)

write.csv(efecto_total, file.path(OUTPUT_DIR, "H2_efecto_total.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")


# =====================================================================
# 11. TABLAS GENERALES (Modelo A + Modelo B)
# =====================================================================

tabla_paths <- rbind(M1$paths, M2$paths, M3$paths,
                     M1_S$paths, M2_S$paths, M3_S$paths,
                     MB$paths, MB_S$paths)

for (outc in c("adjusted_pumps", "total_money", "total_explosions")) {
  fila <- efecto_total[efecto_total$outcome == outc, ]
  idx <- which(tabla_paths$outcome == outc &
                 tabla_paths$tipo_modelo %in% c("Principal", "Secundario", "Secundario_exploratorio"))
  
  tabla_paths$c_total[idx] <- fila$c_total
  tabla_paths$SE_c[idx] <- fila$SE_c
  tabla_paths$t_c[idx] <- fila$t_c
  tabla_paths$p_c[idx] <- fila$p_c
  tabla_paths$LLCI_c[idx] <- fila$LLCI_c
  tabla_paths$ULCI_c[idx] <- fila$ULCI_c
}

tabla_indirectos <- rbind(M1$indirecto, M2$indirecto, M3$indirecto,
                          M1_S$indirecto, M2_S$indirecto, M3_S$indirecto,
                          MB$indirecto, MB_S$indirecto)

cols_paths_num <- setdiff(names(tabla_paths),
                          c("modelo", "outcome", "tipo_modelo", "controles"))
tabla_paths[cols_paths_num] <- round(tabla_paths[cols_paths_num], 4)

cols_indirecto_num <- c("efecto_indirecto", "BootSE", "BootLLCI", "BootULCI")
tabla_indirectos[cols_indirecto_num] <- round(tabla_indirectos[cols_indirecto_num], 4)

write.csv(tabla_paths, file.path(OUTPUT_DIR, "H2_tabla_paths_PROCESS_hc3.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")
write.csv(tabla_indirectos, file.path(OUTPUT_DIR, "H2_tabla_efectos_indirectos_hc3.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

cat("\n\nTABLA DE PATHS:\n")
print(tabla_paths, row.names = FALSE)

cat("\n\nTABLA DE EFECTOS INDIRECTOS:\n")
print(tabla_indirectos, row.names = FALSE)


# =====================================================================
# 12. P-VALOR EXPLÍCITO DEL EFECTO INDIRECTO (paquete mediation)
# =====================================================================

correr_mediation <- function(datos, x_var, m_var, y_var, covariables = NULL) {
  
  formula_m_txt <- paste(m_var, "~", x_var,
                         if (!is.null(covariables)) paste("+", paste(covariables, collapse = "+")) else "")
  formula_y_txt <- paste(y_var, "~", x_var, "+", m_var,
                         if (!is.null(covariables)) paste("+", paste(covariables, collapse = "+")) else "")
  
  assign(".mediation_formula_m", as.formula(formula_m_txt), envir = .GlobalEnv)
  assign(".mediation_formula_y", as.formula(formula_y_txt), envir = .GlobalEnv)
  assign(".mediation_datos", datos, envir = .GlobalEnv)
  
  model.M <- lm(.mediation_formula_m, data = .mediation_datos)
  model.Y <- lm(.mediation_formula_y, data = .mediation_datos)
  
  set.seed(SEED_PROCESS)
  resultado <- mediate(model.M, model.Y, treat = x_var, mediator = m_var,
                       boot = TRUE, sims = N_BOOT)
  
  return(resultado)
}

especificaciones <- list(
  list(nombre = "M1_adjusted_pumps",              datos = datos_h2,  x = "grupo_code", m = "processing_speed",   y = "adjusted_pumps",     cov = NULL),
  list(nombre = "M2_total_money",                 datos = datos_h2,  x = "grupo_code", m = "processing_speed",   y = "total_money",        cov = NULL),
  list(nombre = "M3_total_explosions",             datos = datos_h2,  x = "grupo_code", m = "processing_speed",   y = "total_explosions",   cov = NULL),
  list(nombre = "M1S_adjusted_pumps_controles",    datos = datos_h2,  x = "grupo_code", m = "processing_speed",   y = "adjusted_pumps",     cov = COVARIABLES),
  list(nombre = "M2S_total_money_controles",       datos = datos_h2,  x = "grupo_code", m = "processing_speed",   y = "total_money",        cov = COVARIABLES),
  list(nombre = "M3S_total_explosions_controles",  datos = datos_h2,  x = "grupo_code", m = "processing_speed",   y = "total_explosions",   cov = COVARIABLES),
  list(nombre = "MB_hads_ansiedad_explosiones",    datos = datos_h2b, x = "grupo_code", m = "hads_ansiedad_total", y = "total_explosions",  cov = NULL),
  list(nombre = "MBS_hads_ansiedad_explosiones_controles", datos = datos_h2b, x = "grupo_code", m = "hads_ansiedad_total", y = "total_explosions", cov = COVARIABLES)
)

tabla_pvalores_mediation <- data.frame()

cat("\n\n", strrep("=", 70), "\nP-VALORES EXPLÍCITOS DEL EFECTO INDIRECTO (paquete mediation)\n", strrep("=", 70), "\n")

for (spec in especificaciones) {
  
  cat("\n---", spec$nombre, "---\n")
  
  resultado <- correr_mediation(spec$datos, spec$x, spec$m, spec$y, spec$cov)
  s <- summary(resultado)
  
  fila <- data.frame(
    modelo = spec$nombre,
    ACME = round(s$d.avg, 4),
    ACME_p = round(s$d.avg.p, 4),
    ADE = round(s$z.avg, 4),
    ADE_p = round(s$z.avg.p, 4),
    Total_Effect = round(s$tau.coef, 4),
    Total_p = round(s$tau.p, 4),
    Prop_Mediada = round(s$n.avg, 4)
  )
  
  tabla_pvalores_mediation <- rbind(tabla_pvalores_mediation, fila)
  
  print(summary(resultado))
}

write.csv(tabla_pvalores_mediation,
          file.path(OUTPUT_DIR, "H2_pvalores_mediation_package.csv"),
          row.names = FALSE, fileEncoding = "UTF-8")

cat("\n\nTABLA RESUMEN — p-valores explícitos por modelo:\n")
print(tabla_pvalores_mediation, row.names = FALSE)


# =====================================================================
# 13. INFORMACIÓN FINAL
# =====================================================================

cat("\n\nAnálisis H2 finalizado.\n")
cat("N Modelo A:", nrow(datos_h2), " | N Modelo B:", nrow(datos_h2b), "\n")
cat("Bootstrap:", N_BOOT, " | Seed:", SEED_PROCESS, "\n")
cat("Outputs en:", OUTPUT_DIR, "\n")