# run_adf_tests.py
# Daniele Bellutta
# 19 January 2024


import csv

from statsmodels.tsa.stattools import adfuller

from support.regression import load_node_year_variables


DECISION_VARIABLES_FILE_NAME = "data/decision_variables.csv"
DIRECT_JUDGE_VARIABLES_FILE_NAME = "data/judge_variables/direct_judge_variables.csv"

DEPENDENT_VARIABLES = ["citations_next_year", "citations_next_5_years", "citations_next_10_years"]


def load_dependent_node_values(file_name, node_column, dependent_variables):
  dependent_node_values = {}
  dependent_node_year_values = {dependent_variable: {} for dependent_variable in dependent_variables}

  with open(file_name, "r") as input_file:
    for row in csv.DictReader(input_file):
      for dependent_variable in dependent_variables:
        if (row[dependent_variable]):
          if (row[node_column] in dependent_node_year_values[dependent_variable]):
            dependent_node_year_values[dependent_variable][row[node_column]][int(row["year"])] = float(row[dependent_variable])
          else:
            dependent_node_year_values[dependent_variable][row[node_column]] = {int(row["year"]): float(row[dependent_variable])}

  for dependent_variable, node_year_values in dependent_node_year_values.items():
    dependent_node_values[dependent_variable] = {}
    for node, year_values in node_year_values.items():
       dependent_node_values[dependent_variable][node] = [year_values[year] for year in sorted(year_values.keys())]

  return dependent_node_values


def run_dependent_node_adf(dependent_node_values):
  dependent_node_adrs = {dependent_variable: {} for dependent_variable in dependent_node_values.keys()}
  dependent_nonoptimal_nodes = {dependent_variable: set() for dependent_variable in dependent_node_values.keys()}
  dependent_node_counts = {dependent_variable: 0 for dependent_variable in dependent_node_values.keys()}
  for dependent_variable, node_values in dependent_node_values.items():
    for node, values in node_values.items():
      if (len(values) > 3):
        p_value, lag = adfuller(values, maxlag = None, autolag = "AIC")[1: 3]
        dependent_node_adrs[dependent_variable][node] = (p_value, lag)
        if ((p_value < 0.05) and (lag > 1)):
          dependent_nonoptimal_nodes[dependent_variable].add(node)
        dependent_node_counts[dependent_variable] += 1
  return dependent_node_adrs, dependent_nonoptimal_nodes, dependent_node_counts

def calculate_dependent_ratios(dependent_nonoptimal_nodes, dependent_node_counts):
  dependent_ratios = {}
  for dependent_variable, nonoptimal_nodes in dependent_nonoptimal_nodes.items():
    dependent_ratios[dependent_variable] = float(len(nonoptimal_nodes)) / float(dependent_node_counts[dependent_variable])
  return dependent_ratios


def print_dependent_ratios(dependent_ratios):
  for dependent_variable, ratio in dependent_ratios.items():
    print(dependent_variable, ratio)


def main():
  dependent_nodes_values = load_dependent_node_values(DECISION_VARIABLES_FILE_NAME, "decision", DEPENDENT_VARIABLES)
  decision_ratios = calculate_dependent_ratios(*run_dependent_node_adf(dependent_nodes_values)[1:])

  dependent_nodes_values = load_dependent_node_values(DIRECT_JUDGE_VARIABLES_FILE_NAME, "judge", DEPENDENT_VARIABLES)
  judge_ratios = calculate_dependent_ratios(*run_dependent_node_adf(dependent_nodes_values)[1:])

  print()
  print("=== DECISIONS ===")
  print_dependent_ratios(decision_ratios)

  print()
  print("=== JUDGES ===")
  print_dependent_ratios(judge_ratios)

  print()


main()


