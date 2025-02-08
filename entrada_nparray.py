import numpy as np
import pandas as pd

labels = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O')

tpm = np.array([...])

df = pd.DataFrame(tpm)

df.to_excel("estado_nodo_15.xlsx", index=False, header=False)
