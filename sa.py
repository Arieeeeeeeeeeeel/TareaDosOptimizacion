import random
import math
import time

# Parámetros del SA 
N_MUESTRAS_CALIBRACION = 500   # movimientos de muestra para estimar temperatura inicial
TEMPERATURA_MIN        = 1.0   # temperatura mínima para detener el loop
PORCENTAJE_ACEPTACION  = 0.80  # fracción de movimientos malos a aceptar al inicio


# Construcción de solución inicial

# Construye un tour usando el algoritmo del vecino más cercano
def tour_inicial(instancia):
    n = instancia.n_ciudades
    visitado = [False] * n
    tour = []

    # Partir desde la ciudad 0
    ciudad_actual = 0
    visitado[0] = True
    tour.append(0)

    # En cada paso ir a la ciudad no visitada más cercana
    for _ in range(n - 1):
        mejor_ciudad    = -1
        menor_distancia = float('inf')

        for ciudad in range(n):
            if not visitado[ciudad]:
                d = instancia.distancias[ciudad_actual][ciudad]
                if d < menor_distancia:
                    menor_distancia = d
                    mejor_ciudad    = ciudad

        tour.append(mejor_ciudad)
        visitado[mejor_ciudad] = True
        ciudad_actual = mejor_ciudad

    return tour


# Selecciona ítems de forma greedy según su ratio ganancia/peso
def mochila_inicial(instancia):
    # Calcular el ratio ganancia/peso de cada ítem
    ratios = []
    for i in range(instancia.n_items):
        ganancia = instancia.items[i][0]
        peso     = instancia.items[i][1]
        ratios.append((ganancia / peso, i))

    # Ordenar de mayor a menor ratio
    ratios.sort(reverse=True)

    mochila     = [0] * instancia.n_items
    peso_actual = 0.0

    # Agregar ítems mientras quepan
    for _, indice in ratios:
        peso_item = instancia.items[indice][1]
        if peso_actual + peso_item <= instancia.capacidad:
            mochila[indice] = 1
            peso_actual    += peso_item

    return mochila, peso_actual


# Operadores de vecindad

# Movimiento 2-opt: invierte un segmento aleatorio del tour
def dos_opt(tour):
    n = len(tour)

    # Elegir dos posiciones distintas al azar
    i = random.randint(0, n - 1)
    j = random.randint(0, n - 1)
    while i == j:
        j = random.randint(0, n - 1)

    # Asegurarse de que i < j
    if i > j:
        i, j = j, i

    # Construir nuevo tour invirtiendo el segmento entre i y j
    segmento_invertido = tour[i:j + 1][::-1]
    nuevo_tour = tour[:i] + segmento_invertido + tour[j + 1:]
    return nuevo_tour


# Movimiento bit-flip: agrega o quita un ítem de la mochila
# Devuelve (nueva_mochila, nuevo_peso, delta_ganancia) o (None, 0, 0) si falla
def flip_item(instancia, mochila, peso_actual):
    indice = random.randint(0, instancia.n_items - 1)

    nueva_mochila = mochila[:]  # copiar la mochila para no modificar la original

    if mochila[indice] == 1:
        # El ítem estaba en la mochila: quitarlo
        nueva_mochila[indice] = 0
        nuevo_peso     = peso_actual - instancia.items[indice][1]
        delta_ganancia = -instancia.items[indice][0]
        return nueva_mochila, nuevo_peso, delta_ganancia

    else:
        # El ítem no estaba: intentar agregarlo si cabe
        peso_item = instancia.items[indice][1]
        if peso_actual + peso_item <= instancia.capacidad:
            nueva_mochila[indice] = 1
            nuevo_peso     = peso_actual + peso_item
            delta_ganancia = instancia.items[indice][0]
            return nueva_mochila, nuevo_peso, delta_ganancia
        else:
            # No cabe en la mochila
            return None, 0, 0


# Movimiento de intercambio: quita un ítem y agrega otro diferente
# Sirve como respaldo cuando flip_item falla por capacidad llena
# Devuelve (nueva_mochila, nuevo_peso, delta_ganancia) o (None, 0, 0) si falla
def intercambio_items(instancia, mochila, peso_actual):
    MAX_INTENTOS = 20

    for _ in range(MAX_INTENTOS):
        idx_quitar  = random.randint(0, instancia.n_items - 1)
        idx_agregar = random.randint(0, instancia.n_items - 1)

        # Necesitamos uno adentro para quitar y uno afuera para agregar
        if mochila[idx_quitar] != 1 or mochila[idx_agregar] != 0:
            continue
        if idx_quitar == idx_agregar:
            continue

        # Calcular si el intercambio cabe en la mochila
        nuevo_peso = (peso_actual
                      - instancia.items[idx_quitar][1]
                      + instancia.items[idx_agregar][1])

        if nuevo_peso <= instancia.capacidad:
            nueva_mochila = mochila[:]
            nueva_mochila[idx_quitar]  = 0
            nueva_mochila[idx_agregar] = 1
            delta_ganancia = (instancia.items[idx_agregar][0]
                              - instancia.items[idx_quitar][0])
            return nueva_mochila, nuevo_peso, delta_ganancia

    return None, 0, 0


# -------------------------------------------------------
# Algoritmo principal: Simulated Annealing
# -------------------------------------------------------

def simulated_annealing(instancia, tiempo_max=60.0, semilla=None):
    if semilla is not None:
        random.seed(semilla)

    # --- Solución inicial ---
    tour                 = tour_inicial(instancia)
    mochila, peso_actual = mochila_inicial(instancia)

    # Calcular ganancia inicial una sola vez — después se actualiza en O(1)
    ganancia_actual = 0.0
    for i in range(instancia.n_items):
        if mochila[i] == 1:
            ganancia_actual += instancia.items[i][0]

    tiempo_viaje_actual = instancia.calcular_tiempo_viaje(tour, mochila)
    objetivo_actual     = ganancia_actual - instancia.costo_renta * tiempo_viaje_actual
    objetivo_inicial    = objetivo_actual  # guardar para reportar mejora al final

    # Guardar la mejor solución encontrada hasta ahora
    mejor_tour     = tour[:]
    mejor_mochila  = mochila[:]
    mejor_objetivo = objetivo_actual

    # -------------------------------------------------------
    # Calibración de temperatura inicial por muestreo
    # Genera N_MUESTRAS_CALIBRACION movimientos al azar, mide sus deltas
    # y fija T0 para aceptar PORCENTAJE_ACEPTACION de los movimientos malos
    # -------------------------------------------------------
    deltas_negativos  = []
    t_muestreo_inicio = time.time()

    for _ in range(N_MUESTRAS_CALIBRACION):
        if random.random() < 0.5:
            # Muestra de movimiento de tour
            nuevo_tour_m = dos_opt(tour)
            nuevo_t_m    = instancia.calcular_tiempo_viaje(nuevo_tour_m, mochila)
            nuevo_obj_m  = ganancia_actual - instancia.costo_renta * nuevo_t_m
        else:
            # Muestra de movimiento de mochila
            nm, np, dg = flip_item(instancia, mochila, peso_actual)
            if nm is None:
                nm, np, dg = intercambio_items(instancia, mochila, peso_actual)
            if nm is None:
                continue
            nuevo_t_m   = instancia.calcular_tiempo_viaje(tour, nm)
            nuevo_obj_m = (ganancia_actual + dg) - instancia.costo_renta * nuevo_t_m

        delta = nuevo_obj_m - objetivo_actual
        if delta < 0:
            deltas_negativos.append(-delta)  # guardar la magnitud positiva del empeoramiento

    t_muestreo = time.time() - t_muestreo_inicio

    # Fijar T0: exp(-media_delta / T0) = PORCENTAJE_ACEPTACION
    if len(deltas_negativos) > 0:
        media_delta = sum(deltas_negativos) / len(deltas_negativos)
        temperatura = -media_delta / math.log(PORCENTAJE_ACEPTACION)
    else:
        temperatura = max(abs(objetivo_actual) * 0.01, 1.0)

    # Estimar cuántas iteraciones caben en el tiempo disponible
    # y calcular alpha para que T llegue a TEMPERATURA_MIN justo al acabar
    if t_muestreo > 0:
        iters_por_segundo = N_MUESTRAS_CALIBRACION / t_muestreo
    else:
        iters_por_segundo = 1000.0

    iters_estimadas = int(iters_por_segundo * tiempo_max)
    if iters_estimadas < 1:
        iters_estimadas = 1

    if temperatura > TEMPERATURA_MIN:
        alpha = (TEMPERATURA_MIN / temperatura) ** (1.0 / iters_estimadas)
    else:
        alpha = 0.999  # valor por defecto si la calibración da T0 muy bajo

    # Loop principal
    n_evaluaciones  = 0
    tiempo_inicio   = time.time()
    tiempo_hallazgo = 0.0  # segundo en que se encontró la última mejor solución

    # Historial para graficar la convergencia: guarda (tiempo, mejor_objetivo)
    # cada un segundo aproximadamente
    historial          = []
    proximo_registro   = 0.0
    INTERVALO_REGISTRO = 1.0

    while True:
        tiempo_transcurrido = time.time() - tiempo_inicio

        # Verificar condiciones de parada
        if tiempo_transcurrido >= tiempo_max:
            break
        if temperatura < TEMPERATURA_MIN:
            break

        # Registrar el progreso cada INTERVALO_REGISTRO segundos
        if tiempo_transcurrido >= proximo_registro:
            historial.append((tiempo_transcurrido, mejor_objetivo))
            proximo_registro += INTERVALO_REGISTRO

        if random.random() < 0.5:
            # Movimiento de tour: 2-opt
            # La ganancia no cambia al cambiar el orden del tour
            nuevo_tour     = dos_opt(tour)
            nueva_mochila  = mochila
            nuevo_peso     = peso_actual
            nueva_ganancia = ganancia_actual

        else:
            # Movimiento de mochila: bit-flip, con intercambio como respaldo
            nuevo_tour = tour
            nueva_mochila, nuevo_peso, delta_ganancia = flip_item(instancia, mochila, peso_actual)

            if nueva_mochila is None:
                # flip falló (mochila llena): intentar un intercambio
                nueva_mochila, nuevo_peso, delta_ganancia = intercambio_items(instancia, mochila, peso_actual)

            if nueva_mochila is None:
                # Ningún movimiento válido encontrado
                temperatura *= alpha
                continue

            nueva_ganancia = ganancia_actual + delta_ganancia

        # Evaluar nueva solución usando calcular_tiempo_viaje (no recalcula ganancia)
        nuevo_tiempo   = instancia.calcular_tiempo_viaje(nuevo_tour, nueva_mochila)
        nuevo_objetivo = nueva_ganancia - instancia.costo_renta * nuevo_tiempo
        n_evaluaciones += 1

        diferencia = nuevo_objetivo - objetivo_actual

        # Criterio de aceptación del Simulated Annealing
        if diferencia > 0:
            # La nueva solución es mejor: aceptar siempre
            aceptar = True
        else:
            # La nueva solución es peor: aceptar con probabilidad e^(diferencia/temperatura)
            probabilidad = math.exp(diferencia / temperatura)
            aceptar = random.random() < probabilidad

        # Si se acepta, actualizar la solución actual
        if aceptar:
            tour            = nuevo_tour
            mochila         = nueva_mochila
            peso_actual     = nuevo_peso
            ganancia_actual = nueva_ganancia  # actualización O(1)
            objetivo_actual = nuevo_objetivo

            # Si es la mejor solución encontrada, guardarla
            if objetivo_actual > mejor_objetivo:
                mejor_objetivo  = objetivo_actual
                mejor_tour      = tour[:]
                mejor_mochila   = mochila[:]
                tiempo_hallazgo = time.time() - tiempo_inicio

        # Reducir la temperatura
        temperatura *= alpha

    # Registrar el último punto del historial
    historial.append((time.time() - tiempo_inicio, mejor_objetivo))

    return mejor_tour, mejor_mochila, mejor_objetivo, objetivo_inicial, n_evaluaciones, historial, tiempo_hallazgo
