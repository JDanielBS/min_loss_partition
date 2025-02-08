from pyemd import emd
from numpy.typing import NDArray
import numpy as np

class MetricasDistancia:    
    
    def emd_pyphi(self, u: NDArray[np.float64], v: NDArray[np.float64]) -> float:
        """
        Calcula la Earth Mover's Distance (EMD) entre dos distribuciones de probabilidad u y v.
        La distancia de Hamming es utilizada como métrica de base.

        Args:
            u (NDArray[np.float64]): Distribución de probabilidad u.
            v (NDArray[np.float64]): Distribución de probabilidad v.

        Returns:
            float: Distancia de EMD entre u y v.
        """
        n: int = len(u)
        costs: NDArray[np.float64] = np.empty((n, n))

        for i in range(n):
            costs[i, :i] = [self.hamming_distance(i, j) for j in range(i)]
            costs[:i, i] = costs[i, :i]
        np.fill_diagonal(costs, 0)

        cost_matrix: NDArray[np.float64] = np.array(costs, dtype=np.float64)
        return emd(u, v, cost_matrix)

    def hamming_distance(self, a: int, b: int) -> int:
        """
        Calcula la distancia de Hamming entre dos números enteros.
        El código comentado es para versiones de Python 3.10 o superiores.

        Args:
            a (int): Número entero.
            b (int): Número entero.

        Returns:
            list: Lista con las particiones candidatas y sus datos asociados.
        """
        return self.bit_count(a ^ b)
        # return (a ^ b).bit_count()
    
    def bit_count(self, n):
        """
        Calcula la cantidad de bits encendidos en la representación binaria de un número entero.

        Args:
            n (int): Número entero.

        Returns:
            int: Cantidad de bits encendidos. 
        """
        return bin(n).count('1')