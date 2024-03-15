# plot_judge_timeline.py
# Daniele Bellutta
# 25 January 2024


import csv
from collections import Counter

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.colors import TABLEAU_COLORS

from support.data_processing import load_case_attributes, load_judge_attributes
from support.fonts import set_font
from support.fonts import DEFAULT_FAMILY, DEFAULT_FONT


JUDGES_FILE_NAME = "data/judges.csv"
CASES_FILE_NAME = "data/cases.csv"
AUTHORSHIP_FILE_NAME = "data/authorship.csv"

OUTPUT_FILE_NAME = "figures/judge_timeline.png"


def load_judge_year_votes(judges_file_name, cases_file_name, authorship_file_name):
  judge_year_votes = {}
  jid_names = {id: attributes["name"] for id, attributes in load_judge_attributes(judges_file_name).items()}
  cid_years = {id: attributes["year"] for id, attributes in load_case_attributes(cases_file_name).items()}
  with open(authorship_file_name, "r") as input_file:
    for row in csv.DictReader(input_file):
      judge = jid_names[row["judge"]].upper() if (row["ad hoc"] == "True") else jid_names[row["judge"]].lower()
      year = cid_years[row["decision"]]
      if (judge in judge_year_votes):
        judge_year_votes[judge].update({year: 1})
      else:
        judge_year_votes[judge] = Counter({year: 1})
  return judge_year_votes


def combine_tenures(judge_year_votes, adhoc_year_votes):
  combined_year_votes = {}
  for judge, year_votes in judge_year_votes.items():
    if (judge in adhoc_year_votes):
      combined_year_votes[judge] = year_votes + adhoc_year_votes[judge]
    else:
      combined_year_votes[judge] = year_votes
  for judge, year_votes in adhoc_year_votes.items():
    if (judge not in combined_year_votes):
      combined_year_votes[judge] = year_votes
  return combined_year_votes


def find_conflicts(judge_spans, judge, other_judges):
  conflict_exists = False
  min_year, max_year = judge_spans[judge]
  for other_judge in other_judges:
    other_min, other_max = judge_spans[other_judge]
    if (min(max_year, other_max) - max(min_year, other_min) >= 0):
      conflict_exists = True
      break
  return conflict_exists 

def deconflict_judges(judge_year_votes):
  group_judges, num_groups = {}, 0
  judge_spans = {judge: (min(year_votes.keys()), max(year_votes.keys())) for judge, year_votes in judge_year_votes.items()}
  sorted_judges = [j for j, _ in sorted([(j, s) for j, s in judge_spans.items() if (j.islower())], key = lambda js: js[1][1] - js[1][0], reverse = True)]

  for judge in sorted_judges:
    assigned_group = None
    adhoc_name = judge.upper()

    for group in range(0, num_groups):
      if (not find_conflicts(judge_spans, judge, group_judges[group])):
        if ((adhoc_name not in judge_year_votes) or (not find_conflicts(judge_spans, adhoc_name, group_judges[group]))):
          assigned_group = group
          break

    if (assigned_group is None):
      assigned_group = num_groups
      group_judges[assigned_group] = {judge,}
      num_groups += 1
    else:
      group_judges[assigned_group].add(judge)
    if (adhoc_name in judge_year_votes):
      group_judges[assigned_group].add(adhoc_name)

  return group_judges


def identify_missing_years(judge_year_votes):
  missing_years = set()
  min_year = min(min(year_votes.keys()) for year_votes in judge_year_votes.values())
  max_year = max(max(year_votes.keys()) for year_votes in judge_year_votes.values())
  for year in range(min_year + 1, max_year):
    present = False
    for year_votes in judge_year_votes.values():
      if (year in year_votes):
        present = True
        break
    if (not present):
      missing_years.add(year)
  return missing_years

def separate_tenures(year_votes, missing_years):
  tenures = []
  if (len(year_votes) > 1):
    years = list(sorted(year_votes.keys()))
    tenure = {years[0]: year_votes[years[0]]}
    for prev_year, curr_year in zip(years[:-1], years[1:]):
      if (all((y in missing_years) for y in range(prev_year + 1, curr_year))):
        tenure[curr_year] = year_votes[curr_year]
      else:
        tenures.append(tenure)
        tenure = {curr_year: year_votes[curr_year]}
    tenures.append(tenure)
  else:
    tenures.append(year_votes)
  return tenures


def generate_judge_color(judge_colors, judge, color_palette):
  judge_name = judge.lower()
  if (judge_name not in judge_colors):
    judge_colors[judge_name] = color_palette[len(judge_colors) % len(color_palette)]
  return judge_colors[judge_name]

def plot_year_votes(year_votes, group, max_num_votes, color):
  years, num_votes = None, None
  if (len(year_votes) > 1):
    num_votes = max(year_votes.values())
    years = sorted(sum(([year] * n_votes for year, n_votes in year_votes.items()), []))
  else:
    year = next(iter(year_votes.keys()))
    num_votes = year_votes[year]
    years = ([year - 0.125,] * num_votes) + ([year,] * num_votes) + ([year + 0.125,] * num_votes)
  parts = plt.violinplot(years, positions = [group,], vert = False, widths = num_votes / max_num_votes, showextrema = False, showmeans = False, showmedians = False)
  for pc in parts["bodies"]:
    pc.set_facecolor(color)
    pc.set_alpha(0.5)

def plot_judge_votes(file_name, judge_year_votes):
  group_judges = deconflict_judges(judge_year_votes)
  max_num_votes = max(max(year_votes.values()) for year_votes in judge_year_votes.values())
  missing_years = identify_missing_years(judge_year_votes)
  color_palette = list(sorted(TABLEAU_COLORS.keys()))
  judge_colors = {}

  figure = plt.figure(figsize = (8, 4))
  axes = plt.axes()

  for group, judges in group_judges.items():
    for judge in judges:
      color = generate_judge_color(judge_colors, judge, color_palette)
      for year_votes in separate_tenures(judge_year_votes[judge], missing_years):
        plot_year_votes(year_votes, group, max_num_votes, color)

  plt.autoscale(enable = True, axis = "x", tight = True)
  plt.autoscale(enable = True, axis = "y", tight = True)
  axes.get_yaxis().set_visible(False)
  axes.spines[["left", "top", "right"]].set_visible(False)

  axes.xaxis.get_ticklocs(minor = True)
  axes.minorticks_on()
  axes.xaxis.set_minor_locator(MultipleLocator(1))
  plt.grid(axis = "x", linestyle = ":", linewidth = 0.5, alpha = 0.5)
  axes.set_axisbelow(True)

  plt.xlabel("Year")

  for axis in ["top", "bottom", "left", "right"]:
    axes.spines[axis].set_linewidth(0.5)
  axes.tick_params(width = 0.5)

  plt.savefig(file_name, bbox_inches = "tight", dpi = 300)
  plt.close()


def main():
  set_font(plt, DEFAULT_FAMILY, DEFAULT_FONT)
  judge_year_votes = load_judge_year_votes(JUDGES_FILE_NAME, CASES_FILE_NAME, AUTHORSHIP_FILE_NAME)
  plot_judge_votes(OUTPUT_FILE_NAME, judge_year_votes)


main()


