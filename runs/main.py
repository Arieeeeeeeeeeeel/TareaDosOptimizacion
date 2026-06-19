import sys
import os
import time
import math

# Permitir importar sa.py y ttp.py, que estan un nivel mas arriba (carpeta del proyecto)
DIR_BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(DIR_BASE, ".."))

from ttp import InstanciaTTP
from sa  import simulated_annealing

# -------------------------------------------------------
# Parámetros del experimento (editar aquí para acordar con el otro grupo)
# -------------------------------------------------------
N_EJECUCIONES   = 10    # número de veces que se corre el SA por instancia
TIEMPO_MAX      = 60.0  # segundos por ejecución
ARCHIVO_SALIDA  = os.path.join(DIR_BASE, "..", "resultados", "resultados_informe.txt")
ARCHIVO_BOXPLOT = os.path.join(DIR_BASE, "..", "graficos", "boxplot_informe.png")

# -------------------------------------------------------
# Función auxiliar: imprime en pantalla Y escribe en el archivo
# -------------------------------------------------------
def imprimir(texto, archivo):
    print(texto)
    archivo.write(texto + "\n")

# -------------------------------------------------------
# Genera boxplot con los resultados de las 10 ejecuciones
# -------------------------------------------------------
def generar_boxplot(todos_resultados, nombres):
    try:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 6))
        plt.boxplot(todos_resultados, labels=nombres, patch_artist=True)
        plt.title("Distribucion del objetivo Z por instancia (10 ejecuciones)")
        plt.ylabel("Funcion objetivo Z")
        plt.xlabel("Instancia")
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(ARCHIVO_BOXPLOT)
        plt.close()
        print("\nBoxplot guardado en: " + ARCHIVO_BOXPLOT)

    except ImportError:
        # Si matplotlib no está instalado, guardar los datos en CSV
        archivo_csv = open(os.path.join(DIR_BASE, "..", "resultados", "datos_boxplot.csv"), "w")
        archivo_csv.write("instancia,ejecucion,objetivo\n")
        for nombre, resultados in zip(nombres, todos_resultados):
            for j in range(len(resultados)):
                archivo_csv.write(nombre + "," + str(j + 1) + "," + f"{resultados[j]:.4f}\n")
        archivo_csv.close()
        print("\nmatplotlib no disponible. Datos para boxplot guardados en: datos_boxplot.csv")

# -------------------------------------------------------
# Función principal
# -------------------------------------------------------

def main():
    # Leer los archivos de instancia desde los argumentos
    if len(sys.argv) < 2:
        print("Uso: python main.py <instancia1.txt> [instancia2.txt] ...")
        print("Ejemplo: python main.py instancias/01_facil.txt instancias/02_medio.txt instancias/03_dificil.txt")
        sys.exit(1)

    archivos = sys.argv[1:]

    # Abrir el archivo de resultados (sobreescribe si ya existe)
    salida = open(ARCHIVO_SALIDA, "w")
    imprimir("Resultados del experimento - Simulated Annealing TTP", salida)
    imprimir("Fecha: " + time.strftime("%Y-%m-%d %H:%M:%S"), salida)
    imprimir("Presupuesto: " + str(TIEMPO_MAX) + "s por ejecucion  |  Ejecuciones: " + str(N_EJECUCIONES), salida)

    # Acumular resultados de todas las instancias para el boxplot
    todos_resultados_boxplot = []
    nombres_boxplot          = []

    # Procesar cada instancia
    for ruta in archivos:
        imprimir("\n" + "=" * 62, salida)
        imprimir("Instancia: " + ruta, salida)
        imprimir("=" * 62, salida)

        # Cargar la instancia
        instancia = InstanciaTTP(ruta)
        imprimir("Ciudades: " + str(instancia.n_ciudades) +
                 " | Items: " + str(instancia.n_items) +
                 " | Capacidad: " + str(instancia.capacidad), salida)
        imprimir("Renting ratio: " + str(instancia.costo_renta), salida)
        imprimir("-" * 62, salida)

        resultados            = []
        mejor_tour_global     = None
        mejor_mochila_global  = None
        mejor_objetivo_global = float('-inf')
        obj_inicial           = None  # objetivo de la solución greedy inicial

        # Correr el SA N_EJECUCIONES veces
        for i in range(1, N_EJECUCIONES + 1):
            t_inicio = time.time()

            tour, mochila, objetivo, obj_ini, n_evals, historial, tiempo_hallazgo = simulated_annealing(
                instancia,
                tiempo_max = TIEMPO_MAX,
                semilla    = i * 137  # semilla diferente en cada ejecución
            )

            t_fin  = time.time()
            tiempo = t_fin - t_inicio

            # En la primera ejecución mostrar el objetivo de la solución inicial
            if i == 1:
                obj_inicial = obj_ini
                imprimir("  Solucion inicial (greedy): Z = " + f"{obj_inicial:.2f}", salida)
                imprimir("-" * 62, salida)

            resultados.append(objetivo)

            linea = ("  Ejecucion " + str(i).rjust(2) +
                     ": Z = " + f"{objetivo:14.2f}" +
                     "  |  evals = " + str(n_evals).rjust(7) +
                     "  |  tiempo = " + f"{tiempo:.1f}s")
            imprimir(linea, salida)

            # Guardar la mejor solución global entre todas las ejecuciones
            if objetivo > mejor_objetivo_global:
                mejor_objetivo_global = objetivo
                mejor_tour_global     = tour[:]
                mejor_mochila_global  = mochila[:]

        # Calcular estadísticas de las 10 ejecuciones
        mejor = max(resultados)
        media = sum(resultados) / len(resultados)

        suma_cuadrados = 0.0
        for r in resultados:
            suma_cuadrados += (r - media) ** 2
        desviacion = math.sqrt(suma_cuadrados / len(resultados))

        imprimir("-" * 62, salida)
        imprimir("  Mejor   : " + f"{mejor:.2f}", salida)
        imprimir("  Media   : " + f"{media:.2f}", salida)
        imprimir("  Desv.Est: " + f"{desviacion:.2f}", salida)

        # Recalcular el objetivo de la mejor solución para confirmar
        z_real = instancia.evaluar(mejor_tour_global, mejor_mochila_global)

        # Detalle de la mejor solución encontrada
        items_elegidos = []
        for i in range(instancia.n_items):
            if mejor_mochila_global[i] == 1:
                items_elegidos.append(i)

        ganancia_total = 0.0
        peso_total     = 0.0
        for i in items_elegidos:
            ganancia_total += instancia.items[i][0]
            peso_total     += instancia.items[i][1]

        imprimir("\n  Mejor solucion encontrada:", salida)
        imprimir("    OBJETIVO Z      : " + f"{z_real:.2f}", salida)
        if obj_inicial is not None:
            mejora = z_real - obj_inicial
            imprimir("    Mejora vs greedy: " + f"{mejora:+.2f}", salida)
        imprimir("    Items recogidos : " + str(len(items_elegidos)) + " / " + str(instancia.n_items), salida)
        imprimir("    Ganancia total  : " + f"{ganancia_total:.2f}", salida)
        imprimir("    Peso total      : " + f"{peso_total:.2f}" + " / " + f"{instancia.capacidad:.2f}", salida)
        imprimir("    Uso capacidad   : " + f"{100 * peso_total / instancia.capacidad:.1f}%", salida)

        # Guardar para el boxplot
        todos_resultados_boxplot.append(resultados)
        nombres_boxplot.append(ruta.split("/")[-1].replace(".txt", ""))

    salida.close()
    print("\nResultados guardados en: " + ARCHIVO_SALIDA)

    # Generar boxplot con todos los resultados
    if len(todos_resultados_boxplot) > 0:
        generar_boxplot(todos_resultados_boxplot, nombres_boxplot)

if __name__ == "__main__":
    main()
