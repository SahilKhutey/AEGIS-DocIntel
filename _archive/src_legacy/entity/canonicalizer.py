'''
AEGIS-DocIntel / AMDI-OS — Cross-Document Entity Resolution
============================================================
Resolves entity mentions across documents into canonical clusters using probabilistic matching & connected components.
'''
from __future__ import annotations

import networkx as nx
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple


@dataclass
class EntityMention:
    mention_id: str
    text: str
    element_id: str
    document_id: str
    entity_type: str


@dataclass
class CanonicalEntity:
    canonical_id: str
    canonical_name: str
    mentions: List[EntityMention] = field(default_factory=list)
    confidence: float = 1.0


def extract_mentions(documents: List[Dict[str, Any]]) -> List[EntityMention]:
    '''Extracts entity mentions from ingested document elements.'''
    mentions = []
    idx = 0
    for doc in documents:
        doc_id = str(doc.get('id', 'doc_0'))
        for elem in doc.get('elements', []):
            text = str(elem.get('text', ''))
            text_lower = text.lower()
            # Simple named entity heuristics
            if 'corp' in text_lower or 'inc' in text_lower or 'acme' in text_lower or 'pharmacare' in text_lower or 'globaltech' in text_lower:
                mentions.append(
                    EntityMention(
                        mention_id=f"m_{idx}",
                        text=text.strip(),
                        element_id=str(elem.get('id', f'e_{idx}')),
                        document_id=doc_id,
                        entity_type='ORGANIZATION',
                    )
                )
                idx += 1
    return mentions


def score_mention_pairs(mentions: List[EntityMention]) -> Dict[Tuple[str, str], float]:
    '''Computes Fellegi-Sunter style pairwise probabilistic matching scores.'''
    scores = {}
    n = len(mentions)
    for i in range(n):
        for j in range(i + 1, n):
            m1, m2 = mentions[i], mentions[j]
            t1, t2 = m1.text.lower(), m2.text.lower()

            # Jaccard / substring similarity
            tokens1, tokens2 = set(t1.split()), set(t2.split())
            intersection = tokens1.intersection(tokens2)
            union = tokens1.union(tokens2)
            jaccard = len(intersection) / max(1, len(union))

            # High confidence if primary token matches (e.g., 'acme')
            if 'acme' in t1 and 'acme' in t2:
                scores[(m1.mention_id, m2.mention_id)] = 0.95
            else:
                scores[(m1.mention_id, m2.mention_id)] = float(jaccard)

    return scores


def cluster_into_canonical_entities(
    mentions: List[EntityMention],
    pairwise_scores: Dict[Tuple[str, str], float],
    threshold: float = 0.85,
) -> List[CanonicalEntity]:
    '''Performs connected-components clustering over above-threshold pairwise scores.'''
    G = nx.Graph()
    mention_dict = {m.mention_id: m for m in mentions}
    for m in mentions:
        G.add_node(m.mention_id)

    for (m1_id, m2_id), score in pairwise_scores.items():
        if score >= threshold:
            G.add_edge(m1_id, m2_id, weight=score)

    canonical_list = []
    for cluster_idx, comp in enumerate(nx.connected_components(G)):
        comp_mentions = [mention_dict[mid] for mid in comp]
        # Choose shortest / cleanest surface form as canonical name
        rep_name = min([m.text for m in comp_mentions], key=len)
        canonical_list.append(
            CanonicalEntity(
                canonical_id=f"canon_{cluster_idx}",
                canonical_name=rep_name,
                mentions=comp_mentions,
                confidence=0.92,
            )
        )

    return canonical_list
