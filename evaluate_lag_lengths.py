# evaluate_lag_lengths.py
# Daniele Bellutta
# 5 February 2024


from collections import Counter

from support.regression import load_node_year_variables, generate_variable_coefficients


DECISION_FILE_NAME = "data/decision_variables.csv"
DECISION_INDEX = ["decision", "year"]
DECISION_CONTROL_VARIABLES = {"age", "age_squared", "type", "current_year"}
DECISION_INDEPENDENT_VARIABLES = [
  {"pagerank"},
  {"reverse_pagerank"},
  {"hub"},
  {"authority"},
  {"unanimity"},
]

JUDGE_DIRECT_FILE_NAME = "data/judge_variables/direct_judge_variables.csv"
JUDGE_DIRECT_SYM_INDIRECT_FILE_NAME = "data/judge_variables/direct_and_symmetric_indirect_judge_variables.csv"
JUDGE_INDEX = ["judge", "year"]
JUDGE_CONTROL_VARIABLES = {"seniority", "seniority_squared", "current_year", "num_votes_this_year", "ad_hoc_this_year"}
JUDGE_OFFSET_VARIABLE = "supported_decisions"
JUDGE_INDEPENDENT_VARIABLES = [
  {"hub"},
  {"in_degree"},
]
JUDGE_TABLE_FILE_NAME = "tables/judge_tables/"

TIME_VARIABLE = "current_year"
DEPENDENT_VARIABLES = ["citations_next_year", "citations_next_5_years", "citations_next_10_years"]


def compute_dependent_avg_qaic(dependent_independent_results):
  depdent_sums, dependent_nums = Counter(), Counter()
  for dependent_variable, independent_results in dependent_independent_results.items():
    for results in independent_results.values():
      depdent_sums.update({dependent_variable: results["(Intercept)"]["model_qaic"]})
    dependent_nums.update({dependent_variable: len(independent_results)})
  return {dependent: float(sum_qaics) / float(dependent_nums[dependent]) for dependent, sum_qaics in depdent_sums.items()}

def find_optimal_lag_length(lag_dependent_independent_results):
  dependent_min_qaic, dependent_opt_lag = {}, {}
  for lag_length in sorted(lag_dependent_independent_results.keys()):
    for dependent_variable, avg_qaic in compute_dependent_avg_qaic(lag_dependent_independent_results[lag_length]).items():
      if ((dependent_variable not in dependent_min_qaic) or (avg_qaic < dependent_min_qaic[dependent_variable])):
        dependent_min_qaic[dependent_variable] = avg_qaic
        dependent_opt_lag[dependent_variable] = lag_length
  return dependent_opt_lag


def find_max_dependent_changes(independent_results_a, independent_results_b):
  coeff_change, ame_change, sig_changes = 0, 0, set()

  for independent_variables, results_a in independent_results_a.items():
    results_b = independent_results_b[independent_variables]
    for independent_variable in independent_variables:
      delta_coeff = abs(results_b[independent_variable]["coefficient"] - results_a[independent_variable]["coefficient"])
      delta_ame = abs(results_b[independent_variable]["ame_over_sd"] - results_a[independent_variable]["ame_over_sd"])
      coeff_change = max(coeff_change, delta_coeff)
      ame_change = max(ame_change, delta_ame)

      if (((results_a[independent_variable]["coeff_p-value"] < 0.05) and (results_b[independent_variable]["coeff_p-value"] >= 0.05)) or ((results_a[independent_variable]["ame_p-value"] < 0.05) and (results_b[independent_variable]["ame_p-value"] >= 0.05))):
        sig_changes.add(independent_variable)

  return (coeff_change, ame_change, sig_changes)

def find_max_changes(dependent_lags, lag_dependent_independent_results):
  dependent_coeff_changes, dependent_ame_changes, dependent_sig_changes = {}, {}, {}
  for dependent_variable, optimal_lag in dependent_lags.items():
    if (optimal_lag > 1):
      dependent_coeff_changes[dependent_variable], dependent_ame_changes[dependent_variable], dependent_sig_changes[dependent_variable] = find_max_dependent_changes(lag_dependent_independent_results[1][dependent_variable], lag_dependent_independent_results[optimal_lag][dependent_variable])
  return (dependent_coeff_changes, dependent_ame_changes, dependent_sig_changes)


def print_dependent_data(dependent_data):
  for dependent_variable, datum in dependent_data.items():
    if (datum):
      print(dependent_variable, datum)


def main():
  node_year_variables = load_node_year_variables(DECISION_FILE_NAME, DECISION_INDEX)
  lag_variable_coefficients = {l: generate_variable_coefficients(node_year_variables, DECISION_INDEPENDENT_VARIABLES, DEPENDENT_VARIABLES, DECISION_CONTROL_VARIABLES, dependent_lags = set(range(1, l + 1))) for l in range(1, 6)}
  decision_lags = find_optimal_lag_length(lag_variable_coefficients)
  decision_coeff_changes, decision_ame_changes, decision_sig_changes = find_max_changes(decision_lags, lag_variable_coefficients)

  node_year_variables = load_node_year_variables(JUDGE_DIRECT_FILE_NAME, JUDGE_INDEX)
  lag_variable_coefficients = {l: generate_variable_coefficients(node_year_variables, JUDGE_INDEPENDENT_VARIABLES, DEPENDENT_VARIABLES, JUDGE_CONTROL_VARIABLES, offset_variable = JUDGE_OFFSET_VARIABLE, dependent_lags = set(range(1, l + 1))) for l in range(1, 6)}
  direct_judge_lags = find_optimal_lag_length(lag_variable_coefficients)
  direct_judge_coeff_changes, direct_judge_ame_changes, direct_judge_sig_changes = find_max_changes(direct_judge_lags, lag_variable_coefficients)

  node_year_variables = load_node_year_variables(JUDGE_DIRECT_SYM_INDIRECT_FILE_NAME, JUDGE_INDEX)
  lag_variable_coefficients = {l: generate_variable_coefficients(node_year_variables, JUDGE_INDEPENDENT_VARIABLES, DEPENDENT_VARIABLES, JUDGE_CONTROL_VARIABLES, offset_variable = JUDGE_OFFSET_VARIABLE, dependent_lags = set(range(1, l + 1))) for l in range(1, 6)}
  direct_sym_indirect_judge_lags = find_optimal_lag_length(lag_variable_coefficients)
  direct_sym_indirect_judge_coeff_changes, direct_sym_indirect_judge_ame_changes, direct_sym_indirect_judge_sig_changes = find_max_changes(direct_sym_indirect_judge_lags, lag_variable_coefficients)

  print()
  print("=== DECISIONS ===")
  print("-- Optimal lag lengths ---")
  print_dependent_data(decision_lags)
  if (decision_coeff_changes):
    print("-- Max coefficient changes ---")
    print_dependent_data(decision_coeff_changes)
  if (decision_ame_changes):
    print("-- Max AME changes ---")
    print_dependent_data(decision_ame_changes)
  if (decision_sig_changes):
    print("-- Significance changes ---")
    print_dependent_data(decision_sig_changes)

  print()
  print("=== JUDGES IN DIRECT AGREEMENT ===")
  print("-- Optimal lag lengths ---")
  print_dependent_data(direct_judge_lags)
  if (direct_judge_coeff_changes):
    print("-- Max coefficient changes ---")
    print_dependent_data(direct_judge_coeff_changes)
  if (direct_judge_ame_changes):
    print("-- Max AME changes ---")
    print_dependent_data(direct_judge_ame_changes)
  if (direct_judge_sig_changes):
    print("-- Significance changes ---")
    print_dependent_data(direct_judge_sig_changes)

  print()
  print("=== JUDGES IN DIRECT AND SYMMETRIC INDIRECT AGREEMENT ===")
  print("-- Optimal lag lengths ---")
  print_dependent_data(direct_sym_indirect_judge_lags)
  if (direct_sym_indirect_judge_coeff_changes):
    print("-- Max coefficient changes ---")
    print_dependent_data(direct_sym_indirect_judge_coeff_changes)
  if (direct_sym_indirect_judge_ame_changes):
    print("-- Max AME changes ---")
    print_dependent_data(direct_sym_indirect_judge_ame_changes)
  if (direct_sym_indirect_judge_sig_changes):
    print("-- Significance changes ---")
    print_dependent_data(direct_sym_indirect_judge_sig_changes)

  print()


main()


