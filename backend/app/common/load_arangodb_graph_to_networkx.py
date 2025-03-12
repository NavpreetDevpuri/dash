import networkx as nx
from arango import ArangoClient
from arango.graph import Graph
from arango.database import StandardDatabase
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def load_arangodb_graph_to_networkx(db: StandardDatabase, arango_graph: Graph) -> nx.DiGraph:
    # Create a directed NetworkX graph.
    # Change to nx.Graph() if your graph is undirected.
    print(f"Loading ArangoDB graph '{arango_graph.name}' to NetworkX...")
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

if __name__ == "__main__":
    client = ArangoClient(hosts='http://localhost:8529')
    db = client.db('food_db', username='root', password='root')
    arango_graph = db.graph('food_graph')
    G = load_arangodb_graph_to_networkx(arango_graph)
    print(G.nodes(data=True))
    print(G.edges(data=True))