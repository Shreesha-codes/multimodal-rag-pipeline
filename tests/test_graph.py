import pytest
from backend.models import MultimodalNode
from backend.services.graph import SessionGraph
from backend.services.relationship_engine import link_temporal, link_entities

def test_temporal_linking():
    graph = SessionGraph("test_session")
    
    audio_node = MultimodalNode(
        id="audio1", session_id="test_session", source_file="test.mp4", modality="audio",
        timestamp=10.0, end_timestamp=15.0, text="hello world"
    )
    
    # Inside tolerance (12.0 is between 10.0 and 15.0)
    frame_node_linked = MultimodalNode(
        id="frame1", session_id="test_session", source_file="test.mp4", modality="video_frame",
        timestamp=12.0
    )
    
    # Outside tolerance (30.0 is not near 10-15)
    frame_node_unlinked = MultimodalNode(
        id="frame2", session_id="test_session", source_file="test.mp4", modality="video_frame",
        timestamp=30.0
    )
    
    nodes = [audio_node, frame_node_linked, frame_node_unlinked]
    
    for n in nodes:
        graph.add_node(n)
        
    link_temporal(graph, nodes, tolerance=2.0)
    
    assert graph.graph.has_edge("audio1", "frame1")
    assert not graph.graph.has_edge("audio1", "frame2")
    
    edge_data = graph.graph.get_edge_data("audio1", "frame1")
    assert edge_data["type"] == "VISIBLE_DURING"

def test_entity_linking():
    graph = SessionGraph("test_session")
    
    node_a = MultimodalNode(
        id="nodeA", session_id="test_session", source_file="test.mp4", modality="audio",
        entities=["Redis", "PostgreSQL", "Database"]
    )
    
    # Shares Redis and PostgreSQL
    node_b = MultimodalNode(
        id="nodeB", session_id="test_session", source_file="test.mp4", modality="video_frame",
        entities=["Redis", "PostgreSQL", "API"]
    )
    
    # Shares no entities
    node_c = MultimodalNode(
        id="nodeC", session_id="test_session", source_file="test.mp4", modality="image",
        entities=["Kubernetes", "Docker"]
    )
    
    nodes = [node_a, node_b, node_c]
    
    for n in nodes:
        graph.add_node(n)
        
    link_entities(graph, nodes)
    
    assert graph.graph.has_edge("nodeA", "nodeB")
    assert not graph.graph.has_edge("nodeA", "nodeC")
    assert not graph.graph.has_edge("nodeB", "nodeC")
    
    edge_data = graph.graph.get_edge_data("nodeA", "nodeB")
    assert edge_data["type"] == "RELATED_TO"
    assert set(edge_data["shared_entities"]) == {"redis", "postgresql"}

def test_graph_expansion():
    graph = SessionGraph("test_session")
    
    node_a = MultimodalNode(id="A", session_id="test", source_file="test", modality="audio", timestamp=10.0, end_timestamp=12.0)
    node_b = MultimodalNode(id="B", session_id="test", source_file="test", modality="video_frame", timestamp=11.0)
    
    graph.add_node(node_a)
    graph.add_node(node_b)
    link_temporal(graph, [node_a, node_b])
    
    neighbors = graph.expand_from_nodes(["A"])
    assert len(neighbors) == 1
    assert neighbors[0]["node_id"] == "B"
    assert neighbors[0]["relationship"]["type"] == "VISIBLE_DURING"
