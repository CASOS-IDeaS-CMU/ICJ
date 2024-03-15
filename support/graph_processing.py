# graph_processing.py
# Daniele Bellutta
# 23 April 2020


import networkx as nx
from networkx.algorithms.bipartite.matrix import biadjacency_matrix


def load_graph(file_name):
  return nx.read_graphml(file_name)


def extract_subgraph(graph, year):
  subgraph = nx.DiGraph()
  subgraph.add_nodes_from([(n, dict(a)) for n, a in graph.nodes(data = True) if (a["year"] <= year)])
  subgraph.add_edges_from([(s, t, dict(a)) for s, t, a in graph.edges(data = True) if (a["year"] <= year)])
  return subgraph

def binarize_graph(graph):
  binarized = graph.copy()
  for u, v in binarized.edges():
    weight = dict(binarized.get_edge_data(u, v))["weight"]
    if ((weight is not None) and (weight != 0)):
      binarized[u][v]["weight"] = 1
  return binarized

def remove_negative_edges(graph):
  removed = graph.copy()
  for u, v in graph.edges():
    weight = dict(graph.get_edge_data(u, v))["weight"]
    if ((weight is not None) and (weight < 0)):
      removed.remove_edge(u, v)
  return removed

def remove_self_loops(graph):
  removed = graph.copy()
  for node in graph.nodes():
    if (removed.has_edge(node, node)):
      removed.remove_edge(node, node)
  return removed

def simplify_weights(graph):
  simplified = graph.copy()
  for u, v, attributes in graph.edges(data = True):
    weight = attributes["weight"]
    if (weight > 0):
      simplified[u][v]["weight"] = 1
    elif (weight < 0):
      simplified[u][v]["weight"] = -1
  return simplified

def isolate_node_type(graph, attribute_name, attribute_value):
  subgraph = nx.DiGraph()
  subgraph.add_nodes_from([(n, dict(a)) for n, a in graph.nodes(data = True) if ((attribute_name not in a) or (a[attribute_name] == attribute_value))])
  subgraph.add_edges_from([(s, t, dict(a)) for s, t, a in graph.edges(data = True) if (subgraph.has_node(s) and subgraph.has_node(t))])
  return subgraph


def order_nodes(graph, filter):
  return sorted([n for n, a in graph.nodes(data = True) if (filter(n, a))])

def adjacency_matrix(graph, row_order, column_order):
  adjacency = None
  if (row_order and column_order):
    adjacency = biadjacency_matrix(graph, row_order = row_order, column_order = column_order)
  else:
    adjacency = nx.adjacency_matrix(graph, nodelist = row_order if (row_order) else column_order)
  return adjacency

def multiply_graphs(graph_a, graph_b, inside_filter):
  product = None
  outside_filter = lambda n, a: (not inside_filter(n, a))
  inside_nodes = order_nodes(graph_a, inside_filter)

  nodes_a = order_nodes(graph_a, outside_filter)
  nodes_a = nodes_a if (nodes_a) else inside_nodes
  nodes_b = order_nodes(graph_b, outside_filter)
  nodes_b = nodes_b if (nodes_b) else inside_nodes

  if (set(inside_nodes) == set(order_nodes(graph_b, inside_filter))):
    product = nx.DiGraph()

    adjacency = adjacency_matrix(graph_a, nodes_a, inside_nodes)
    adjacency *= adjacency_matrix(graph_b, inside_nodes, nodes_b)

    product.add_nodes_from([(n, dict(a)) for n, a in graph_a.nodes(data = True) if (n in nodes_a)])
    product.add_nodes_from([(n, dict(a)) for n, a in graph_b.nodes(data = True) if (n in nodes_b)])

    for i, j in zip(*adjacency.nonzero()):
      u = nodes_a[i]
      v = nodes_b[j]
      attributes = {}

      if (graph_a.has_edge(u, v)):
        attributes = dict(graph_a.get_edge_data(u, v))
      elif (graph_b.has_edge(u, v)):
        attributes = dict(graph_b.get_edge_data(u, v))

      attributes["weight"] = float(adjacency[i, j])
      product.add_edge(u, v, **attributes)

  return product

def add_graphs(graph_a, graph_b):
  result = nx.DiGraph()
  result.add_nodes_from([(n, dict(a)) for n, a in graph_a.nodes(data = True)])
  result.add_nodes_from([(n, dict(a)) for n, a in graph_b.nodes(data = True)])

  for graph in [graph_a, graph_b]:
    for u, v, attributes in graph.edges(data = True):
      if (result.has_edge(u, v)):
        result[u][v]["weight"] += dict(graph.get_edge_data(u, v))["weight"]
      else:
        result.add_edge(u, v, **attributes)

  return result


def write_graph(file_name, graph):
  nx.write_graphml(graph, file_name)

