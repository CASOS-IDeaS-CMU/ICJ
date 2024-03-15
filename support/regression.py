# regression.py
# Daniele Bellutta
# 29 April 2020


import csv
import numpy as np
import pandas as pd
from statistics import stdev, mean
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats.mstats import zscore
from statsmodels.stats.outliers_influence import variance_inflation_factor

import rpy2.robjects as ro
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
import rpy2.robjects.conversion as cv

importr("glm2")
importr("MASS")
importr("lmtest")
importr("sandwich")
importr("margins")
importr("AER")
importr("Metrics")
importr("bbmle")

from support.variable_computation import generate_lagged_variable_name


AME_RANGE_SD = 1.0

NONE_CONVERTER = cv.Converter("None converter")
NONE_CONVERTER.py2rpy.register(type(None), lambda _: ro.r("NULL"))


def load_node_year_variables(file_name, index):
  return pd.read_csv(file_name, index_col = index)


def remove_variables(decision_year_variables, keep):
  remove = {v for v in decision_year_variables.columns if (v not in keep)}
  removed = decision_year_variables.drop(columns = remove)
  return removed.dropna()

def standardize_variables(data, variables):
  standardized = data.copy()
  means = {}
  deviations = {}

  for variable in variables:
    if (np.issubdtype(standardized[variable].dtype, np.number)):
      variable_data = list(standardized[variable])
      standardized[variable] = zscore(variable_data)
      means[variable] = np.mean(variable_data)
      deviations[variable] = np.std(variable_data)

  return (standardized, means, deviations)

def compute_variable_collinearities(data):
  variable_vifs = {}
  numeric_data = data.select_dtypes(include = ["number"])
  for v, variable in enumerate(numeric_data.columns):
    variable_vifs[variable] = variance_inflation_factor(numeric_data.values, v)
  return variable_vifs

def prepare_offset(data, variable):
  if ((variable) and (data[variable] == 0).any()):
    data[variable] += 0.01


def fit_glm(data, independent_variables, dependent_variable, offset_variable):
  model_results = {"num_data": data.shape[0], "dependent_std_dev": float(stdev(data[dependent_variable].tolist())), "dependent_mean": float(mean(data[dependent_variable].tolist()))}
  variable_results = {}

  formula_offset = str(dependent_variable) + " ~ " + (" + ".join(independent_variables))
  if (offset_variable):
    formula_offset += " + offset(log(%s))" % (offset_variable)
  variables = "c(" + ", ".join([("\"%s\"" % (v)) for v in independent_variables if (not v.startswith("lagged_"))]) + ")"
  ame_half = float(AME_RANGE_SD) / 2.0
  ame_change = "c(" + str(-ame_half) + ", " + str(ame_half) + ")"

  with localconverter(ro.default_converter + pandas2ri.converter + NONE_CONVERTER):
    r_code = """
      fit_model <- function(data) {{
        options(warn = 1)

        dispersion <- dispersiontest(glm({formula_offset}, data = data, family = poisson), trafo = 1)
        dispersion_p <- dispersion$p.value
        dispersion_alpha <- dispersion$estimate

        model <- glm({formula_offset}, data = data, family = quasipoisson(link = "log"))
        dispersion = sum((model$weights * model$residuals^2)[model$weights > 0])/model$df.residual

        vcov <- vcovHC(model, type = "HC3")
        coefficients <- coeftest(model, vcov. = vcov)
        confidence_intervals <- coefci(model, level = 0.95, vcov. = vcov)
        marg_effects <- summary(margins(model, data = data, vcov = vcov, level = 0.95, variables = {variables}, change = {ame_change}))

        fit_rmse <- rmse(data${dependent_variable}, predict(model, newdata = data, type = "response"))
        model <- glm({formula_offset}, data = data, family = poisson(link = "log"))
        qaic <- qAIC(model, dispersion=dispersion, nobs=length(data))

        return(list(row.names(coefficients), coefficients, confidence_intervals, marg_effects, dispersion_p, dispersion_alpha, fit_rmse, qaic))
      }}
    """
    ro.r(r_code.format(formula_offset = formula_offset, variables = variables, ame_change = ame_change, dependent_variable = dependent_variable))

    variable_names, coefficients_matrix, intervals_matrix, marginal_effects, dispersion_p, dispersion_alpha, fit_rmse, qaic = ro.globalenv["fit_model"](data)
    dispersion_p = dispersion_p[0]
    dispersion_alpha = dispersion_alpha[0]
    fit_rmse = fit_rmse[0]
    qaic = qaic[0]

    model_results["regression_type"] = "quasi-Poisson"
    model_results["dispersion_p-value"] = dispersion_p
    model_results["dispersion_alpha"] = dispersion_alpha
    model_results["qaic"] = qaic

    model_results["fit_rmse"] = fit_rmse
    model_results["fit_rmse_over_dep_std_dev"] = fit_rmse /  model_results["dependent_std_dev"]

    coefficients = list(coefficients_matrix[:, 0])
    std_errors = list(coefficients_matrix[:, 1])
    z_stats = list(coefficients_matrix[:, 2])
    p_values = list(coefficients_matrix[:, 3])
    confidence_intervals = [tuple(ci) for ci in list(intervals_matrix)]

    for variable, coefficient, std_error, z_stat, p_value, (ci_low, ci_high) in zip(variable_names, coefficients, std_errors, z_stats, p_values, confidence_intervals):
      variable_name = variable[:-4] if (variable.endswith("TRUE")) else variable
      variable_results[variable_name] = {
        "coefficient": coefficient,
        "coeff_std_error": std_error,
        "coeff_z-statistic": z_stat,
        "coeff_p-value": p_value,
        "coeff_95_ci_lower": ci_low,
        "coeff_95_ci_upper": ci_high,
      }

    for variable, ame, std_error, z_stat, p_value, ci_low, ci_high in zip(marginal_effects["factor"], marginal_effects["AME"], marginal_effects["SE"], marginal_effects["z"], marginal_effects["p"], marginal_effects["lower"], marginal_effects["upper"]):
      variable_results[variable].update({
        "avg_marginal_effect": ame,
        "ame_std_error": std_error,
        "ame_z-statistic": z_stat,
        "ame_p-value": p_value,
        "ame_95_ci_lower": ci_low,
        "ame_95_ci_upper": ci_high,
        "ame_over_sd": (float(ame) / model_results["dependent_std_dev"]),
        "ame_std_error_over_sd": (float(std_error) / model_results["dependent_std_dev"])
      })

  return (model_results, variable_results)


def prepare_regression_variables(node_year_variables, independent_variables, dependent_variable, offset_variable, dependent_lags = {1,}):
  lagged_dependent_variables = {generate_lagged_variable_name(dependent_variable, lag_length = lag_length) for lag_length in dependent_lags}
  categorical_variables = set(node_year_variables.select_dtypes(exclude = ["number"]).columns).union({c for c in node_year_variables.columns if (c.startswith("categorical_"))}).intersection(set(independent_variables))
  regressors = (set(independent_variables) | lagged_dependent_variables) - categorical_variables - {offset_variable}

  regression_variables = remove_variables(node_year_variables, set(independent_variables) | {dependent_variable, *lagged_dependent_variables, offset_variable})
  regression_variables, variable_means, variable_deviations = standardize_variables(regression_variables, regressors - lagged_dependent_variables)

  regression_variables = regression_variables.reindex(sorted(regression_variables.columns), axis = 1)
  prepare_offset(regression_variables, offset_variable)

  return (regression_variables, regressors | categorical_variables, variable_means, variable_deviations)


def fit_model(node_year_variables, independent_variables, dependent_variable, control_variables, offset_variable = None, dependent_lags = {1,}):
  regression_variables, regressors, variable_means, variable_deviations = prepare_regression_variables(node_year_variables, independent_variables | control_variables, dependent_variable, offset_variable, dependent_lags = dependent_lags)
  model_results, variable_results = fit_glm(regression_variables, list(sorted(list(regressors))), dependent_variable, offset_variable)
  return (model_results, variable_results, variable_means, variable_deviations)


def generate_variable_coefficients(node_year_variables, independent_variable_sets, dependent_variables, control_variables, offset_variable = None, dependent_lags = {1,}):
  dependent_independent_results = {}

  for dependent_variable in dependent_variables:
    dependent_independent_results[dependent_variable] = {}
    lagged_control_variables = set(control_variables) | {generate_lagged_variable_name(dependent_variable, lag_length = lag_length) for lag_length in dependent_lags}

    for independent_variables in independent_variable_sets:
      key = frozenset(independent_variables)
      dependent_independent_results[dependent_variable][key] = {}

      model_results, variable_results, _, _ = fit_model(node_year_variables, independent_variables, dependent_variable, lagged_control_variables, offset_variable = offset_variable, dependent_lags = dependent_lags)
      variable_vifs = compute_variable_collinearities(node_year_variables[set(independent_variables) | lagged_control_variables].dropna())

      for variable, results in variable_results.items():
        augmented_results = dict(results)
        augmented_results.update({("model_" + key): value for key, value in model_results.items()})
        augmented_results["vif"] = variable_vifs[variable] if (variable in variable_vifs) else None
        dependent_independent_results[dependent_variable][key][variable] = augmented_results

  return dependent_independent_results


def write_variable_coefficients(file_name, dependent_independent_results):
  columns = set()
  for independent_results in dependent_independent_results.values():
    for variable_results in independent_results.values():
      for results in variable_results.values():
        columns |= set(results.keys())

  with open(file_name, "w") as output_file:
    writer = csv.DictWriter(output_file, fieldnames = ["dependent_variable", "independent_variables", "variable"] + list(sorted(list(columns))))
    writer.writeheader()

    for dependent_variable, independent_results in dependent_independent_results.items():
      for independent_variables, variable_results in independent_results.items():
        independent_text = str(independent_variables)

        if (len(independent_variables) == 1):
          for independent_variable in independent_variables:
            independent_text = str(independent_variable)
            break

        for variable, results in variable_results.items():
          row = {
            "dependent_variable": dependent_variable,
            "independent_variables": independent_text,
            "variable": variable,
          }
          row.update(results)
          writer.writerow(row)


