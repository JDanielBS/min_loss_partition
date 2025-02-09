import numpy as np
import pandas as pd

tpm = np.array([...])

df = pd.DataFrame(tpm)

df.to_excel("estado_nodo_n.xlsx", index=False, header=False)
