# agreement_generation.py
# Daniele Bellutta
# 4 May 2020


from support.graph_processing import extract_subgraph, binarize_graph, remove_self_loops, multiply_graphs, add_graphs


DECISION_FILTER = lambda n, a: (not n.startswith("j"))


def compute_direct_agreement(citation_graph, vote_graph, year):
  vote_subgraph = extract_subgraph(vote_graph, year)
  return remove_self_loops(multiply_graphs(vote_subgraph, vote_subgraph.reverse(), DECISION_FILTER))

def compute_indirect_agreement(citation_graph, vote_graph, year):
  vote_subgraph = extract_subgraph(vote_graph, year)
  citation_subgraph = binarize_graph(extract_subgraph(citation_graph, year))
  indirect_agreement = multiply_graphs(vote_subgraph, citation_subgraph, DECISION_FILTER)
  return remove_self_loops(multiply_graphs(indirect_agreement, vote_subgraph.reverse(), DECISION_FILTER))

def compute_symmetric_indirect_agreement(citation_graph, vote_graph, year):
  undirected_citation_graph = binarize_graph(add_graphs(citation_graph, citation_graph.reverse()))
  return remove_self_loops(compute_indirect_agreement(undirected_citation_graph, vote_graph, year))

def compute_direct_and_indirect_agreement(citation_graph, vote_graph, year):
  direct_agreement = compute_direct_agreement(citation_graph, vote_graph, year)
  indirect_agreement = compute_indirect_agreement(citation_graph, vote_graph, year)
  return remove_self_loops(add_graphs(direct_agreement, indirect_agreement))

def compute_direct_and_symmetric_indirect_agreement(citation_graph, vote_graph, year):
  direct_agreement = compute_direct_agreement(citation_graph, vote_graph, year)
  symmetric_indirect_agreement = compute_symmetric_indirect_agreement(citation_graph, vote_graph, year)
  return remove_self_loops(add_graphs(direct_agreement, symmetric_indirect_agreement))

