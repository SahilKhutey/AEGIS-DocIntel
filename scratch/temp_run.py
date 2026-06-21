
import sys
sys.path.insert(0, r"c:\Users\User\Documents\AEGIS-DocIntel\amdi-os")
from mios.engines.tensor.tensor_engine import TensorEngine
te = TensorEngine()
elements = [
    {'page': 1, 'section': 'intro', 'content': 'First word to tokenize'},
    {'page': 1, 'section': 'results', 'content': 'The quantitative score is 125.50'},
    {'page': 2, 'section': 'intro', 'content': 'Other page element'}
]
doc_tensor = te.build_tensor(elements, max_rows=3, max_cols=3)
print(sys.version.split()[0], doc_tensor.shape)
