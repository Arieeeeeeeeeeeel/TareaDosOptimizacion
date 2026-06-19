import math
#Algoritmo tepepe
# Clase que representa una instancia del problema TTP
class InstanciaTTP:

    def __init__(self, ruta_archivo):
        # Atributos del problema
        self.nombre       = ""
        self.n_ciudades   = 0
        self.n_items      = 0
        self.capacidad    = 0.0
        self.vel_min      = 0.1
        self.vel_max      = 1.0
        self.costo_renta  = 1.0
        self.tipo_dist    = "CEIL_2D"
        self.coordenadas  = []   # lista de tuplas (x, y) por ciudad
        self.items        = []   # lista de tuplas (ganancia, peso, ciudad)

        self.leer_archivo(ruta_archivo)
        self.calcular_distancias()
        self.preparar_items_por_ciudad()

    # Lee el archivo de instancia y carga los datos
    def leer_archivo(self, ruta):
        archivo = open(ruta, 'r')
        lineas = archivo.readlines()
        archivo.close()

        seccion = None  # indica en qué sección del archivo estamos

        for linea in lineas:
            linea = linea.strip()
            if linea == "":
                continue

            linea_upper = linea.upper()

            # Detectar inicio de la sección de coordenadas
            if "NODE_COORD_SECTION" in linea_upper:
                seccion = "coordenadas"
                continue

            # Detectar inicio de la sección de ítems
            if "ITEMS SECTION" in linea_upper:
                seccion = "items"
                continue

            # Leer parámetros del encabezado (tienen formato "CLAVE: VALOR")
            if seccion is None and ":" in linea:
                clave, _, valor = linea.partition(":")
                clave = clave.strip().upper().replace("_", " ")
                valor = valor.strip()

                if "PROBLEM NAME"    in clave: self.nombre      = valor
                elif "DIMENSION"     in clave: self.n_ciudades  = int(valor)
                elif "NUMBER OF ITEMS" in clave: self.n_items   = int(valor)
                elif "CAPACITY"      in clave: self.capacidad   = float(valor)
                elif "MIN SPEED"     in clave: self.vel_min     = float(valor)
                elif "MAX SPEED"     in clave: self.vel_max     = float(valor)
                elif "RENTING RATIO" in clave: self.costo_renta = float(valor)
                elif "EDGE WEIGHT TYPE" in clave: self.tipo_dist = valor
                continue

            # Leer coordenadas: cada línea tiene "indice x y"
            if seccion == "coordenadas":
                partes = linea.split()
                if len(partes) >= 3:
                    x = float(partes[1])
                    y = float(partes[2])
                    self.coordenadas.append((x, y))

            # Leer ítems: cada línea tiene "indice ganancia peso ciudad"
            elif seccion == "items":
                partes = linea.split()
                if len(partes) >= 4:
                    ganancia = float(partes[1])
                    peso     = float(partes[2])
                    ciudad   = int(partes[3]) - 1  # pasar a índice 0
                    self.items.append((ganancia, peso, ciudad))

    # Construye la matriz de distancias entre todas las ciudades
    def calcular_distancias(self):
        n = self.n_ciudades
        # Crear matriz n x n llena de ceros
        self.distancias = [[0] * n for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                x1, y1 = self.coordenadas[i]
                x2, y2 = self.coordenadas[j]
                dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

                # Redondear según el tipo de distancia del archivo
                if "CEIL" in self.tipo_dist.upper():
                    dist = math.ceil(dist)
                else:
                    dist = int(dist + 0.5)

                self.distancias[i][j] = dist
                self.distancias[j][i] = dist

    # Prepara una lista de ítems por ciudad para acelerar la evaluación
    def preparar_items_por_ciudad(self):
        # items_por_ciudad[c] = lista de índices de ítems que están en ciudad c
        self.items_por_ciudad = [[] for _ in range(self.n_ciudades)]
        for i in range(self.n_items):
            ciudad = self.items[i][2]
            self.items_por_ciudad[ciudad].append(i)

    # Calcula solo el tiempo de viaje (sin la ganancia) — usado por el SA para evaluar rápido
    def calcular_tiempo_viaje(self, tour, mochila):
        peso_actual  = 0.0
        tiempo_total = 0.0

        for k in range(self.n_ciudades):
            ciudad_actual    = tour[k]
            ciudad_siguiente = tour[(k + 1) % self.n_ciudades]

            for i in self.items_por_ciudad[ciudad_actual]:
                if mochila[i] == 1:
                    peso_actual += self.items[i][1]

            velocidad = self.vel_max - (peso_actual / self.capacidad) * (self.vel_max - self.vel_min)
            if velocidad < self.vel_min:
                velocidad = self.vel_min

            distancia = self.distancias[ciudad_actual][ciudad_siguiente]
            tiempo_total += distancia / velocidad

        return tiempo_total

    # Calcula el valor de la función objetivo para un tour y una mochila dados
    def evaluar(self, tour, mochila):
        # Calcular la ganancia total de los ítems seleccionados
        ganancia_total = 0.0
        for i in range(self.n_items):
            if mochila[i] == 1:
                ganancia_total += self.items[i][0]

        # Simular el recorrido para calcular el tiempo total de viaje
        peso_actual  = 0.0
        tiempo_total = 0.0

        for k in range(self.n_ciudades):
            ciudad_actual    = tour[k]
            ciudad_siguiente = tour[(k + 1) % self.n_ciudades]

            # Recoger los ítems de la ciudad actual
            for i in self.items_por_ciudad[ciudad_actual]:
                if mochila[i] == 1:
                    peso_actual += self.items[i][1]

            # La velocidad depende del peso que lleva el ladrón
            velocidad = self.vel_max - (peso_actual / self.capacidad) * (self.vel_max - self.vel_min)
            if velocidad < self.vel_min:
                velocidad = self.vel_min

            # Tiempo = distancia / velocidad
            distancia = self.distancias[ciudad_actual][ciudad_siguiente]
            tiempo_total += distancia / velocidad

        # Objetivo: maximizar ganancia menos costo de renta por tiempo
        return ganancia_total - self.costo_renta * tiempo_total
