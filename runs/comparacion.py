import sys
import os
import time
import math

# Permitir importar sa.py y ttp.py, que estan un nivel mas arriba (carpeta del proyecto)
DIR_BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(DIR_BASE, ".."))

from ttp import InstanciaTTP
from sa  import simulated_annealing

# Experimento de COMPARACION con el otro grupo (genetico vs SA)
# Presupuesto acordado: 10 minutos (600s) por ejecucion.
# Ademas del resultado final, se registra el mejor Z encontrado
# a los 2, 5 y 10 minutos para poder comparar la velocidad de convergencia de ambos algoritmos en esos tres cortes de tiempo.
N_EJECUCIONES   = 10     # número de veces que se corre el SA por instancia
TIEMPO_MAX      = 600.0  # segundos por ejecución (10 minutos, acordado con el otro grupo)
ARCHIVO_SALIDA  = os.path.join(DIR_BASE, "..", "resultados", "resultadosComparacion_presentacion.txt")
ARCHIVO_BOXPLOT = os.path.join(DIR_BASE, "..", "graficos", "boxplot_presentacion.png")

# Cortes de tiempo (en segundos) donde se mide el mejor Z encontrado hasta ese momento
CORTES_SEGUNDOS = [120.0, 300.0, 600.0]
CORTES_NOMBRES  = ["2 min", "5 min", "10 min"]


# Función auxiliar: imprime en pantalla Y escribe en el archivo
def imprimir(texto, archivo):
    print(texto)
    archivo.write(texto + "\n")


# Busca en el historial el mejor Z que se tenia hasta el segundo "tiempo_corte"
# El historial es una lista de tuplas (tiempo, mejor_objetivo) ordenada por tiempo
def valor_en_tiempo(historial, tiempo_corte):
    valor = historial[0][1]
    for tiempo_punto, objetivo_punto in historial:
        if tiempo_punto <= tiempo_corte:
            valor = objetivo_punto
        else:
            break
    return valor


# Calcula mejor, media y desviacion estandar de una lista de valores
def calcular_estadisticas(valores):
    mejor = max(valores)
    media = sum(valores) / len(valores)

    suma_cuadrados = 0.0
    for v in valores:
        suma_cuadrados += (v - media) ** 2
    desviacion = math.sqrt(suma_cuadrados / len(valores))

    return mejor, media, desviacion


# Genera un grafico de cajas por instancia, comparando la distribucion del mejor Z a los 2, 5 y 10 minutos
def generar_boxplot(datos_por_instancia, nombres):
    try:
        import matplotlib.pyplot as plt

        fig, ejes = plt.subplots(1, len(datos_por_instancia), figsize=(15, 5))

        for k in range(len(datos_por_instancia)):
            ejes[k].boxplot(datos_por_instancia[k], labels=CORTES_NOMBRES, patch_artist=True)
            ejes[k].set_title(nombres[k])
            ejes[k].set_ylabel("Mejor Z")
            ejes[k].grid(True, axis='y', linestyle='--', alpha=0.7)

        plt.suptitle("Mejor Z encontrado a los 2, 5 y 10 minutos (10 ejecuciones)")
        plt.tight_layout()
        plt.savefig(ARCHIVO_BOXPLOT)
        plt.close()
        print("\nBoxplot guardado en: " + ARCHIVO_BOXPLOT)

    except ImportError:
        archivo_csv = open(os.path.join(DIR_BASE, "..", "resultados", "datos_boxplot_comparacion.csv"), "w")
        archivo_csv.write("instancia,corte,ejecucion,objetivo\n")
        for nombre, datos_cortes in zip(nombres, datos_por_instancia):
            for corte_nombre, valores in zip(CORTES_NOMBRES, datos_cortes):
                for j in range(len(valores)):
                    archivo_csv.write(nombre + "," + corte_nombre + "," + str(j + 1) + "," + f"{valores[j]:.4f}\n")
        archivo_csv.close()
        print("\nmatplotlib no disponible. Datos para boxplot guardados en: datos_boxplot_comparacion.csv")


# Función principal

def main():
    if len(sys.argv) < 2:
        print("Uso: python comparacion.py <instancia1.txt> [instancia2.txt] ...")
        print("Ejemplo: python comparacion.py instancias/01_facil.txt instancias/02_medio.txt instancias/03_dificil.txt")
        sys.exit(1)

    archivos = sys.argv[1:]

    salida = open(ARCHIVO_SALIDA, "w")
    imprimir("Resultados de comparacion (vs otro grupo) - Simulated Annealing TTP", salida)
    imprimir("Fecha: " + time.strftime("%Y-%m-%d %H:%M:%S"), salida)
    imprimir("Presupuesto: " + str(TIEMPO_MAX) + "s por ejecucion  |  Ejecuciones: " + str(N_EJECUCIONES), salida)
    imprimir("Cortes de tiempo: " + str(CORTES_NOMBRES), salida)

    datos_boxplot_por_instancia = []
    nombres_boxplot              = []

    for ruta in archivos:
        imprimir("\n" + "=" * 62, salida)
        imprimir("Instancia: " + ruta, salida)
        imprimir("=" * 62, salida)

        instancia = InstanciaTTP(ruta)
        imprimir("Ciudades: " + str(instancia.n_ciudades) +
                 " | Items: " + str(instancia.n_items) +
                 " | Capacidad: " + str(instancia.capacidad), salida)
        imprimir("Renting ratio: " + str(instancia.costo_renta), salida)
        imprimir("-" * 62, salida)

        tiempos_hallazgo = []
        obj_inicial      = None

        # Una lista de resultados por cada corte de tiempo (2 min, 5 min, 10 min)
        resultados_cortes = []
        for _ in CORTES_SEGUNDOS:
            resultados_cortes.append([])

        for i in range(1, N_EJECUCIONES + 1):
            tour, mochila, objetivo, obj_ini, n_evals, historial, tiempo_hallazgo = simulated_annealing(
                instancia,
                tiempo_max = TIEMPO_MAX,
                semilla    = i * 137  # mismas semillas que el experimento del informe
            )

            if i == 1:
                obj_inicial = obj_ini
                imprimir("  Solucion inicial (greedy): Z = " + f"{obj_inicial:.2f}", salida)
                imprimir("-" * 62, salida)

            tiempos_hallazgo.append(tiempo_hallazgo)

            # Guardar el mejor Z hasta cada corte de tiempo
            valores_corte = []
            for tiempo_corte in CORTES_SEGUNDOS:
                valor = valor_en_tiempo(historial, tiempo_corte)
                valores_corte.append(valor)

            # El ultimo corte (10 min) es el final de la ejecucion: usar
            # directamente "objetivo" para que coincida con el resultado real
            valores_corte[-1] = objetivo

            for k in range(len(CORTES_SEGUNDOS)):
                resultados_cortes[k].append(valores_corte[k])

            linea = ("  Ejecucion " + str(i).rjust(2) +
                     ": Z(2min) = "  + f"{valores_corte[0]:14.2f}" +
                     "  Z(5min) = "  + f"{valores_corte[1]:14.2f}" +
                     "  Z(10min) = " + f"{valores_corte[2]:14.2f}" +
                     "  |  evals = " + str(n_evals).rjust(7) +
                     "  |  tiempo_hallazgo = " + f"{tiempo_hallazgo:6.1f}s")
            imprimir(linea, salida)

        # Estadisticas de calidad (Z) en cada corte de tiempo
        imprimir("-" * 62, salida)
        for k in range(len(CORTES_SEGUNDOS)):
            mejor, media, desviacion = calcular_estadisticas(resultados_cortes[k])
            imprimir("  Z a los " + CORTES_NOMBRES[k] + " (Calidad)", salida)
            imprimir("    Mejor   : " + f"{mejor:.2f}", salida)
            imprimir("    Media   : " + f"{media:.2f}", salida)
            imprimir("    Desv.Est: " + f"{desviacion:.2f}", salida)

        # Estadisticas de tiempo de convergencia
        media_hallazgo = sum(tiempos_hallazgo) / len(tiempos_hallazgo)

        imprimir("  Tiempo de convergencia (ultima mejora)", salida)
        imprimir("    Media   : " + f"{media_hallazgo:.1f}s" + " / " + f"{TIEMPO_MAX:.0f}s", salida)

        datos_boxplot_por_instancia.append(resultados_cortes)
        nombres_boxplot.append(os.path.basename(ruta).replace(".txt", ""))

    salida.close()
    print("\nResultados guardados en: " + ARCHIVO_SALIDA)

    if len(datos_boxplot_por_instancia) > 0:
        generar_boxplot(datos_boxplot_por_instancia, nombres_boxplot)

if __name__ == "__main__":
    main()
