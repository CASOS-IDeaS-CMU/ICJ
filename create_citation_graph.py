# create_citation_graph.py
# Daniele Bellutta
# 8 April 2020


import csv
from collections import Counter
import networkx as nx

from support.data_processing import load_case_attributes
from support.graph_processing import write_graph


CITATIONS_FILE_NAME = "data/citations.csv"
CASES_FILE_NAME = "data/cases.csv"
AUTHORSHIP_FILE_NAME = "data/authorship.csv"
OUTPUT_FILE_NAME = "data/citation_graph.graphml"


def load_citations(file_name):
  citations = Counter()
  with open(file_name, "r") as input_file:
    reader = csv.DictReader(input_file)
    for row in reader:
      citations.update({(row["source"], row["target"]): 1})
  return citations

def load_decision_votes(file_name):
  decision_for = Counter()
  decision_against = Counter()

  with open(file_name, "r") as input_file:
    reader = csv.DictReader(input_file)

    for row in reader:
      weight = float(row["weight"])
      if (weight > 0):
        decision_for.update({row["decision"]: 1})
      elif (weight < 0):
        decision_against.update({row["decision"]: 1})

  return {d: {"votes_for": f, "votes_against": decision_against[d]} for d, f in decision_for.items()}


def create_graph(citations, case_attributes, decision_votes):
  graph = nx.DiGraph()
  case_years = {id: attributes["year"] for id, attributes in case_attributes.items()}
  graph.add_nodes_from([(d, {**a, **decision_votes[d]}) for d, a in case_attributes.items()])
  graph.add_edges_from([(i, j, {"weight": w, "year": case_years[i]}) for (i, j), w in citations.items()])
  return graph


def main():
  citations = load_citations(CITATIONS_FILE_NAME)
  case_attributes = load_case_attributes(CASES_FILE_NAME)
  decision_votes = load_decision_votes(AUTHORSHIP_FILE_NAME)
  graph = create_graph(citations, case_attributes, decision_votes)
  write_graph(OUTPUT_FILE_NAME, graph)


main()


