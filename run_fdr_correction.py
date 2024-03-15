# run_fdr_correction.py
# Daniele Bellutta
# 24 November 2021


import csv
from os.path import join, dirname, basename
from statsmodels.stats.multitest import multipletests


INPUT_FILE_NAMES = {
  "data/decision_model_coefficients.csv",
  "data/judge_model_coefficients/direct_judge_model_coefficients.csv",
#  "data/judge_model_coefficients/direct_and_indirect_judge_model_coefficients.csv",
  "data/judge_model_coefficients/direct_and_symmetric_indirect_judge_model_coefficients.csv",
}

P_VALUE_COLUMNS = {"coeff_p-value", "ame_p-value"}
VARIABLE_NAME_COLUMN = "variable"
CORRECTION_METHOD = "fdr_bh"


def load_result_p_values(file_name):
  result_p_values = {}
  with open(file_name, "r") as input_file:
    for row in csv.DictReader(input_file):
      result = {k: v for k, v in row.items() if (k not in P_VALUE_COLUMNS)}
      result_p_values[tuple(result.items())] = {column: (float(row[column]) if (row[column]) else None) for column in P_VALUE_COLUMNS}
  return result_p_values

def load_file_result_p_values(file_names):
  file_result_p_values = {}
  for file_name in file_names:
    file_result_p_values[file_name] = load_result_p_values(file_name)
  return file_result_p_values


def generate_corrected_column_name(column_name):
  return "corrected_" + str(column_name)

def correct_result_p_values(file_result_p_values):
  file_result_corrected = {}
  for file_name, result_p_values in file_result_p_values.items():
    file_result_corrected[file_name] = {result: {} for result in result_p_values.keys()}

  file_names = list(sorted(file_result_corrected.keys()))
  f_results = []
  f_r_columns = []
  for file_name in file_names:
    results = [result for result in file_result_p_values[file_name].keys() if ("Intercept" not in dict(result)[VARIABLE_NAME_COLUMN])]
    f_results.append(results)
    f_r_columns.append([[k for k, v in file_result_p_values[file_name][result].items() if (v is not None)] for result in results])

  uncorrected_values = []
  for f, file_name in enumerate(file_names):
    for r, result in enumerate(f_results[f]):
      uncorrected_values += [file_result_p_values[file_name][result][column] for column in f_r_columns[f][r]]

  _, corrected_values, _, _ = multipletests(uncorrected_values, method = CORRECTION_METHOD)

  v = 0
  for f, file_name in enumerate(file_names):
    for r, result in enumerate(f_results[f]):
      for column in f_r_columns[f][r]:
        file_result_corrected[file_name][result][generate_corrected_column_name(column)] = corrected_values[v]
        v += 1

  return file_result_corrected


def write_result_p_values(file_name, result_p_values, result_corrected):
  columns = set()
  for result, column_p_values in result_p_values.items():
    columns |= set(dict(result).keys())
    columns |= set(column_p_values.keys())
  for column_p_values in result_corrected.values():
    columns |= set(column_p_values.keys())

  with open(file_name, "w") as output_file:
    writer = csv.DictWriter(output_file, fieldnames = list(columns))
    writer.writeheader()

    for result, column_p_values in result_p_values.items():
      row = dict(result)
      row.update(column_p_values)
      row.update(result_corrected[result])
      writer.writerow(row)


def generate_output_file_name(file_name):
  return join(dirname(file_name), "corrected_" + basename(file_name))

def write_file_result_p_values(file_result_p_values, file_result_corrected):
  for file_name, result_p_values in file_result_p_values.items():
    write_result_p_values(generate_output_file_name(file_name), result_p_values, file_result_corrected[file_name])


def main():
  file_result_p_values = load_file_result_p_values(INPUT_FILE_NAMES)
  file_result_corrected = correct_result_p_values(file_result_p_values)
  write_file_result_p_values(file_result_p_values, file_result_corrected)


main()


