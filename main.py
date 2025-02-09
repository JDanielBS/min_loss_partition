from modelos.ComparacionEstrategias import ComparacionEstrategias
from modelos.sistema import Sistema
from icecream import ic

def main():
    # Rutas de las matrices de probabilidad
    tpm = 'archivos/resultado_6.csv'
    tpm_estado_nodo = 'archivos/estado_nodo_6.xlsx'

    # Crear objeto de comparación
    comparacion = ComparacionEstrategias(tpm_estado_nodo, tpm)

    # Crear el subsistema, tiene la siguiente estructura (estado inicial, sistema candidato, mecanismo, purview)
    sistema = Sistema('100000', '111111', '111111', '111111')

    # Establecer información de PyPhi
    pyphi_info = {
        'labels': ('A', 'B', 'C', 'D', 'E', 'F'),
        'i_state': comparacion.convertir_e_inicial(sistema.get_estado_inicial()),
        'c_system': comparacion.obtener_indices(sistema.get_sistema_candidato()),
        'mechanism': sistema.get_subsistema_presente(),
        'purview': sistema.get_subsistema_futuro(),
    }

    # Ejecutar búsqueda de mínima pérdida
    comparacion.minima_perdida(sistema, pyphi_info)

if __name__ == "__main__":
    main()