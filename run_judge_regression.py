# run_judge_regression.py
# Daniele Bellutta
# 29 April 2020


from support.regression import load_node_year_variables, generate_variable_coefficients, write_variable_coefficients


INPUT_PREFIX = "data/judge_variables/"
INPUT_SUFFIX = "_judge_variables.csv"
COEFFICIENTS_PREFIX = "data/judge_model_coefficients/"
COEFFICIENTS_SUFFIX = "_judge_model_coefficients.csv"

NETWORK_TYPES = [
  "direct",
#  "direct_and_indirect",
  "direct_and_symmetric_indirect",
]
SYMMETRIC_NETWORKS = {"direct", "direct_and_symmetric_indirect"}

INDEX = ("judge", "year")
TIME_VARIABLE = "current_year"

CONTROL_VARIABLES = {"seniority", "seniority_squared", "current_year", "num_votes_this_year", "ad_hoc_this_year"}
OFFSET_VARIABLE = "supported_decisions"

DEPENDENT_VARIABLES = ["citations_next_year", "citations_next_5_years", "citations_next_10_years"]
ASYMMETRIC_INDEPENDENT_VARIABLES = [
  {"hub"},
  {"authority"},
  {"in_degree"},
  {"out_degree"},
]
SYMMETRIC_INDEPENDENT_VARIABLES = [
  {"hub"},
  {"in_degree"},
]


def generate_input_file_name(network_type):
  return INPUT_PREFIX + str(network_type) + INPUT_SUFFIX

def generate_coefficients_file_name(network_type):
  return COEFFICIENTS_PREFIX + str(network_type) + COEFFICIENTS_SUFFIX


def main():
  for network_type in NETWORK_TYPES:
    print(network_type)
    judge_year_variables = load_node_year_variables(generate_input_file_name(network_type), INDEX)
    independent_variables = SYMMETRIC_INDEPENDENT_VARIABLES if (network_type in SYMMETRIC_NETWORKS) else ASYMMETRIC_INDEPENDENT_VARIABLES

    variable_coefficients = generate_variable_coefficients(judge_year_variables, independent_variables, DEPENDENT_VARIABLES, CONTROL_VARIABLES, offset_variable = OFFSET_VARIABLE, dependent_lags = {1,})
    write_variable_coefficients(generate_coefficients_file_name(network_type), variable_coefficients)


main()


