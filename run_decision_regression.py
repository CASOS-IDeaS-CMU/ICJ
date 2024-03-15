# run_decision_regression.py
# Daniele Bellutta
# 13 April 2020


from support.regression import load_node_year_variables, generate_variable_coefficients, write_variable_coefficients


INPUT_FILE_NAME = "data/decision_variables.csv"
COEFFICIENTS_FILE_NAME = "data/decision_model_coefficients.csv"

INDEX = ("decision", "year")
TIME_VARIABLE = "current_year"
CONTROL_VARIABLES = {"age", "age_squared", "type", "current_year"}

DEPENDENT_VARIABLES = ["citations_next_year", "citations_next_5_years", "citations_next_10_years"]
INDEPENDENT_VARIABLES = [
  {"pagerank"},
  {"reverse_pagerank"},
  {"hub"},
  {"authority"},
  {"unanimity"},
]


def main():
  decision_year_variables = load_node_year_variables(INPUT_FILE_NAME, INDEX)
  variable_coefficients = generate_variable_coefficients(decision_year_variables, INDEPENDENT_VARIABLES, DEPENDENT_VARIABLES, CONTROL_VARIABLES, dependent_lags = {1,})
  write_variable_coefficients(COEFFICIENTS_FILE_NAME, variable_coefficients)


main()


