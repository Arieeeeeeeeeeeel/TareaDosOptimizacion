================================================================
Tarea 2 - Metaheurísticas: Travelling Thief Problem (TTP)
Algoritmo implementado: Simulated Annealing
================================================================

INTEGRANTES DEL GRUPO
----------------------------------------------------------------
- Diego Alvarado 20.916.064-1
- Ignacia Brahim 21.275.186-3
- Ariel Villar 20.447.126-6


REQUISITOS
----------------------------------------------------------------
- Python 3.8 o superior
- matplotlib (opcional, para generar los gráficos de boxplot y
  convergencia; si no está instalado, los datos se guardan en
  archivos .csv dentro de resultados/)


ESTRUCTURA DEL PROYECTO
----------------------------------------------------------------
- ttp.py              : Parser de instancias TTP y evaluación de la función objetivo
- sa.py               : Algoritmo Simulated Annealing con vecindad mixta
- instancias/         : Archivos de las 3 instancias (01_facil, 02_medio, 03_dificil)
- runs/               : Scripts ejecutables de los experimentos
    - main.py         : Experimento principal (10 ejecuciones x 60s por instancia)
    - convergencia.py : Estudio de convergencia (corridas largas de 600s)
    - comparacion.py  : Experimento de comparación con el otro grupo
                         (10 ejecuciones x 10 minutos por instancia,
                         midiendo el mejor Z a los 2, 5 y 10 minutos)
- resultados/         : Salidas en texto (.txt) de cada experimento
- graficos/           : Gráficos generados (boxplots, curvas de convergencia)
- docs/               : Documentos de la tarea (pauta y enunciado)
- README.txt          : Este archivo


INSTRUCCIONES DE EJECUCIÓN
----------------------------------------------------------------
Todos los scripts se deben ejecutar desde la carpeta raíz del proyecto
(tarea2/), pasando como argumentos las instancias a resolver.

Experimento principal (10 ejecuciones de 60s por instancia):

    python runs/main.py instancias/01_facil.txt instancias/02_medio.txt instancias/03_dificil.txt

Estudio de convergencia (3 semillas, corridas de 600s por instancia):

    python runs/convergencia.py

Experimento de comparación con el otro grupo (10 ejecuciones de 10 minutos
por instancia; total aproximado: 5 horas para las 3 instancias):

    python runs/comparacion.py instancias/01_facil.txt instancias/02_medio.txt instancias/03_dificil.txt

Para cambiar el presupuesto de tiempo o el número de ejecuciones,
editar las constantes al inicio de cada script (N_EJECUCIONES, TIEMPO_MAX).


PARÁMETROS DEL ALGORITMO
----------------------------------------------------------------
- Presupuesto por ejecución  : 60s (informe) / 600s (comparación y convergencia)
- Número de ejecuciones      : 10 por instancia (3 semillas en convergencia)
- Temperatura inicial (T0)   : calibrada automáticamente con 500 muestras,
                                buscando un 80% de aceptación de movimientos
                                de empeoramiento
- Temperatura mínima         : valor fijo = 1.0
- Factor de enfriamiento (α) : calculado para que T llegue a la temperatura
                                mínima justo al terminar el tiempo disponible
- Mezcla de movimientos      : 50% 2-opt (tour) / 50% sobre la mochila
                                (bit-flip, con intercambio de ítems como respaldo
                                si la mochila está llena)
- Solución inicial           : tour por vecino más cercano + mochila greedy
                                por ratio ganancia/peso


DESCRIPCIÓN BREVE DEL ALGORITMO
----------------------------------------------------------------
Se implementa Simulated Annealing (SA) con representación mixta:
  - Un tour de ciudades (permutación)
  - Un plan de empaque binario (qué ítems llevar)

En cada iteración se elige aleatoriamente entre:
  1. Movimiento de tour (2-opt): invertir un segmento del tour.
  2. Movimiento de mochila (bit-flip): agregar o quitar un ítem,
     o intercambiar un ítem por otro si la mochila está llena.

La función objetivo es: Z = ganancia_items - R * tiempo_viaje
donde R es el "renting ratio" de la instancia y el tiempo de viaje
depende del peso cargado (más peso = más lento).

La evaluación de cada movimiento es incremental (no se recalcula
todo desde cero), lo que permite muchas más iteraciones por segundo.

Cada ejecución reporta, además del mejor Z encontrado: el número
de evaluaciones realizadas y el tiempo (tiempo_hallazgo) en el que
se encontró la última mejora antes de quedar estancado.
================================================================
