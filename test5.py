import networkx as nx
from arango import ArangoClient
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def load_arangodb_graph_to_networkx(db_name, username, password, graph_name):
    # Connect to ArangoDB
    client = ArangoClient(hosts='http://localhost:8529')
    db = client.db(db_name, username=username, password=password)
    
    # Access the graph by name
    arango_graph = db.graph(graph_name)
    
    # Create a directed NetworkX graph.
    # Change to nx.Graph() if your graph is undirected.
    G = nx.DiGraph()
    
    # --- Define helper functions to load vertices and edges ---
    def load_vertices_from_collection(vc_name):
        collection = db.collection(vc_name)
        vertices = []
        for vertex in collection.all():
            # Use '_id' as the node identifier and include all attributes.
            vertices.append((vertex['_id'], vertex))
        return vertices

    def load_edges_from_collection(ec_name):
        collection = db.collection(ec_name)
        edges = []
        for edge in collection.all():
            # Use '_from' and '_to' to indicate the endpoints.
            edges.append((edge['_from'], edge['_to'], edge))
        return edges

    # --- Load vertices in parallel ---
    vertex_collections = list(arango_graph.vertex_collections())
    # Estimate total number of vertices for progress bar
    total_nodes = sum(db.collection(vc).count() for vc in vertex_collections)
    pbar_vertices = tqdm(total=total_nodes, desc="Loading vertices", unit="node")
    
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(load_vertices_from_collection, vc): vc for vc in vertex_collections}
        for future in as_completed(futures):
            for node_id, attrs in future.result():
                G.add_node(node_id, **attrs)
                pbar_vertices.update(1)
    pbar_vertices.close()

    # --- Load edges in parallel ---
    edge_definitions = list(arango_graph.edge_definitions())
    # Estimate total number of edges for progress bar
    total_edges = sum(db.collection(ed['edge_collection']).count() for ed in edge_definitions)
    pbar_edges = tqdm(total=total_edges, desc="Loading edges", unit="edge")
    
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(load_edges_from_collection, ed['edge_collection']): ed['edge_collection']
            for ed in edge_definitions
        }
        for future in as_completed(futures):
            for source, target, attrs in future.result():
                G.add_edge(source, target, **attrs)
                pbar_edges.update(1)
    pbar_edges.close()
    
    return G

    # Set your connection parameters and graph name here.
    db_name = "common_db"
    username = "root"
    password = "zxcv"
    graph_name = "restaurants"
    
    G = load_arangodb_graph_to_networkx(db_name, username, password, graph_name)
    print("Loaded graph with {} nodes and {} edges.".format(G.number_of_nodes(), G.number_of_edges()))

    # Get schema information for the graph
    print("\nGraph Schema Information:")
    
    # Get node types and their counts
    node_types = {}
    for node, attrs in G.nodes(data=True):
        # Extract collection name from node ID (format: collection/key)
        collection = node.split('/')[0] if '/' in node else 'unknown'
        node_types[collection] = node_types.get(collection, 0) + 1
    
    print("\nNode Collections:")
    for collection, count in node_types.items():
        print(f"  - {collection}: {count} nodes")
    
    # Get edge types and their counts
    edge_types = {}
    for u, v, attrs in G.edges(data=True):
        # Check if edge has a type attribute
        if '_edge_type' in attrs:
            edge_type = attrs['_edge_type']
        elif '_id' in attrs and '/' in attrs['_id']:
            # Extract collection from edge ID
            edge_type = attrs['_id'].split('/')[0]
        else:
            edge_type = 'unknown'
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    
    print("\nEdge Collections:")
    for collection, count in edge_types.items():
        print(f"  - {collection}: {count} edges")
    
    # Sample node data for each node type
    print("\nSample Node Data:")
    node_samples = {}
    for node, attrs in G.nodes(data=True):
        collection = node.split('/')[0] if '/' in node else 'unknown'
        if collection not in node_samples:
            node_samples[collection] = (node, attrs)
            print(f"\n  {collection} Sample:")
            print(f"    ID: {node}")
            for key, value in attrs.items():
                print(f"    {key}: {value}")
    
    # Sample edge data for each edge type
    print("\nSample Edge Data:")
    edge_samples = {}
    for u, v, attrs in G.edges(data=True):
        if '_edge_type' in attrs:
            edge_type = attrs['_edge_type']
        elif '_id' in attrs and '/' in attrs['_id']:
            edge_type = attrs['_id'].split('/')[0]
        else:
            edge_type = 'unknown'
            
        if edge_type not in edge_samples:
            edge_samples[edge_type] = (u, v, attrs)
            print(f"\n  {edge_type} Sample:")
            print(f"    From: {u}")
            print(f"    To: {v}")
            for key, value in attrs.items():
                print(f"    {key}: {value}")
    
    # Node attribute summary
    if G.number_of_nodes() > 0:
        print("\nNode Attribute Summary:")
        all_node_keys = set()
        for _, attrs in G.nodes(data=True):
            all_node_keys.update(attrs.keys())
        
        print(f"  Available attributes: {', '.join(sorted(all_node_keys))}")
    
    # Edge attribute summary
    if G.number_of_edges() > 0:
        print("\nEdge Attribute Summary:")
        all_edge_keys = set()
        for _, _, attrs in G.edges(data=True):
            all_edge_keys.update(attrs.keys())
        
        print(f"  Available attributes: {', '.join(sorted(all_edge_keys))}")