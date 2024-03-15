# data_processing.py
# Daniele Bellutta
# 27 April 2020


import csv


CASE_TYPES = {
  "J": "Jurisdiction",
  "A": "Merits",
  "B": "Advisory",
}


def load_case_attributes(file_name):
  case_attributes = {}

  with open(file_name, "r") as input_file:
    reader = csv.DictReader(input_file)

    for row in reader:
      attributes = dict(row)
      attributes.pop("id")
      attributes["year"] = int(attributes["year"])
      attributes["type"] = CASE_TYPES[attributes["type"]]
      case_attributes[row["id"]] = attributes

  return case_attributes

def load_judge_attributes(file_name):
  judge_attributes = {}
  with open(file_name, "r") as input_file:
    reader = csv.DictReader(input_file)
    for row in reader:
      attributes = dict(row)
      attributes.pop("id")
      judge_attributes[row["id"]] = attributes
  return judge_attributes

