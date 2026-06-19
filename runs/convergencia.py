import sys
import os
import time

# Permitir importar sa.py y ttp.py, que estan un nivel mas arriba (carpeta del proyecto)
DIR_BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(DIR_BASE, ".."))

from ttp import InstanciaTTP
from sa  import simulated_annealing

# Estudio de convergencia: una corrida larga por instancia,
# repetida con varias semillas, guardando como va mejorando
# el objetivo Z a lo largo del tiempo

INSTANCIAS = [
    os.path.join(DIR_BASE, "..", "instancias", "01_facil.txt"),
    os.path.join(DIR_BASE, "..", "instancias", "02_medio.txt"),
    os.path.join(DIR_BASE, "..", "instancias", "03_dificil.txt"),
]

SEMILLAS = [42, 7, 123]   # 3 semillas distintas por instancia

TIEMPO_MAX      = 600.0   # 10 minutos por corrida
ARCHIVO_SALIDA  = os.path.join(DIR_BASE, "..", "resultados", "resultadosConvergencia_informe.txt")
ARCHIVO_GRAFICO = os.path.join(DIR_BASE, "..", "graficos", "convergencia_informe.png")


# Imprime en pantalla y escribe en el archivo
def imprimir(texto, archivo):
    print(texto)
    archivo.write(texto + "\n")


# Genera un gráfico con las curvas de convergencia por instancia
# (una línea por semilla en cada subgráfico)
def generar_grafico(resultados, nombres):
    try:
        import matplotlib.pyplot as plt

        fig, ejes = plt.subplots(len(resultados), 1, figsize=(9, 12))

        for k in range(len(resultados)):
            for semilla, historial in resultados[k]:
                tiempos   = [punto[0] for punto in historial]
                objetivos = [punto[1] for punto in historial]
                ejes[k].plot(tiempos, objetivos, label="semilla " + str(semilla))

            ejes[k].set_title("Convergencia - " + nombres[k])
            ejes[k].set_xlabel("Tiempo (s)")
            ejes[k].set_ylabel("Mejor Z")
            ejes[k].grid(True, linestyle='--', alpha=0.7)
            ejes[k].legend()

        plt.tight_layout()
        plt.savefig(ARCHIVO_GRAFICO)
        plt.close()
        print("\nGrafico guardado en: " + ARCHIVO_GRAFICO)

    except ImportError:
        # Si matplotlib no está instalado, guardar los datos en CSV
        archivo_csv = open(os.path.join(DIR_BASE, "..", "resultados", "datos_convergencia.csv"), "w")
        archivo_csv.write("instancia,semilla,tiempo,objetivo\n")
        for nombre, lista_semillas in zip(nombres, resultados):
            for semilla, historial in lista_semillas:
                for tiempo_punto, objetivo_punto in historial:
                    archivo_csv.write(nombre + "," + str(semilla) + "," +
                                       f"{tiempo_punto:.2f}" + "," + f"{objetivo_punto:.4f}\n")
        archivo_csv.close()
        print("\nmatplotlib no disponible. Datos guardados en: datos_convergencia.csv")


def main():
    salida = open(ARCHIVO_SALIDA, "w")
    imprimir("Estudio de convergencia - Simulated Annealing TTP", salida)
    imprimir("Fecha: " + time.strftime("%Y-%m-%d %H:%M:%S"), salida)
    imprimir("Tiempo por corrida: " + str(TIEMPO_MAX) + "s  |  Semillas: " + str(SEMILLAS), salida)

    resultados = []   # por instancia: lista de (semilla, historial)
    nombres    = []

    for ruta in INSTANCIAS:
        imprimir("\n" + "=" * 62, salida)
        imprimir("Instancia: " + ruta, salida)
        imprimir("=" * 62, salida)

        instancia = InstanciaTTP(ruta)
        imprimir("Ciudades: " + str(instancia.n_ciudades) +
                 " | Items: " + str(instancia.n_items), salida)

        lista_semillas = []

        for semilla in SEMILLAS:
            imprimir("-" * 62, salida)
            imprimir("  Semilla: " + str(semilla), salida)

            tour, mochila, objetivo, obj_ini, n_evals, historial, tiempo_hallazgo = simulated_annealing(
                instancia,
                tiempo_max = TIEMPO_MAX,
                semilla    = semilla
            )

            imprimir("    Solucion inicial (greedy): Z = " + f"{obj_ini:.2f}", salida)
            imprimir("    Mejor Z final            : Z = " + f"{objetivo:.2f}", salida)
            imprimir("    Evaluaciones totales     : " + str(n_evals), salida)

            # Guardar el historial completo (tiempo, mejor_objetivo)
            imprimir("    Historial (tiempo_s -> mejor_Z):", salida)
            for tiempo_punto, objetivo_punto in historial:
                imprimir("      " + f"{tiempo_punto:6.1f}s -> " + f"{objetivo_punto:14.2f}", salida)

            lista_semillas.append((semilla, historial))

        resultados.append(lista_semillas)
        nombres.append(os.path.basename(ruta).replace(".txt", ""))

    salida.close()
    print("\nResultados guardados en: " + ARCHIVO_SALIDA)

    generar_grafico(resultados, nombres)


if __name__ == "__main__":
    main()
