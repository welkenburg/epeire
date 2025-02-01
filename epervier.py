# import externes
import osmnx as ox  # Bibliothèque pour télécharger et manipuler des réseaux de transport depuis OpenStreetMap
import os
import json

# import internes
from utils import *  # Importation des fonctions personnalisées définies dans un module externe 'utils'
from debug import *

data_fold : str = "data/"

class Epervier:
    def __init__(self, starting_point : str, time_limit : float):
        self.map_coef : float = 2
        self.time_lim : float = time_limit # s
        self.speed_lim : float = 180 # km/h
        self.map_radius : float = kmh_to_ms(self.speed_lim) * time_limit * self.map_coef
        self.starting_coords : tuple = ox.geocode(starting_point)
        self.graph : nx.MultiDiGraph = self.get_graph(self.starting_coords, self.map_radius)

    def get_graph(self, coords, radius) -> tuple[nx.MultiDiGraph, list]:
        self.fileName : str = f"{coords[0]}-{coords[1]}-{radius}".replace(".",",")
        self.map_path : str = os.path.join(data_fold, f"{self.fileName}.graphml")

        if not os.path.exists(self.map_path):
            graph : nx.MultiDiGraph = ox.graph_from_address(f"{coords[0]},{coords[1]}", dist=radius, network_type="all")
            ox.save_graphml(graph, filepath=self.map_path)
        else:
            graph : nx.MultiDiGraph = ox.load_graphml(self.map_path)
        
        return graph
    
    def add_graph_infos(self, f_dir : str | float = None):
        def translate_dir(direction :str) -> float:
            translation = {"E" : 0, "NE" : 45, "N" : 90, "NO" : 135, "O" : 180, "SO" : 225, "S" : 270, "SE" : 315}
            if direction in translation:
                return translation[direction]
            return None
        
        if f_dir:
            if type(f_dir) == float or (f_dir := translate_dir(f_dir)):
                add_node_alignment(self.graph, f_dir)
        ox.add_edge_speeds(self.graph)
        ox.add_edge_travel_times(self.graph)

        # possible optimisation (faire les deux en meme temps)
        add_node_speed(self.graph)
        add_node_distance(self.graph, self.starting_coords, "distance_depart")

    def exclude_isochrone(self):
        starting_node : int = get_point_in_graph(self.starting_coords, self.graph)
        isochrone : dict = dijkstra_with_limit(self.graph, starting_node, weight="travel_time", limit=self.time_lim)

        isonodes : list = isochrone.keys()
        self.isograph :nx.MultiDiGraph = self.graph.subgraph(isonodes).copy()
        self.graph.remove_edges_from(self.isograph.edges())
        self.graph.remove_nodes_from(self.isograph.nodes())

    def select_points(self, strategie : dict, n_points : int):
        new_weights = {}
        for attr in strategie["weights"]:
            normalize_attribute(self.graph, attr)
            new_weights[f"normalized_{attr}"] = strategie["weights"][attr]

        # algorithme glouton (solution suboptimale)
        top_nodes = []
        calculate_node_score(self.graph, weights=new_weights)
        for point in range(n_points):
            top_node = get_top_node(self.graph, top_nodes)
            top_nodes.append(top_node)
            if point != n_points-1:
                add_node_distance(self.graph, (self.graph.nodes[top_node]["y"],self.graph.nodes[top_node]["x"]), f"distance_{point}")
                normalize_attribute(self.graph, f"distance_{point}")
                update_node_score(self.graph, {f"normalized_distance_{point}":strategie["points_repeltion"]})

        points = [(self.graph.nodes[node]["y"],self.graph.nodes[node]["x"]) for node in top_nodes]
        return points

    def save(self):
        ox.save_graphml(self.graph, filepath=self.map_path)

if __name__ == "__main__":
    e = Epervier("auch",4*60)
    # e.add_graph_infos()
    # e.exclude_isochrone()
    # e.save()
    strat = {"weights" : {
                "distance_depart": -0.8,  
                "speed_avg": 0.2,   
                "street_count": 0.1,
                "speed_max" : 0.4   
            },
            "points_repeltion" : 0.6}
    points = e.select_points(strat, 6)
    print(points)