# tg_anmc
Trabajo de graduación de la Licenciatura en Ciencias del Comportamiento de Angela Navajas McCormick

Código de tesis de grado: diferencias etarias en toma de riesgo (BART),
mediadas por velocidad de procesamiento. 

## Estructura

```
codigo_experimento/
├── exp.py              # experimento propio (PsychoPy)
├── symbol/              # estímulos, tarea de velocidad de procesamiento
└── bart_task-main/      # BART base, de Hannah Sophie Heinrichs (2020) — ver ATRIBUCION.txt

codigo_analisis/
├── 01_importar_datos_crudos.py
├── 02_calcular_puntajes.py
├── 03_aplicar_exclusiones.py
├── 04_procesar_velocidad_procesamiento.py
├── 05_construir_base_maestra.py
├── 06_H1_descriptivas_y_diferencias.py
├── 07_H2_mediacion.R
└── 08_H3_afecto_BART.py
```

Scripts en `codigo_analisis/` se corren en orden numérico.

## Entorno

Python 3.10.14 (scipy, statsmodels) · R 4.5.0 (PROCESS v4.3.1, `mediation`)
