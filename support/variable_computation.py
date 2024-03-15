# variable_computation.py
# Daniele Bellutta
# 28 April 2020


import csv


def compute_citations(citation_graph, start_year, end_year):
  decision_citations = {}

  for decision in citation_graph.nodes():
    decision_citations[decision] = 0
    for predecessor in citation_graph.predecessors(decision):
      year = citation_graph.get_edge_data(predecessor, decision)["year"]
      if ((year >= start_year) and (year <= end_year)):
        decision_citations[decision] += 1

  return decision_citations

def compute_properties(graph, property_function, weighted = False, normalized = False):
  node_degrees = {}
  num_nodes = float(graph.number_of_nodes())
  for node in graph.nodes():
    parameters = (node, "weight") if (weighted) else (node,)
    node_degrees[node] = property_function(*parameters)
    if (normalized):
      node_degrees[node] = float(node_degrees[node]) / num_nodes
  return node_degrees


def compute_independent_variables(independent_variables, graph, damping_factor):
  return {v: f(graph, damping_factor) for v, f in independent_variables.items()}


def compute_unanimities(citation_graph):
  return {d: float(a["votes_for"]) / float(a["votes_for"] + a["votes_against"]) for d, a in citation_graph.nodes(data = True)}

def compute_damping_factor(decision_unanimities):
  return float(sum(decision_unanimities.values())) / float(len(decision_unanimities.values()))


def switch_keys(variable_nodes):
  node_variables = {}
  for variable, node_values in variable_nodes.items():
    for node, value in node_values.items():
      if (node in node_variables):
        node_variables[node][variable] = value
      else:
        node_variables[node] = {variable: value}
  return node_variables


def generate_dependent_variable_name(num_years):
  dependent_variable_name = "citations_next_"
  if (num_years > 1):
    dependent_variable_name += str(num_years) + "_years"
  else:
    dependent_variable_name += "year"
  return dependent_variable_name

def parse_dependent_variable_years(dependent_variable_name):
  num_years = None
  if (dependent_variable_name.endswith("s")):
    end_num = dependent_variable_name[15:].index("_")
    num_years = int(dependent_variable_name[15: 15 + end_num])
  else:
    num_years = 1
  return num_years


def generate_lagged_variable_name(variable_name, lag_length = 1):
  return "lagged_" + variable_name + ("_%d" % (lag_length,) if (lag_length > 1) else "")

def compute_lagged_variables(node_year_variables, dependent_variable, node, year, lag_lengths, normalizer_variable = None):
  lagged_variables = {}
  dependent_num_years = parse_dependent_variable_years(dependent_variable)

  for lag_length in lag_lengths:
    lagged_dependent_name = generate_lagged_variable_name(dependent_variable, lag_length = lag_length)
    adjusted_year = year - (lag_length * dependent_num_years)
    adjusted_dependent = dependent_variable

    if ((node, adjusted_year) not in node_year_variables):
      for y in range(1, dependent_num_years):
        if ((node, adjusted_year + y) in node_year_variables):
          adjusted_year += y
          adjusted_dependent = generate_dependent_variable_name(dependent_num_years - y)
          break

    if (((node, adjusted_year) in node_year_variables) and ((normalizer_variable is None) or (node_year_variables[(node, adjusted_year)][normalizer_variable] > 0))):
      lagged_variables[lagged_dependent_name] = float(node_year_variables[(node, adjusted_year)][adjusted_dependent])
      if (normalizer_variable is not None):
        lagged_variables[lagged_dependent_name] /= float(node_year_variables[(node, adjusted_year)][normalizer_variable])
    else:
      lagged_variables[lagged_dependent_name] = 0

  return lagged_variables


def write_variables(file_name, node_year_variables, node_class):
  header = set()
  for variables in node_year_variables.values():
    header |= set(variables.keys())

  with open(file_name, "w") as output_file:
    writer = csv.DictWriter(output_file, fieldnames = [node_class, "year"] + sorted(header))
    writer.writeheader()

    for (node, year), variables in node_year_variables.items():
      row = dict(variables)
      row[node_class] = node
      row["year"] = year
      writer.writerow(row)

def write_node_variables(file_name, node_variables, node_class):
  header = set()
  for variables in node_variables.values():
    header |= set(variables.keys())

  with open(file_name, "w") as output_file:
    writer = csv.DictWriter(output_file, fieldnames = [node_class] + sorted(header))
    writer.writeheader()

    for node, variables in node_variables.items():
      row = dict(variables)
      row[node_class] = node
      writer.writerow(row)


