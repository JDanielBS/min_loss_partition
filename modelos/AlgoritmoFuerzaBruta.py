from itertools import chain, combinations
from icecream import ic
import time
from modelos.matriz import MatrizTPM
from modelos.MetricasDistancia import MetricasDistancia
import numpy as np

class AlgoritmoFuerzaBruta():
    '''
    Fuerza bruta para encontrar todas las combinaciones posibles de una lista de elementos.
    '''

    def __init__(self, ruta, sistema):
        self.__matriz = MatrizTPM(ruta)
        self.__matriz.set_sistema(sistema)
        self.__emd = MetricasDistancia()

    def estrategia_fuerza_bruta(self):
        self.__matriz.condiciones_de_background()
        self.__matriz.obtener_estado_nodo()
        self.__matriz.matriz_subsistema()
        self.__matriz.get_matriz_subsistema()
        t_inicio = time.time()

        fuerza_bruta = self.fuerza_bruta()

        t_fin = time.time()
        t_proceso = t_fin - t_inicio

        return fuerza_bruta, t_proceso

    def generar_combinaciones(self, elementos):
        """
        Genera todas las combinaciones posibles de la lista dada,
        excluyendo la combinación completa.

        Args:
            elementos (list): Lista de elementos representados como tuplas.

        Returns:
            list: Lista de combinaciones.
        """
        # Lista para almacenar todas las combinaciones
        todas_combinaciones = []

        # Generar combinaciones de tamaño 1 hasta len(elementos) - 1
        for r in range(1, len(elementos)):
            combinaciones_r = list(combinations(elementos, r))
            todas_combinaciones.extend(combinaciones_r)

        return todas_combinaciones

    def fuerza_bruta(self):
        """
        Realiza el cálculo de EMD para todas las combinaciones posibles de la lista de elementos.

        Args:
            elementos (list): Lista de elementos representados como tuplas.

        Returns:
            list: Lista de resultados de EMD.
        """

        # Obtener la lista de elementos
        elementos = self.__matriz.pasar_cadena_a_lista()

        # Generar todas las combinaciones posibles
        combinaciones = self.generar_combinaciones(elementos)

        # Realizar el cálculo de EMD para cada combinación
        emd_minimo = float('inf')
        resultados_emd = []
        for combinacion in combinaciones:
            resultado_emd = self.realizar_emd(combinacion)

            resultado_json = {
                'emd': resultado_emd[0],
                'distribucion': resultado_emd[1].tolist(),
                'particion1': combinacion,
                'particion2': self.__matriz.encontrar_complemento_particion(combinacion)
            }

            # agregar el resultado al diccionario
            resultados_emd.append(resultado_json)

            if resultado_emd[0] < emd_minimo:
                emd_minimo = resultado_emd[0]

        # Eliminar del diccionarios aquellas que no tengan el emd mínimo
        resultados_emd = [resultado for resultado in resultados_emd if resultado['emd'] == emd_minimo]

        return resultados_emd

    def realizar_emd(self, lista):
        matriz_normal, matriz_complemento = self.__matriz.marginalizar_normal_complemento(lista)
        est_n, est_c = self.__matriz.get_estado_inicial_n_c()
        self.__matriz.limpiar_estados_inicialies()
        resultado_tensorial = self.__matriz.producto_tensorial_matrices(matriz_normal[0], matriz_complemento[0], matriz_normal[1], matriz_complemento[1], est_n, est_c)
        resultados_lista = np.array(resultado_tensorial.iloc[0].values.tolist(), dtype='float64')
        return (self.__emd.emd_pyphi(resultados_lista, self.__matriz.get_matriz_subsistema()), resultados_lista)
