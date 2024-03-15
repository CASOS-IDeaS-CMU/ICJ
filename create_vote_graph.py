# create_vote_graph.py
# Daniele Bellutta
# 27 April 2020


import csv
import networkx as nx

from support.data_processing import load_case_attributes, load_judge_attributes
from support.graph_processing import write_graph


AUTHORSHIP_FILE_NAME = "data/authorship.csv"
CASES_FILE_NAME = "data/cases.csv"
JUDGES_FILE_NAME = "data/judges.csv"
OUTPUT_FILE_NAME = "data/vote_graph.graphml"


def load_judge_votes(file_name):
  judge_votes = {}
  judge_positions = {}

  with open(file_name, "r") as input_file:
    reader = csv.DictReader(input_file)
    for row in reader:
      judge_votes[(row["judge"], row["decision"])] = int(row["weight"])
      judge_positions[(row["judge"], row["decision"])] = ("true" in row["ad hoc"].lower())

  return (judge_votes, judge_positions)


def judge_label(id):
  return "j%s" % (str(id))

def decision_label(id):
  return str(id)

def create_graph(judge_votes, case_attributes, judge_attributes, judge_positions):
  graph = nx.DiGraph()

  graph.add_nodes_from([(judge_label(j), {"class": "judge", **judge_attributes[j]}) for (j, _) in judge_votes.keys()])
  graph.add_nodes_from([(decision_label(d), {"class": "decision", **case_attributes[d]}) for (_, d) in judge_votes.keys()])
  graph.add_edges_from([(judge_label(j), decision_label(d), {"weight": w, "year": case_attributes[d]["year"], "ad_hoc": judge_positions[(j, d)]}) for (j, d), w in judge_votes.items()])

  for judge, _, attributes in graph.edges(data = True):
    if ("year" in graph.nodes[judge]):
      if (attributes["year"] < graph.nodes[judge]["year"]):
        graph.nodes[judge]["year"] = attributes["year"]
      elif (attributes["year"] > graph.nodes[judge]["last_year"]):
        graph.nodes[judge]["last_year"] = attributes["year"]
    else:
      graph.nodes[judge]["year"] = attributes["year"]
      graph.nodes[judge]["last_year"] = attributes["year"]

  return graph


def main():
  judge_votes, judge_positions = load_judge_votes(AUTHORSHIP_FILE_NAME)
  case_attributes = load_case_attributes(CASES_FILE_NAME)
  judge_attributes = load_judge_attributes(JUDGES_FILE_NAME)
  graph = create_graph(judge_votes, case_attributes, judge_attributes, judge_positions)
  write_graph(OUTPUT_FILE_NAME, graph)


main()


