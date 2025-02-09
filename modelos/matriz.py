import pandas as pd
import itertools
import math
from icecream import ic
import numpy as np
from modelos.sistema import Sistema
# import dask.dataframe as dd


class MatrizTPM:
    def __init__(self, route = None, array = None):
        self.__matriz = pd.DataFrame(array) if route is None else pd.read_csv(route, sep=",", header=None)
        self.__matriz_candidata = None
        self.__matriz_subsistema = None
        self.__matriz_no_futuro = None
        self.__matriz_estado_nodo_dict = {}
        self.__matriz_estado_nodo_marginalizadas = {}
        self.__listado_candidatos = []
        self.__listado_valores_futuros = []
        self.__listado_valores_presentes = []
        self.__sistema = None
        self.__estado_inicial_subsistema= None
        self.__estado_i_normal = ''
        self.__estado_i_complemento = ''
        self.indexar_matriz() if route is not None else self.__matriz.values

    def get_matriz(self):
        return print(self.__matriz)
    
    def get_matriz_subsistema(self):
        return self.__matriz_subsistema

    def set_sistema(self, sistema):
        self.__sistema = sistema
      
    def get_listados(self):
        # Print detallado para depurar los valores de las listas
        print(f"Listado candidatos: {self.__listado_candidatos}")
        print(f"Listado valores futuros: {self.__listado_valores_futuros}")
        print(f"Listado valores presentes: {self.__listado_valores_presentes}")
    
    def get_valores_presentes(self):
        return self.__listado_valores_presentes
    
    def get_diccionario(self):
        return self.__matriz_estado_nodo_dict
    
    def get_dic_marginalizadas(self):
        return self.__matriz_estado_nodo_marginalizadas
    
    def get_estado_inicial_n_c(self):
        return self.__estado_i_normal, self.__estado_i_complemento
    
    def get_datos_para_kmeans(self):
        datos = self.__matriz_subsistema
        return datos

    """
    ------------------------------------------------------------------------------------------------
    Poner en notación little endian
    ------------------------------------------------------------------------------------------------
    """

    def indexar_matriz(self):
        """
        Indexa las filas y columnas de la matriz con etiquetas en formato little-endian
        """
        filas = self.__matriz.shape[0]
        columnas = self.__matriz.shape[1]

        num_etiquetas = max(filas, columnas)
        num_bits = math.ceil(math.log2(num_etiquetas))

        labels = list(self.lil_endian_int(num_bits, num_etiquetas))

        if len(labels) >= columnas:
            self.__matriz.columns = labels[:columnas]
        if len(labels) >= filas:
            self.__matriz.index = labels[:filas]

    def lil_endian_int(self, n: int, num_etiquetas: int):
        """
        Genera una lista de enteros que representan los números en
        little-endian para los índices en ``range(2**n)``.

        Args:
            n (int): Número de bits.
        """
        for state in range(num_etiquetas):
            yield bin(state)[2:].zfill(n)[::-1]
    
    def indexar_array(self):
        """
        Indexa las filas y columnas de la matriz con etiquetas en formato little-endian

        Returns:
            pd.DataFrame: Matriz indexada
        """
        filas = self.__matriz.shape[0]
        columnas = self.__matriz.shape[1]

        num_bits_filas = math.ceil(math.log2(filas))
        num_bits_col = math.ceil(math.log2(columnas))

        labels_filas = list(self.lil_endian_int(num_bits_filas, filas))
        labels_columnas = list(self.lil_endian_int(num_bits_col, columnas))

        self.__matriz.columns = labels_columnas
        self.__matriz.index = labels_filas

        return self.__matriz

    """
    ------------------------------------------------------------------------------------------------
    Condiciones de background
    ------------------------------------------------------------------------------------------------
    """
    def condiciones_de_background(self):
        """
        Elimina las filas y columnas de la matriz que no cumplen con las condiciones de background.

        Returns:
            pd.DataFrame: Matriz con condiciones de background aplicadas
        """
        self.__listado_candidatos = self.obtener_indices(self.__sistema.get_sistema_candidato(), "1")
        self.__listado_valores_futuros = self.obtener_indices(self.__sistema.get_subsistema_futuro(), "1")
        self.__listado_valores_presentes = self.obtener_indices(self.__sistema.get_subsistema_presente(), "1")  # a partir de los indices de listado candidatos, se obtiene el estado inicial candidato
        self.__estado_inicial_subsistema = "".join([self.__sistema.get_estado_inicial()[i] for i in self.__listado_valores_presentes])
        if (len(self.obtener_indices(self.__sistema.get_sistema_candidato(), "0")) != 0):
            self.eliminar_filas_por_bits(self.__sistema.get_sistema_candidato(), self.__sistema.get_estado_inicial())
            self.eliminar_columnas_por_bits(self.__sistema.get_sistema_candidato())
        self.__matriz_candidata = self.__matriz.copy()

        # Se elimina la matriz original para liberar memoria
        del self.__matriz

        temporal = self.marginalizar_columnas('0'*len(self.__listado_candidatos), self.__matriz_candidata.copy(), '1')
        sub_presente = ''
        for index, content in enumerate(self.__sistema.get_subsistema_presente()):
            if index in self.__listado_candidatos:
                sub_presente += content
        self.__matriz_no_futuro = self.marginalizar_filas(sub_presente, temporal, '1')

    def eliminar_filas_por_bits(self, sistema_candidato, estado_inicial):
        """
        Elimina las filas cuyos índices tengan un bit específico en la posición indicada.

        Args:
            sistema_candidato (str): Sistema candidato (nodos a usar, se representan con un 1 en una cadena binaria)
            estado_inicial (str): Estado inicial del sistema
        """
        indices = self.obtener_indices(sistema_candidato, "0")

        for i in indices:
            bit_indicado = estado_inicial[i]
            filas_a_mantener = [j for j in self.__matriz.index if j[i] == bit_indicado]
            self.__matriz = self.__matriz.loc[filas_a_mantener]
            filas_a_mantener.clear()

        nuevos_indices = [
            "".join([fila[i] for i in range(len(fila)) if i not in indices])
            for fila in self.__matriz.index
        ]
        self.__matriz.index = nuevos_indices

    def eliminar_columnas_por_bits(self, sistema_candidato):
        """
        Elimina las columnas cuyos índices tengan un bit específico en la posición indicada.

        Args:
            sistema_candidato (str): Sistema candidato (nodos a usar, se representan con un 1 en una cadena binaria)
        """
        indices = self.obtener_indices(sistema_candidato, "0")

        nuevos_indices = [
            "".join([columna[i] for i in range(len(columna)) if i not in indices])
            for columna in self.__matriz.columns
        ]
        self.__matriz.columns = nuevos_indices

        # Transponemos la matriz para que las columnas se conviertan en filas, agrupamos, y luego volvemos a transponer
        self.__matriz = self.__matriz.groupby(self.__matriz.columns, axis=1, sort=False).sum()

    def eliminar_columnas_por_bits_b(self, sistema_candidato):
        """
        Elimina las columnas cuyos índices tengan un bit específico en la posición indicada.
        Intentos con dask para mejorar la eficiencia de memoria.

        Args:
            sistema_candidato (str): Sistema candidato (nodos a usar, se representan con un 1 en una cadena binaria)
        """
        # Step 1: Get indices to remove
        indices = self.obtener_indices(sistema_candidato, "0")

        # Step 2: Update column names by removing specified bits
        nuevos_indices = [
            "".join([columna[i] for i in range(len(columna)) if i not in indices])
            for columna in self.__matriz.columns
        ]
        self.__matriz.columns = nuevos_indices

        # Eliminar duplicados conservando el orden
        indices_agrupados = list(dict.fromkeys(nuevos_indices))

        # Step 1: Transpose the pandas DataFrame
        matriz_transposed = self.__matriz.T

        # Step 2: Convert the transposed DataFrame to Dask
        dask_matriz = dd.from_pandas(matriz_transposed, npartitions=10, sort=False)  # Adjust npartitions as needed

        # Step 3: Dispose of the original pandas DataFrame
        del self.__matriz  # Free up memory
        del matriz_transposed  # Free up memory

        # Step 4: Perform Dask operations (e.g., groupby and sum)
        dask_matriz_grouped = dask_matriz.groupby(dask_matriz.index, sort=False).sum()

        # Step 5: Compute the result and transpose back
        self.__matriz = dask_matriz_grouped.compute().loc[indices_agrupados]

    def obtener_indices(self, cadena, num_indicado):
        """
        Obtiene los índices de todas las apariciones del numero indicado en representación binaria.

        Args:
            cadena (str): Cadena binaria
            num_indicado (str): Número a buscar en la cadena binaria
        """
        indices = []

        for idx, bit in enumerate(cadena):
            if bit == num_indicado:
                indices.append(idx)
        return indices
    
    def matriz_subsistema(self):
        """
        Calcula la matriz según el subsistema futuro y el presente.
        """
        # leer el subsistema presente y futuro
        indices_f = self.obtener_indices(self.__sistema.get_subsistema_futuro(), '1')
        
        # obtener el estado_nodo del diccionario de acuerdo a los indices_f
        temporal = self.__matriz_no_futuro.copy()
        sub_presente = "".join([self.__sistema.get_subsistema_presente()[i] for i in self.__listado_candidatos])
        indices_temporal = []
        for i in indices_f:
            matriz_futuro = self.__matriz_estado_nodo_dict[i].copy()
            matriz_marginalizada = self.marginalizar_filas(sub_presente, matriz_futuro, '1')
            self.__matriz_estado_nodo_marginalizadas[i] = matriz_marginalizada
            temporal = self.producto_tensorial_matrices(temporal, matriz_marginalizada, indices_temporal, [i], self.__estado_inicial_subsistema, self.__estado_inicial_subsistema)
            indices_temporal.append(i)
            
        self.__matriz_subsistema = np.array(temporal.iloc[0].values.tolist(), dtype='float64')

    """
    ------------------------------------------------------------------------------------------------
    Marginalización por filas y columnas
    ------------------------------------------------------------------------------------------------
    """
    def marginalizar_normal_complemento(self, lista_subsistema):
        """
        Obtienen tanto la matriz mariginalizada normal como el complemento de esta.

        Args:
            lista_subsistema (list): Lista con los nodos del subsistema

        Returns:
            tuple: Tupla con la matriz marginalizada normal y los indices de esta (nodos que se mantienen)
            tuple: Tupla con la matriz marginalizada complemento y los indices de esta (nodos que se mantienen)
        """
        cadena_presente = self.pasar_lista_a_cadena(lista_subsistema, 0)
        cadena_futuro = self.pasar_lista_a_cadena(lista_subsistema, 1)

        normal = self.marginalizar_bits(cadena_presente, cadena_futuro, '1')
        complemento = self.marginalizar_bits(cadena_presente, cadena_futuro, '0')

        indices_n = self.obtener_indices(cadena_futuro, '1')
        indices_c = self.obtener_indices(cadena_futuro, '0')

        i = 0
        j = 0
        while i < len(indices_n) and j < len(indices_c):
            if indices_n[i] < indices_c[j]:
                indices_n[i] = self.__listado_valores_futuros[indices_n[i]]
                i += 1
            else:
                indices_c[j] = self.__listado_valores_futuros[indices_c[j]]
                j += 1
        while i < len(indices_n):
            indices_n[i] = self.__listado_valores_futuros[indices_n[i]]
            i += 1
        while j < len(indices_c):
            indices_c[j] = self.__listado_valores_futuros[indices_c[j]]
            j += 1
        
        return (normal, indices_n), (complemento, indices_c)

    def marginalizar_bits(self, cadena_presente, cadena_futuro, bit):
        '''
        Marginaliza las filas y columnas de la matriz que no pertenecen al subsistema presente y futuro.
        Obtiene los nodos necesarios de los estado-nodo y hace el producto tensorial entre ellos para
        generar la matriz estado-estado y así obtener la distribución de probabilidad.
        Bit en 1 si se quiere hacer de manera normal, 0 si se quiere el complemento.

        Args:
            cadena_presente (str): Cadena binaria con los nodos del subsistema presente
            cadena_futuro (str): Cadena binaria con los nodos del subsistema futuro
            bit (str): Bit para indicar si se quiere hacer la marginalización normal o el complemento
        
        Returns:
            pd.DataFrame: Matriz marginalizada en estado-estado
        '''
        indices_futuros = self.obtener_indices(cadena_futuro, bit)
        estado_inicial = self.generar_estado_inicial_subsistema(cadena_presente, bit)
        if len(indices_futuros) == 1:
            key = self.__listado_valores_futuros[indices_futuros[0]]
            temporal = self.__matriz_estado_nodo_marginalizadas[key].copy()
            temporal_marginalizada = self.marginalizar_filas(cadena_presente, temporal, bit)
        else:
            temporal = self.__matriz_no_futuro.copy()
            temporal_marginalizada = self.marginalizar_filas(cadena_presente, temporal, bit)
            indices_temporal = []
            for i in indices_futuros:
                key = self.__listado_valores_futuros[i]
                matriz_futuro = self.__matriz_estado_nodo_marginalizadas[key].copy()
                matriz_marginalizada = self.marginalizar_filas(cadena_presente, matriz_futuro, bit)
                temporal_marginalizada = self.producto_tensorial_matrices(temporal_marginalizada, matriz_marginalizada, indices_temporal, [key], estado_inicial, estado_inicial)
                indices_temporal.append(key)

        return temporal_marginalizada
    
    def generar_estado_inicial_subsistema(self, subsistema_presente, bit):
        """
        Genera el estado inicial que debe tener la matriz marginalizada según el subsistema presente.
        Ej: Si la matriz tiene 4 nodos, el estado inicial es 1000 y el subsistema presente es 1010, 
        entonces cogerá los bits 0 y 3 de la cadena de estado inicial para generar el estado inicial 
        del subsistema: 10.

        Args:
            subsistema_presente (str): Subsistema presente
            bit (str): Bit para indicar si se quiere el estado normal o el complemento
        """
        for index, content in enumerate(subsistema_presente):
            if content == bit:
                index_estado_i = self.__listado_valores_presentes[index]
                if bit == '1':
                    self.__estado_i_normal += self.__sistema.get_estado_inicial()[index_estado_i]
                else:
                    self.__estado_i_complemento += self.__sistema.get_estado_inicial()[index_estado_i]
        if bit == '1':
            self.__estado_inicial_subsistema = self.__estado_i_normal
            return self.__estado_i_normal
        else:
            self.__estado_inicial_subsistema = self.__estado_i_complemento
            return self.__estado_i_complemento

    def marginalizar_filas(self, subsistema_presente, matriz, bit):
        """
        Marginaliza las filas de la matriz que no pertenecen al subsistema presente.

        Args:
            subsistema_presente (str): Indica cuales nodos se mantendran en el subsistema presente, 
            se representan con un 1 en una cadena binaria
            matriz (pd.Dataframe): Matriz TPM a marginalizar
            bit (char): 1 para el normal, 0 para el complemento
        
        Returns:
            pd.DataFrame: Matriz marginalizada
        """
        # 1 para el normal, 0 para el complemento
        indices = self.obtener_indices(subsistema_presente, bit)
        nuevos_indices = []
        
        # Recorre cada fila de la matriz

        nuevos_indices = [
            "".join([fila[i] for i in range(len(fila)) if i in indices])
            for fila in matriz.index
        ]

        matriz.index = nuevos_indices

        # Transponemos la matriz para que las columnas se conviertan en filas, agrupamos, y luego volvemos a transponer
        matriz = matriz.groupby(matriz.index, sort=False).mean()
        return matriz
      
    def marginalizar_columnas(self, sistema_futuro, matriz, bit):
        """
        Elimina las columnas cuyos índices tengan un bit específico en la posición indicada.

        Args:
            sistema_futuro (str): Sistema futuro (nodos a usar, se representan con un 1 en una cadena binaria)
            matriz (pd.DataFrame): Matriz TPM a marginalizar
            bit (char): 1 para el normal, 0 para el complemento
        
        Returns:
            pd.DataFrame: Matriz marginalizada
        """
        indices = self.obtener_indices(sistema_futuro, bit)
        
        nuevos_indices = []

        # Recorre cada columna de la matriz
        if(indices != []):
            nuevos_indices = [
                "".join([columna[i] for i in range(len(columna)) if i in indices]) or columna[-1]
                for columna in matriz.columns
            ]
        else:
            for _ in range(len(matriz.columns)):
                nuevos_indices.append('')
        
        matriz.columns = nuevos_indices

        # Transponemos la matriz para que las columnas se conviertan en filas, agrupamos, y luego volvemos a transponer
        matriz = matriz.T.groupby(matriz.columns, sort=False).sum().T
        return matriz
        
    """
    ------------------------------------------------------------------------------------------------
    Obtener estado nodo
    ------------------------------------------------------------------------------------------------
    """
    def obtener_estado_nodo(self):
        """
        Marginaliza las columnas para obtener el estado nodo de la matriz.
        
        Returns:
            pd.DataFrame: Matriz estado nodo
        """
        sistema_candidato = self.__sistema.get_sistema_candidato()
        cadena_dinamica = "0" * len(sistema_candidato)
        
        for i in range(len(sistema_candidato)):
            if i in self.__listado_candidatos:
                # Crear una cadena con un solo "1" en la posición correspondiente a la iteración actual
                subsistema_futuro = cadena_dinamica[:i] + "1" + cadena_dinamica[i+1:]
                
                # Reiniciar matriz_estado_nodo a una copia de __matriz
                self.__matriz_estado_nodo = self.__matriz_candidata.copy()
                
                # Marginalizar columnas con el subsistema futuro
                matriz_estado = self.marginalizar_columnas(subsistema_futuro, self.__matriz_estado_nodo, '1')

                # Guardar la matriz de estado nodo en un diccionario con el índice como clave
                self.__matriz_estado_nodo_dict[i] = matriz_estado
        
        del self.__matriz_candidata  # Liberar memoria
    
    
    def producto_tensorial_matrices(self, mat1, mat2, indices1, indices2, est1, est2):
        """
        Realiza el producto tensorial entre dos distribuciones de probabilidad, estas distribuciones las
        obtiene de las matrices TPM según los estados inciales que se le pasan.

        Args:
            mat1 (pd.DataFrame): Matriz de la primera distribución de probabilidad
            mat2 (pd.DataFrame): Matriz de la segunda distribución de probabilidad
            indices1 (list): Índices de los nodos originales que posee la matriz 1
            indices2 (list): Índices de los nodos originales que posee la matriz 2
            est1 (str): Estado inicial del subsistema 1
            est2 (str): Estado inicial del subsistema 2
        
        Returns:
            list: Distribución de probabilidad resultante del producto tensorial
        """
        # Crear etiquetas en formato little-endian para las combinaciones de columnas
        n_cols_resultado = 2 ** (len(indices1) + len(indices2))
        etiquetas_little_endian = [
            "".join(str((i >> k) & 1) for k in range(len(indices1) + len(indices2)))
            for i in range(n_cols_resultado)
        ]

        # Crear la matriz de resultado con las nuevas etiquetas de columnas
        resultado = pd.DataFrame(index=[self.__estado_inicial_subsistema], columns=etiquetas_little_endian)

        # Obtener la fila del estado inicial candidato
        if len(mat1) == 1 and mat1.index[0] == '':
            fila_inicial_m1 = ''
        else:
            fila_inicial_m1 = est1
        if len(mat2) == 1 and mat2.index[0] == '':
            fila_inicial_m2 = ''
        else:
            fila_inicial_m2 = est2

        mat1 = mat1.loc[[fila_inicial_m1]]
        mat2 = mat2.loc[[fila_inicial_m2]]
        
        # Iterar sobre cada combinación de columnas para realizar el producto tensorial
        for col1, col2 in itertools.product(mat1.columns, mat2.columns):
            # Construir el índice binario en formato little-endian de manera directa
            index_binario = ""
            i, j, k = 0, 0, 0

            # Iterar a través de los arreglos
            while i < len(indices1) and j < len(indices2):
                if indices1[i] < indices2[j]:
                    index_binario += str(col1)[i]
                    i += 1
                else:
                    index_binario += str(col2)[j]
                    j += 1
                k += 1

            # Una vez que uno de los arreglos ha sido completado,
            # ponemos los bits restantes
            while i < len(indices1):
                index_binario += str(col1)[i]
                i += 1
                k += 1
            while j < len(indices2):
                index_binario += str(col2)[j]
                j += 1
                k += 1

            # Calcular y asignar el producto
            # Calcular y asignar el producto en la fila correspondiente
            resultado.at[self.__estado_inicial_subsistema, index_binario] = mat1.at[fila_inicial_m1, col1] * mat2.at[fila_inicial_m2, col2]

        # Llenar valores NaN con 0 para la matriz de salida
        resultado.fillna(0, inplace=True)
        return resultado

    """
    ------------------------------------------------------------------------------------------------
    Carpintería
    ------------------------------------------------------------------------------------------------
    """
    def pasar_lista_a_cadena(self, lista, bit):
        """
        Convierte una lista de enteros en una cadena de bits.

        Args:
            lista (list): Lista de tuplas que contienen la representación de los nodos mediante
            el uso de enteros.
            bit (int): Obtener la cadena de los nodos según el bit indicado, 0 para presente, 1 para futuro.

        Returns:
            str: Cadena de bits
        """
        # Inicializa la cadena con ceros y la convierte en una lista mutable
        if bit == 0:
            longitud = len(self.__listado_valores_presentes)
        else:
            longitud = len(self.__listado_valores_futuros)

        cadena_dinamica = list("0" * longitud)
        
        # Recorre cada elemento de la lista 
        for estado, posicion in lista:
            if estado == bit:
                # Coloca un "1" en la posición indicada
                index = self.__listado_valores_presentes.index(posicion) if bit == 0 else self.__listado_valores_futuros.index(posicion)
                cadena_dinamica[index] = "1"
        
        if bit == 0:
            cadena_dinamica = "".join([cadena_dinamica[i] for i in range(len(self.__listado_valores_presentes))])
        else:
            cadena_dinamica = "".join([cadena_dinamica[i] for i in range(len(self.__listado_valores_futuros))])
        
        # Convierte la lista de caracteres de vuelta a una cadena
        return cadena_dinamica
    
    def pasar_cadena_a_lista(self):
        """
        Convierte una cadena de bits a una lista.

        Returns:
            list: Lista de tuplas que contienen la representación de los nodos mediante el uso de enteros.
        """
        indices_f = self.obtener_indices(self.__sistema.get_subsistema_futuro(), "1")
        indices_p = self.obtener_indices(self.__sistema.get_subsistema_presente(), "1")
        listado = []

        for i in indices_p:
            listado.append((0, i))
        for i in indices_f:
            listado.append((1, i))

        return listado
    
    def limpiar_estados_inicialies(self):
        self.__estado_i_normal = ''
        self.__estado_i_complemento = ''
        self.__estado_inicial_subsistema = ''
        
    """
    ------------------------------------------------------------------------------------------------
    Implementación de k-means
    ------------------------------------------------------------------------------------------------
    """
    def encontrar_complemento_particion(self, lista):
        """
        Encuentra el complemento de una partición.

        Args:
            lista (list): Lista con las tuplas que representan la partición
        
        Returns:
            list: Lista con las tuplas que representan el complemento de la partición
        """
        # ENTRAN TUPLAS DONDE EL PRIMER ELEMENTO SI ES CERO ES PRESENTE, SI ES UNO ES FUTURO, SE MIRA 
        # EL SISTEMA CANDIDATO PARA SABER QUE LE FALTA EN EL COMPLEMENTO
        complemento = []
        for i in range(len(self.__listado_valores_presentes)):
            valor_presente = self.__listado_valores_presentes[i]
            if (0, valor_presente) not in lista:
                complemento.append((0, valor_presente))
        for i in range(len(self.__listado_valores_futuros)):
            valor_futuro = self.__listado_valores_futuros[i]
            if (1, valor_futuro) not in lista:
                complemento.append((1, valor_futuro))
        return complemento
