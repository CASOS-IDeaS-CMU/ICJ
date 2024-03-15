# compute_influence_scores.py
# Daniele Bellutta
# 23 April 2020


from collections import Counter
import networkx as nx

from support.graph_processing import load_graph, extract_subgraph, simplify_weights, write_graph
from support.variable_computation import compute_citations, compute_properties, compute_independent_variables, switch_keys, compute_damping_factor, compute_unanimities, generate_dependent_variable_name, compute_lagged_variables, write_variables, write_node_variables
from support.agreement_generation import compute_direct_agreement, compute_indirect_agreement, compute_symmetric_indirect_agreement, compute_direct_and_indirect_agreement, compute_direct_and_symmetric_indirect_agreement


CITATION_GRAPH_FILE_NAME = "data/citation_graph.graphml"
VOTE_GRAPH_FILE_NAME = "data/vote_graph.graphml"
OUTPUT_PREFIX = "data/judge_variables/"
OUTPUT_SUFFIX = "_judge_variables.csv"

DIRECT_OUTPUT_FILE_NAME = "data/direct_final_judge_variables.csv"
#DIRECT_INDIRECT_OUTPUT_FILE_NAME = "data/direct_and_indirect_final_judge_variables.csv"
DIRECT_SYMMETRIC_INDIRECT_OUTPUT_FILE_NAME = "data/direct_and_symmetric_indirect_final_judge_variables.csv"

GRAPH_GENERATORS = {
  "direct": compute_direct_agreement,
#  "indirect": compute_indirect_agreement,
#  "symmetric_indirect": compute_symmetric_indirect_agreement,
#  "direct_and_indirect": compute_direct_and_indirect_agreement,
  "direct_and_symmetric_indirect": compute_direct_and_symmetric_indirect_agreement,
}

INDEPENDENT_VARIABLES = {
  "in_degree": lambda g, d: compute_properties(g, g.in_degree, normalized = True),
  "out_degree": lambda g, d: compute_properties(g, g.out_degree, normalized = True),
  "hub": lambda g, d: nx.hits_numpy(g)[0],
  "authority": lambda g, d: nx.hits_numpy(g)[1],
}

MAX_YEAR = 99999


def compute_judge_citations(citation_graph, vote_graph, start_year, end_year):
  judge_citations = Counter()
  vote_subgraph = extract_subgraph(vote_graph, start_year - 1)
  decision_citations = compute_citations(citation_graph, start_year, end_year)

  for judge, attributes in vote_graph.nodes(data = True):
    if (attributes["class"] == "judge"):
      judge_citations.update({judge: 0})

      for decision in vote_graph.successors(judge):
        if (vote_graph.get_edge_data(judge, decision)["weight"] > 0):
          judge_citations.update({judge: decision_citations[decision]})

  return judge_citations

def compute_dependent_variables(citation_graph, vote_graph, year_pairs):
  dependent_variables = {}
  for (start_year, end_year) in year_pairs:
    dependent_variables[end_year - start_year + 1] = compute_judge_citations(citation_graph, vote_graph, start_year, end_year)
  return dependent_variables


def count_judge_decisions(vote_graph):
  judge_decisions = Counter()

  for judge, attributes in vote_graph.nodes(data = True):
    if (attributes["class"] == "judge"):
      judge_decisions.update({judge: 0})

      for decision in vote_graph.successors(judge):
        if (vote_graph.get_edge_data(judge, decision)["weight"] > 0):
          judge_decisions.update({judge: 1})

  return judge_decisions

def count_judge_votes(vote_graph, year):
  judge_votes = Counter()
  judge_member = {}
  judge_ad_hoc = {}

  for judge, attributes in vote_graph.nodes(data = True):
    if (attributes["class"] == "judge"):
      judge_votes.update({judge: 0})
      judge_member[judge] = False
      judge_ad_hoc[judge] = False

      for decision in vote_graph.successors(judge):
        if (vote_graph.get_edge_data(judge, decision)["year"] == year):
          judge_votes.update({judge: 1})

          if (vote_graph.get_edge_data(judge, decision)["ad_hoc"]):
            judge_ad_hoc[judge] = True
          else:
            judge_member[judge] = True

  return (judge_votes, judge_member, judge_ad_hoc)

def compute_judge_unanimities(citation_graph, vote_graph):
  judge_unanimities = {}
  decision_unanimities = compute_unanimities(citation_graph)

  for judge, attributes in vote_graph.nodes(data = True):
    if (attributes["class"] == "judge"):
      judge_unanimities[judge] = []

      for decision in vote_graph.successors(judge):
        if (vote_graph.get_edge_data(judge, decision)["weight"] > 0):
          if (judge in judge_unanimities):
            judge_unanimities[judge].append(decision_unanimities[decision])

  for judge in judge_unanimities.keys():
    num_decisions = len(judge_unanimities[judge])
    if (num_decisions > 0):
      judge_unanimities[judge] = float(sum(judge_unanimities[judge])) / float(num_decisions)
    else:
      judge_unanimities[judge] = 0.0

  return judge_unanimities


def compute_variables(citation_graph, vote_graph, damping_factor, num_dependent_years, graph_generator, dependent_lags = {1,}):
  judge_year_variables = {}
  years = sorted({a["year"] for _, a in vote_graph.nodes(data = True)})
  max_year = years[-1]
  max_dependent_years = max(num_dependent_years)

  for year in range(years[0], max_year - min(num_dependent_years) + 1):
    current_graph = simplify_weights(graph_generator(citation_graph, vote_graph, year))
    judge_independent_variables = switch_keys(compute_independent_variables(INDEPENDENT_VARIABLES, current_graph, damping_factor))

    future_citation_graph = extract_subgraph(citation_graph, year + max_dependent_years)
    future_vote_graph = extract_subgraph(vote_graph, year + max_dependent_years)
    year_pairs = [(year + 1, year + num_years) for num_years in num_dependent_years]
    dependent_variables = compute_dependent_variables(future_citation_graph, future_vote_graph, year_pairs)

    judge_dependent_variables = {}
    for num_years, judge_variables in dependent_variables.items():
      if (year + num_years <= max_year):
        judge_dependent_variables[generate_dependent_variable_name(num_years)] = judge_variables
    judge_dependent_variables = switch_keys(judge_dependent_variables)

    current_vote_graph = extract_subgraph(vote_graph, year)
    judge_decisions = count_judge_decisions(current_vote_graph)
    judge_unanimities = compute_judge_unanimities(extract_subgraph(citation_graph, year), current_vote_graph)
    judge_votes, judge_member, judge_ad_hoc = count_judge_votes(current_vote_graph, year)

    for judge, independent_variables in judge_independent_variables.items():
      variables = {**independent_variables, **judge_dependent_variables[judge]}

      variables["seniority"] = year - vote_graph.nodes[judge]["year"]
      variables["seniority_squared"] = variables["seniority"] ** 2
      variables["supported_decisions"] = judge_decisions[judge]
      variables["average_unanimity"] = judge_unanimities[judge]
      variables["current_year"] = year
      variables["network_size"] = current_graph.number_of_nodes()
      variables["num_votes_this_year"] = judge_votes[judge]
      variables["member_this_year"] = str(judge_member[judge])
      variables["ad_hoc_this_year"] = str(judge_ad_hoc[judge])

      for dependent_variable in judge_dependent_variables[judge].keys():
        variables.update(compute_lagged_variables(judge_year_variables, dependent_variable, judge, year, dependent_lags, normalizer_variable = "supported_decisions"))

      judge_year_variables[(judge, year)] = variables

  return judge_year_variables


def generate_output_file_name(network_type):
  return OUTPUT_PREFIX + str(network_type) + OUTPUT_SUFFIX


def main():
  citation_graph = load_graph(CITATION_GRAPH_FILE_NAME)
  vote_graph = load_graph(VOTE_GRAPH_FILE_NAME)
  damping_factor = compute_damping_factor(compute_unanimities(citation_graph))
  print(damping_factor)

  for network_type, graph_generator in GRAPH_GENERATORS.items():
    judge_year_variables = compute_variables(citation_graph, vote_graph, damping_factor, list(range(1, 11)), graph_generator, {1, 2, 3, 4, 5})
    write_variables(generate_output_file_name(network_type), judge_year_variables, "judge")

  direct_graph = compute_direct_agreement(citation_graph, vote_graph, MAX_YEAR)
  judge_independent_variables = switch_keys(compute_independent_variables(INDEPENDENT_VARIABLES, direct_graph, damping_factor))
  write_node_variables(DIRECT_OUTPUT_FILE_NAME, judge_independent_variables, "judge")

  #indirect_graph = compute_direct_and_indirect_agreement(citation_graph, vote_graph, MAX_YEAR)
  #judge_independent_variables = switch_keys(compute_independent_variables(INDEPENDENT_VARIABLES, indirect_graph, damping_factor))
  #write_node_variables(DIRECT_INDIRECT_OUTPUT_FILE_NAME, judge_independent_variables, "judge")

  symmetric_graph = compute_direct_and_symmetric_indirect_agreement(citation_graph, vote_graph, MAX_YEAR)
  judge_independent_variables = switch_keys(compute_independent_variables(INDEPENDENT_VARIABLES, symmetric_graph, damping_factor))
  write_node_variables(DIRECT_SYMMETRIC_INDIRECT_OUTPUT_FILE_NAME, judge_independent_variables, "judge")


main()


