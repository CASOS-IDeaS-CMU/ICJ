# compute_precedent_scores.py
# Daniele Bellutta
# 12 April 2020


import csv
import networkx as nx

from support.graph_processing import load_graph, extract_subgraph
from support.variable_computation import compute_citations, compute_properties, compute_independent_variables, compute_unanimities, compute_damping_factor, switch_keys, generate_dependent_variable_name, compute_lagged_variables, write_variables, write_node_variables


AUTHORSHIP_FILE_NAME = "data/authorship.csv"
CITATION_GRAPH_FILE_NAME = "data/citation_graph.graphml"
OUTPUT_FILE_NAME = "data/decision_variables.csv"
FINAL_VARIABLES_FILE_NAME = "data/final_decision_variables.csv"

INDEPENDENT_VARIABLES = {
  "reverse_pagerank": lambda g, d: compute_precedent_scores(g, d, unanimity = False, weighted = False),
  "unanimity": lambda g, d: compute_unanimities(g),
  "in_degree": lambda g, d: compute_properties(g, g.in_degree, normalized = True),
  "out_degree": lambda g, d: compute_properties(g, g.out_degree, normalized = True),
  "pagerank": lambda g, d: nx.pagerank_numpy(g, alpha = d),
  "hub": lambda g, d: nx.hits_numpy(g)[0],
  "authority": lambda g, d: nx.hits_numpy(g)[1],
}
DEPENDENT_VARIABLES = {
  "citations_next_year": lambda g, s_y, e_y: compute_citations(g, s_y, e_y),
}


def compute_precedent_scores(citation_graph, damping_factor, unanimity = False, weighted = False, normalize = False):
  decision_scores = {}
  num_decisions = citation_graph.number_of_nodes()
  decision_unanimities = (compute_unanimities(citation_graph) if (unanimity) else None)
  complement = (1.0 - damping_factor) / float(num_decisions)

  while (len(decision_scores) < num_decisions):
    for decision, attributes in citation_graph.nodes(data = True):
      successors = list(citation_graph.successors(decision))

      if (all([n in decision_scores for n in successors])):
        first_term = complement
        scores = [decision_scores[d] for d in successors]
        normalizer = len(scores)
        average_score = 0

        if (normalize):
          num_descendants = len(nx.descendants(citation_graph, decision))
          if (num_descendants > 0):
            first_term /= float(num_descendants)

        if (weighted):
          weights = [citation_graph.get_edge_data(decision, s)["weight"] for s in successors]
          scores = [s * w for s, w in zip(scores, weights)]
          normalizer = sum(weights)

        if (scores):
          average_score = float(sum(scores)) / float(normalizer)
        if (unanimity):
          first_term *= decision_unanimities[decision]

        decision_scores[decision] = first_term + (damping_factor * average_score)

  return decision_scores


def compute_dependent_variables(citation_graph, year_pairs):
  dependent_variables = {}
  for (start_year, end_year) in year_pairs:
    dependent_variables[end_year - start_year + 1] = compute_citations(citation_graph, start_year, end_year)
  return dependent_variables


def compute_variables(citation_graph, damping_factor, num_dependent_years, dependent_lags = {1,}):
  decision_year_variables = {}
  years = sorted({a["year"] for _, a in citation_graph.nodes(data = True)})
  max_year = years[-1]
  max_dependent_years = max(num_dependent_years)

  for year in range(years[0], max_year - min(num_dependent_years) + 1):
    current_graph = extract_subgraph(citation_graph, year)
    decision_independent_variables = switch_keys(compute_independent_variables(INDEPENDENT_VARIABLES, current_graph, damping_factor))

    future_graph = extract_subgraph(citation_graph, year + max_dependent_years)
    year_pairs = [(year + 1, year + num_years) for num_years in num_dependent_years]
    dependent_variables = compute_dependent_variables(future_graph, year_pairs)

    decision_dependent_variables = {}
    for num_years, decision_variables in dependent_variables.items():
      if (year + num_years <= max_year):
        decision_dependent_variables[generate_dependent_variable_name(num_years)] = decision_variables
    decision_dependent_variables = switch_keys(decision_dependent_variables)

    for decision, independent_variables in decision_independent_variables.items():
      variables = {**independent_variables, **decision_dependent_variables[decision]}

      variables["age"] = year - citation_graph.nodes[decision]["year"]
      variables["age_squared"] = variables["age"] ** 2
      variables["type"] = citation_graph.nodes[decision]["type"].lower()
      variables["topic"] = citation_graph.nodes[decision]["topic"].lower()
      variables["num_votes"] = citation_graph.nodes[decision]["votes_for"] + citation_graph.nodes[decision]["votes_against"]
      variables["current_year"] = year
      variables["network_size"] = current_graph.number_of_nodes()

      for dependent_variable in decision_dependent_variables[decision].keys():
        variables.update(compute_lagged_variables(decision_year_variables, dependent_variable, decision, year, dependent_lags, normalizer_variable = None))

      decision_year_variables[(decision, year)] = variables

  return decision_year_variables


def main():
  citation_graph = load_graph(CITATION_GRAPH_FILE_NAME)
  damping_factor = compute_damping_factor(compute_unanimities(citation_graph))
  print(damping_factor)
  decision_year_variables = compute_variables(citation_graph, damping_factor, list(range(1, 11)), dependent_lags = {1, 2, 3, 4, 5})
  write_variables(OUTPUT_FILE_NAME, decision_year_variables, "decision")

  decision_independent_variables = switch_keys(compute_independent_variables(INDEPENDENT_VARIABLES, citation_graph, damping_factor))
  write_node_variables(FINAL_VARIABLES_FILE_NAME, decision_independent_variables, "decision")


main()


