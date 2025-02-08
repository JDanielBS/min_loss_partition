import pyphi
import time
import copy
import numpy as np
import pandas as pd
from icecream import ic
import itertools as it
import pyphi.compute
from pyphi.models.cuts import Bipartition, KPartition, Part
from pyphi.labels import NodeLabels

class PyphiCode:

    def __init__(self, route, node_labels, i_state, c_system):
        self.__route = route
        self.__node_labels = node_labels
        self.__i_state = i_state
        self.__c_system = c_system

    def pyphi_partition(self, mechanism_e, purview_e):
        """
        Ejecuta el cálculo de la partición óptima de un subsistema dados un 
        subsistema presente y un subsistema futuro.

        Args:
            mechanism_e (list): Subsistema presente.
            purview_e (list): Subsistema futuro.

        Returns:
            dict: Diccionario con la partición óptima y sus datos asociados
        """
        # Define el símbolo para el conjunto vacío
        VOID: str = '∅'
        
        # Configura PyPhi
        pyphi.config.PARTITION_TYPE = 'BI'

        # Inicia registro de tiempo 
        t_inicio = time.time()

        # Lee el archivo Excel
        df = pd.read_excel(self.__route, header=None, engine='openpyxl')

        # Convierte el DataFrame a un numpy.ndarray
        tpm = df.to_numpy()

        # Define los nombres de los nodos
        node_labels = self.__node_labels

        # Crea un Network a partir de la TPM
        network = pyphi.Network(tpm, node_labels=node_labels)

        # Establece el estado inicial
        state = self.__i_state

        # Establece el sistema candidato
        candidate_nodes = self.__c_system

        # Establecer subsistema
        subsystem = pyphi.Subsystem(network, state, nodes=candidate_nodes)

        # Calcula la causa y el efecto
        mip = subsystem.effect_mip(mechanism_e, purview_e)

        # Finaliza registro de tiempo
        t_fin = time.time()
        t_proceso = t_fin - t_inicio

        # ? Reconstrucción de resultados
        integrated_info: float = mip.phi

        repertoire = mip.repertoire
        repertoire = repertoire.squeeze()

        part_reper = mip.partitioned_repertoire
        part_reper = part_reper.squeeze()

        sub_states: list[tuple[int, ...]] = copy.copy(list(self.lil_endian_int(repertoire.ndim)))

        distribution: list[float] = [repertoire[sub_state] for sub_state in sub_states]
        part_distrib: list[float] = [part_reper[sub_state] for sub_state in sub_states]

        min_info_part: KPartition = mip.partition

        dual: Part = min_info_part.parts[True]
        prim: Part = min_info_part.parts[False]
        dual_mech, dual_purv = dual.mechanism, dual.purview
        prim_mech, prim_purv = prim.mechanism, prim.purview


        # Lista que tiene las particiones, cada partición tiene una lista con las variables en presente y en futuro
        min_info_part: list[list[list[str], list[str]], list[list[str], list[str]]] = [
            [
                [node_labels[i] for i in prim_purv] if prim_purv else [VOID],
                [node_labels[i] for i in prim_mech] if prim_mech else [VOID],
            ],
            [
                [node_labels[i] for i in dual_purv] if dual_purv else [VOID],
                [node_labels[i] for i in dual_mech] if dual_mech else [VOID],
            ],
        ]

        partition_info = {
            'min_info_part': min_info_part,
            'emd': integrated_info,
            'distribution': distribution,
            'part_distrib': part_distrib,
            'dual_purv': dual_purv,
            'dual_mech': dual_mech,
            'prim_purv': prim_purv,
            'prim_mech': prim_mech
        }

        return partition_info, t_proceso

    def lil_endian_int(self, n: int):
        """
        Genera una lista de enteros que representan los números en
        little-endian para los índices en ``range(2**n)``.

        Args:
            n (int): Número de bits.
        """
        for state in it.product((0, 1), repeat=n):
            yield state[::-1]

