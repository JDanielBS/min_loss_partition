# min_loss_partition

Python tool that searches for the **minimum-loss partition** of a subsystem of a binary network (for example, a 6-node system A–F) from its transition probability matrix (TPM). Loss is measured with the **Earth Mover's Distance (EMD)**, and the result is compared against the reference solution from **PyPhi**.

## What it does

1. **Builds the TPM** from the per-node marginal probabilities (`entrada_matriz.py`, `entrada_nparray.py`).
2. **Computes the optimal partition with three methods**:
   - **Strategy 3** (`modelos/AlgoritmoPrincipal.py`): k-means-like heuristic. Starts from a random partition and moves nodes between the two halves while the EMD improves.
   - **Brute force** (`modelos/AlgoritmoFuerzaBruta.py`): tries every possible partition.
   - **PyPhi** (`modelos/PyphiCode.py`): computes the reference partition with the `pyphi` library.
3. **Compares results** (`modelos/ComparacionEstrategias.py`): reruns strategy 3 until its EMD is close to PyPhi's, then saves a summary (partitions, losses, timings, number of attempts) to `solucion_pyphi.xlsx`.

## Structure

```
main.py                    # Entry point: compares strategies for one subsystem
entrada_matriz.py          # Builds the TPM as a tensor product of per-node matrices (CSV)
entrada_nparray.py         # Variant of TPM generation using numpy
modelos/
  ComparacionEstrategias.py  # Runs the tests and writes results to Excel
  AlgoritmoPrincipal.py      # Strategy 3 (partition heuristic)
  AlgoritmoFuerzaBruta.py    # Exhaustive partition search
  PyphiCode.py               # Reference computation with PyPhi
  MetricasDistancia.py       # EMD and Hamming distance
  matriz.py                  # TPM handling: marginalization, indexing, states
  sistema.py                 # System definition (initial state, background, mechanism, purview)
  LectorExcel.py             # Reads each node's ON/OFF state from Excel
archivos/                  # Example inputs and outputs (TPM, node states, optimal partition)
condiciones/               # Example system structure (estructura_6.csv)
```

## Requirements

Python 3.9+ and the following libraries (there is no `requirements.txt`; install them manually):

```bash
pip install numpy pandas openpyxl pyemd pyphi icecream
```

- `pyphi` provides the reference partition (`PyphiCode.py`).
- `pyemd` computes the EMD.
- `icecream` is used only for debugging (`ic(...)`).

## Usage

### 1. Run the comparison (main flow)

From the project root:

```bash
python main.py
```

`main.py` uses these defaults:

- TPM: `archivos/resultado_6.csv`
- Node states: `archivos/estado_nodo_6.xlsx`
- System: `Sistema('100000', '111111', '111111', '111111')`
  - `estado_inicial` (initial state), `sistema_candidato` (background), `subsistema_futuro` (purview), `subsistema_presente` (mechanism).

To analyze a different system, change the `Sistema(...)` arguments and the `labels` tuple in `main.py`. Results are appended to `solucion_pyphi.xlsx` in the working directory. If the file already exists, its headers must match the new record.

### 2. Generate a new TPM

`entrada_matriz.py` reads the per-node matrices from `archivos/estado_nodo_6.xlsx`, computes the tensor product of all of them, and exports the result to CSV:

```bash
python entrada_matriz.py
```

### 3. Use a system from code

```python
from modelos.sistema import Sistema
from modelos.ComparacionEstrategias import ComparacionEstrategias

comparacion = ComparacionEstrategias('archivos/estado_nodo_6.xlsx', 'archivos/resultado_6.csv')
sistema = Sistema('100000', '111111', '111111', '111111')
solucion_e3, tiempo = comparacion.estrategia3(sistema)     # heuristic
soluciones_fb = comparacion.fuerza_bruta(sistema)          # exhaustive
```

## Data format

- **Initial state, background, purview, and mechanism**: bit strings, one position per node (`'100000'` = node A on, the rest off).
- **TPM (`resultado_6.csv`)**: 64 rows × 6 columns, no header.
- **`archivos/estado_nodo_6.xlsx`**: one column per node with its probability of being on; `LectorExcel` builds the ON/OFF matrix for each node from it.

## Outputs

- `solucion_pyphi.xlsx`: one row per test with the PyPhi partition, the strategy 3 partition, their EMDs, timings, and attempts.
- `solucion_e3_fb.xlsx`: strategy 3 vs. brute-force comparison (written by `pasar_a_excel_e3_fb`).
- `archivos/particion_optima.json`: example optimal partition.

## Notes and limitations

- Default paths are relative: run the scripts from the project root.
- `LectorExcel` has a default path with backslashes (`'archivos\estado_nodo_6.xlsx'`). It works on Windows, but `/` or `os.path.join` is safer.
- `entrada_matriz.py` writes `resultado_6.csv` to the current directory, not to `archivos/`. Move it or change the path if you need to replace the TPM used by `main.py`.
- Strategy 3 is a heuristic and may need several attempts. `prueba_con_subsistema` repeats until its EMD is close to PyPhi's (tolerance `1e-9` in `son_cercanos`). If it never converges, it runs forever.
- Some methods contain commented-out debug calls (`ic(...)`), and variable names mix Spanish and English. These are leftovers from development.
- `ic(...)` calls require `icecream` to be installed, even when no output is shown.
