'''
AEGIS-DocIntel / AMDI-OS — External Framework Connectors
==========================================================
Provides drop-in integration adapters for LangChain and LlamaIndex ecosystems:
  - AEGISLangChainDocumentTransformer: Plug AEGIS Reading-Order DAG + Elastic Chunker into LangChain.
  - AEGISLlamaIndexNodeParser: Plug AEGIS Reading-Order DAG + Elastic Chunker into LlamaIndex.
'''
from __future__ import annotations

from typing import Any, Dict, List, Optional
from src.engines.graph_reading_order import SpatialReadingGraph
from src.ael.elastic_chunker import ElasticChunker, ChunkingConfig


class AEGISLangChainDocumentTransformer:
    '''
    Drop-in LangChain Document Transformer powered by AEGIS-DocIntel:
      - Recovers spatial reading order via Kahn's priority queue DAG
      - Performs structure-aware elastic chunking
      - Appends Anthropic-style contextual prefixes
    '''

    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.chunker = ElasticChunker(config=config)
        self.reading_graph = SpatialReadingGraph()

    def transform_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        '''
        Transforms input documents into reading-ordered, structure-preserved chunks.
        Expects documents as list of dicts with 'text', 'x', 'y', 'w', 'h', 'type', 'page'.
        '''
        if not documents:
            return []

        # Step 1: Spatial Reading Order DAG Recovery
        V, E = self.reading_graph.build_reading_graph(documents)
        ordered_nodes = self.reading_graph.recover_reading_order(V, E)

        # Step 2: Structure-Aware Elastic Chunking (returns List[List[Dict]])
        raw_chunks = self.chunker.chunk_nodes(ordered_nodes)

        # Step 3: Add Contextual Metadata & Prefixes
        transformed = []
        for idx, chunk_nodes in enumerate(raw_chunks):
            if not chunk_nodes:
                continue

            joined_text = "\n".join(str(n.get('text', '')) for n in chunk_nodes)
            first_node = chunk_nodes[0]
            chunk_dict = {
                'text': joined_text,
                'page': first_node.get('page', 1),
                'type': first_node.get('type', 'text'),
                'heading': first_node.get('heading', ''),
            }

            prefixed_text = self.chunker.generate_contextual_prefix(chunk_dict, doc_title='Document')
            transformed.append({
                'page_content': prefixed_text,
                'metadata': {
                    'chunk_id': f'aegis_chunk_{idx}',
                    'chunk_type': chunk_dict['type'],
                    'page': chunk_dict['page'],
                    'element_count': len(chunk_nodes),
                    'is_protected': chunk_dict['type'] in self.chunker.config.protected_types,
                }
            })
        return transformed


class AEGISLlamaIndexNodeParser:
    '''
    Drop-in LlamaIndex Node Parser powered by AEGIS-DocIntel:
      - Converts raw documents into LlamaIndex-compatible Node payloads.
    '''

    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.transformer = AEGISLangChainDocumentTransformer(config=config)

    def get_nodes_from_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        '''Generates structured LlamaIndex nodes.'''
        transformed = self.transformer.transform_documents(documents)
        nodes = []
        for item in transformed:
            nodes.append({
                'text': item['page_content'],
                'extra_info': item['metadata'],
            })
        return nodes
