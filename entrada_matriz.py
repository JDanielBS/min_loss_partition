import numpy as np
import pandas as pd
from modelos.AlgoritmoPrincipal import AlgoritmoPrincipal
from modelos.LectorExcel import LectorExcel
from icecream import ic
from modelos.matriz import MatrizTPM
from numpy.typing import NDArray
from functools import reduce

def main():
    excel = LectorExcel()
    tensor = excel.leer() # listado de np NDarray 
    tensor_invertido = [np.array(m) for m in reversed(tensor)]

    # Aplicar el producto tensorial en el orden inverso
    resultados = []
    for filas in zip(*tensor_invertido):  # Itera fila a fila de cada matriz en el tensor invertido
        # Multiplica los vectores en el orden inverso (de último a primero)
        producto = reduce(lambda x, y: np.kron(x, y), filas)  # `np.kron` es el producto tensorial
        resultados.append(producto)

    # Convertimos la lista `resultados` a un arreglo numpy con la forma final
    resultado_matriz = np.array(resultados)
    # exportar a csv
    pd.DataFrame(resultado_matriz).to_csv('resultado_10.csv', index=False, header=False)

if __name__ == '__main__':
    main()