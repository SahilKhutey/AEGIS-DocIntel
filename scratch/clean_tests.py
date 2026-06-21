with open("tests/test_graph.py", "r", encoding="utf-8") as f:
    content = f.read()

lines = content.splitlines()
cleaned_lines = []
for line in lines:
    stripped = line.strip()
    if "NOTE: The output was truncated" in line:
        continue
    cleaned_lines.append(line)

# Let's write them back, but let's filter out consecutive blank lines
filtered_lines = []
last_was_blank = False
for line in cleaned_lines:
    if line.strip() == "":
        if not last_was_blank:
            filtered_lines.append("")
            last_was_blank = True
    else:
        filtered_lines.append(line)
        last_was_blank = False

# Now let's find the truncation point at the end of the file.
# The file ends with:
#     engine.graph.add_node(GraphNode(node_id=
# Let's find this line and truncate the file there, then write the complete tests.
for i in range(len(filtered_lines)-1, -1, -1):
    if 'engine.graph.add_node(GraphNode(node_id=' in filtered_lines[i] or 'node_id=' in filtered_lines[i] and i > len(filtered_lines) - 10:
        # truncate here
        filtered_lines = filtered_lines[:i]
        break

# Add completed test_shortest_path_no_path and other tests
extra_tests = """    engine.graph.add_node(GraphNode(node_id="b", node_type="element"))
    path = engine.shortest_path("a", "b")
    assert path is None

def test_get_neighbors():
    engine = GraphEngine()
    elements = [
        make_element("e1"),
        make_element("e2"),
    ]
    engine.build_nodes(elements)
    engine.build_edges(elements)
    neighbors = engine.get_neighbors("e1")
    assert len(neighbors) == 1
    assert neighbors[0] == "e2"
    
    # Test with edge type filter
    neighbors_follows = engine.get_neighbors("e1", EdgeType.FOLLOWS)
    assert len(neighbors_follows) == 1
    
    neighbors_spatial = engine.get_neighbors("e1", EdgeType.ABOVE)
    assert len(neighbors_spatial) == 0

def test_find_relationships():
    engine = GraphEngine()
    elements = [
        make_element("e1"),
        make_element("e2"),
        make_element("e3"),
    ]
    engine.build_nodes(elements)
    engine.build_edges(elements)
    
    rels = engine.find_relationships("e1", max_hops=2)
    assert "follows" in rels
    assert len(rels["follows"]) == 2

def test_find_similar_nodes():
    engine = GraphEngine()
    elements = [
        make_element("e1"),
        make_element("e2"),
        make_element("e3"),
    ]
    engine.build_nodes(elements)
    engine.build_edges(elements)
    similar = engine.find_similar_nodes("e1", top_k=2)
    assert len(similar) > 0

def test_subgraphs():
    engine = GraphEngine()
    elements = [
        make_element("e1", section="sec1"),
        make_element("e2", section="sec1"),
        make_element("e3", section="sec2"),
    ]
    engine.build_nodes(elements)
    
    sub_section = engine.get_subgraph_by_section("sec1")
    assert len(sub_section.nodes) == 2
    
    sub_type = engine.get_subgraph_by_node_type("text")
    assert len(sub_type.nodes) == 3

def test_distributions_and_json():
    engine = GraphEngine()
    elements = [
        make_element("e1", etype=ElementType.TEXT),
        make_element("e2", etype=ElementType.TABLE),
    ]
    engine.build_nodes(elements)
    engine.build_edges(elements)
    
    node_dist = engine.node_type_distribution()
    edge_dist = engine.edge_type_distribution()
    
    assert node_dist["text"] == 1
    assert node_dist["table"] == 1
    assert edge_dist["follows"] == 1
    
    json_data = engine.export_to_json()
    assert len(json_data["nodes"]) == 2
    assert len(json_data["edges"]) == 1
    
    # Test statistics
    stats = engine.statistics()
    assert stats.n_nodes == 2
    assert stats.n_edges == 1
    assert stats.is_connected is True
    assert stats.is_dense is False

    engine.clear()
    assert engine.graph.graph.number_of_nodes() == 0
"""

with open("tests/test_graph.py", "w", encoding="utf-8") as f:
    f.write("\\n".join(filtered_lines) + "\\n" + extra_tests)

print("test_graph.py cleaned and completed successfully!")
