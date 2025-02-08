import time
from modelos.matriz import MatrizTPM
from icecream import ic
from modelos.MetricasDistancia import MetricasDistancia
import numpy as np
from itertools import chain, combinations
import random
import json

class AlgoritmoPrincipal:
    def __init__(self, ruta, sistema):
        self.__matriz = MatrizTPM(ruta)
        self.__matriz.set_sistema(sistema)
        self.__emd = MetricasDistancia()
        self.__particiones_candidatas = []

    def estrategia3(self):
        """
        Realiza la estrategia 3 para encontrar la partición óptima de un subsistema.

        Returns:
            dict: Diccionario con la partición óptima y sus datos asociados.
            float: Tiempo de ejecución del proceso.
        """
        self.__matriz.condiciones_de_background()
        self.__matriz.obtener_estado_nodo()
        self.__matriz.matriz_subsistema()
        self.__matriz.get_matriz_subsistema()
        t_inicio = time.time()

        # Realizar la estrategia 3
        particion_inicial = self.generar_particion_inicial()
        self.__particiones_candidatas.clear()
        self.estrategia_kmeans_logica(particion_inicial, None)
        mejor_particion = self.guardar_mejor()

        t_fin = time.time()
        t_proceso = t_fin - t_inicio

        return mejor_particion, t_proceso
            
    def generar_particion_inicial(self):
        """
        Genera una partición inicial de manera aleatoria.

        Returns:
            list: Lista con algunos nodos del subsistema.
        """
        nodos = self.__matriz.pasar_cadena_a_lista()
        
        particion1 = []
        particion2 = []

        while not particion1 or not particion2:
            # Mezclar los nodos de manera aleatoria
            random.shuffle(nodos)

            # Generar un porcentaje de división aleatorio entre 20%-80% y 35%-65%
            porcentaje_division = random.uniform(0.2, 0.8)
            punto_division = int(len(nodos) * porcentaje_division)

            # Asignar nodos a los subconjuntos de manera desbalanceada
            particion1 = nodos[:punto_division]
            particion2 = nodos[punto_division:]

        return particion1
    
    def estrategia_kmeans_logica(self, particion_inicial, nodo_pasado):
        """
        Hace pruebas a partir de una partición inicial, pasando los nodos que mejoren
        el EMD de una mitad de la partición a la otra; esto se repite hasta que no se encuentren mejoras.

        Args:
            particion_inicial (list): Lista con algunos nodos del subsistema.
            nodo_pasado (tuple): Nodo que se movió en la iteración anterior.

        Returns:
            list: Lista con las particiones candidatas y sus datos asociados.
        """
        resultado = self.realizar_emd(particion_inicial)
        mejor_emd = resultado[0]
        distribucion = resultado[1]
        particion_complemento = self.__matriz.encontrar_complemento_particion(particion_inicial)
        
        mejor_particion = (particion_inicial, particion_complemento)

        if not nodo_pasado:
            p_sin_nodo_pasado = list(filter(lambda x: x != nodo_pasado, particion_inicial))
        else:
            p_sin_nodo_pasado = particion_inicial

        # Probar moviendo nodos de particion1 a particion2
        if len(p_sin_nodo_pasado) != 1 and mejor_emd != 0:
            for nodo in p_sin_nodo_pasado:
                nueva_particion1 = [n for n in particion_inicial if n != nodo]
                nueva_particion2 = particion_complemento + [nodo]
                resultado = self.realizar_emd(nueva_particion1)
                nuevo_emd = resultado[0]
                nueva_distribucion = resultado[1]
                if nuevo_emd < mejor_emd:
                    mejor_emd = nuevo_emd
                    mejor_particion = (nueva_particion1, nueva_particion2)
                    distribucion = nueva_distribucion
                    nodo_pasado = nodo
            
        if not nodo_pasado:
            p_sin_nodo_pasado = list(filter(lambda x: x != nodo_pasado, particion_complemento))
        else:
            p_sin_nodo_pasado = particion_complemento
            
        # Probar moviendo nodos de particion2 a particion1
        if len(p_sin_nodo_pasado) != 1 and mejor_emd != 0:
            for nodo in p_sin_nodo_pasado:
                nueva_particion2 = [n for n in particion_complemento if n != nodo]
                nueva_particion1 = particion_inicial + [nodo]
                resultado = self.realizar_emd(nueva_particion1)
                nuevo_emd = resultado[0]
                nueva_distribucion = resultado[1]
                    
                if nuevo_emd < mejor_emd:
                    mejor_emd = nuevo_emd
                    mejor_particion = (nueva_particion1, nueva_particion2)
                    distribucion = nueva_distribucion
                    nodo_pasado = nodo
                else:
                    nodo_pasado = None
            
        diccionario_particiones = {
            'emd': mejor_emd,
            'particion1': mejor_particion[0],
            'particion2': mejor_particion[1],
            'distribucion_teorica': self.__matriz.get_matriz_subsistema(),
            'distribucion_experimental': distribucion
        }   
        self.__particiones_candidatas.append(diccionario_particiones)

        # Verificar si el mejor EMD es cero
        if mejor_emd != 0 and mejor_particion != (particion_inicial, particion_complemento):
            self.estrategia_kmeans_logica(mejor_particion[0], nodo_pasado)

        return self.__particiones_candidatas
    
    def realizar_emd(self, lista):
        """
        Realiza el cálculo del EMD con una lista del subsistema, siendo esta la mitad 
        de una partición.

        Args:
            lista (list): Lista con algunos nodos del subsistema.

        Returns:
            tuple: Tupla con el valor del EMD y la distribución de probabilidad.
        """
        matriz_normal, matriz_complemento = self.__matriz.marginalizar_normal_complemento(lista)
        est_n, est_c = self.__matriz.get_estado_inicial_n_c()
        self.__matriz.limpiar_estados_inicialies()
        resultado_tensorial = self.__matriz.producto_tensorial_matrices(matriz_normal[0], matriz_complemento[0], matriz_normal[1], matriz_complemento[1], est_n, est_c)
        resultados_lista = np.array(resultado_tensorial.iloc[0].values.tolist(), dtype='float64')
        return (self.__emd.emd_pyphi(resultados_lista, self.__matriz.get_matriz_subsistema()), resultados_lista)

    def guardar_mejor(self):
        """
        Guarda la última partición encontrada en una archivo JSON

        Returns:
            dict: Diccionario con la partición óptima y sus datos asociados. 
        """
        mejor_particion = self.__particiones_candidatas.pop()

        p1, p2 = mejor_particion['particion1'], mejor_particion['particion2']
        p_formateada = self.format_tuples(p1, p2)

        # Convertimos las distribuciones a listas y creamos el diccionario
        diccionario_particiones = {
            'emd': mejor_particion['emd'],  # Es un float
            'particion1': p1,  # Es una lista de tuplas
            'particion2': p2,  # Es una lista de tuplas
            'particion_formateada': p_formateada,  # Formato futuro y presente
            'distribucion_teorica': mejor_particion['distribucion_teorica'].tolist(),  # Convertimos numpy.array a lista
            'distribucion_experimental': mejor_particion['distribucion_experimental'].tolist()  # Convertimos numpy.array a lista
        }

        # Guardamos en un archivo JSON
        with open('archivos/particion_optima.json', 'w') as f:
            json.dump(diccionario_particiones, f, indent=4)  # Formato legible
        
        return diccionario_particiones

    def format_tuples(self, list_of_tuples1, list_of_tuples2):
        """
        Formatea dos listas de tuplas en el formato deseado.

        Args:
            list_of_tuples1 (list): Primera lista de tuplas (lado, índice).
            list_of_tuples2 (list): Segunda lista de tuplas (lado, índice).

        Returns:
            list: Lista formateada con los elementos separados en futuro y presente.
        """
        def process_list(tuples):
            # Filtra y organiza los elementos por futuro (1) y presente (0)
            future = [chr(65 + t[1]) for t in tuples if t[0] == 1]  # Convierte índices a letras
            present = [chr(65 + t[1]) for t in tuples if t[0] == 0]

            # Si alguna lista está vacía, agrega el símbolo ∅
            future = future if future else ['∅']
            present = present if present else ['∅']

            return [future, present]

        # Procesa ambas listas
        formatted_list1 = process_list(list_of_tuples1)
        formatted_list2 = process_list(list_of_tuples2)

        # Retorna ambas listas formateadas dentro de una lista principal
        return [formatted_list2, formatted_list1]
