import sys
import types
sys.modules['pytest'] = types.ModuleType('pytest')

import asyncio
import numpy as np
from src.core.document_object import DocumentObject
from src.core.orchestrator import AMDIOrchestrator

async def main():
    doc = DocumentObject(filename='test.txt', raw_bytes=b'Line 1\nLine 2\n')
    orch = AMDIOrchestrator()
    nd = await orch._parse(doc)
    elements = orch._to_elements(nd)
    
    print('Starting MIOS Ingestion steps manually...')
    positions = {}
    importances = {}
    connectivity = {}
    for idx, el in enumerate(elements):
        bbox = getattr(el, 'bbox', None)
        space = (bbox.x0, bbox.y0, bbox.x1, bbox.y1) if bbox else (0.0, 0.0, 1.0, 1.0)
        entropy = getattr(el, 'entropy', 0.5)
        relevance = 0.5
        p_state = orch.physics.register(
            element_id=el.element_id,
            content=el.content,
            space=space,
            page=el.page,
            entropy=entropy,
            relevance=relevance
        )
        positions[el.element_id] = (space[0] + space[2]) / 2.0, (space[1] + space[3]) / 2.0
        importances[el.element_id] = p_state.energy
        connectivity[el.element_id] = 1 + (1 if idx % 2 == 0 else 0)

    # 3. Point-Set Topology Space
    topo_sig = orch.topology.analyze(positions)
    print('Topology analyzed:', topo_sig)

    # 4. Spectral Layout signal
    layout_signal = np.array([p.energy for p in orch.physics.particles.values()], dtype=np.float32)
    spectral_sig = orch._spectral.analyze(layout_signal)
    print('Spectral analyzed:', spectral_sig)

    # 5. Tensor Space
    raw_elements = [
        {'page': p.page, 'section': getattr(p, 'section', 'default'), 'content': p.content}
        for p in orch.physics.particles.values()
    ]
    doc_tensor = orch.tensor_eng.build_tensor(raw_elements)
    print('Tensor shape:', doc_tensor.shape)

    # 6. Markov transition matrix
    section_sequences = [[getattr(el, 'section', 'default') or 'default' for el in elements]]
    markov_sig = orch.markov.build_transition_chain(section_sequences)
    print('Markov states:', markov_sig.states)
    print('All done successfully!')

if __name__ == '__main__':
    asyncio.run(main())
