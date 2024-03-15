# convert_data_to_csv.py
# Daniele Bellutta
# 26 February 2020


import json
import csv


INPUT_FILE_NAME = "data/original.json"
OUTPUT_FILE_NAME = "data/cases.csv"
CITATIONS_FILE_NAME = "data/citations.csv"

NAME_REPLACEMENTS = {
  "Advisory Opinion.{2,40}Kosovo": "Advisory Opinion on Kosovo",
  "Ahmadou Sadio Diallo ( Guinea v. Congo)": "Ahmadou Sadio Diallo (Guinea v. Congo)",
}
EXCLUDE_CITATIONS = {
  ("52", "39"),
  ("79", "78"),
}


def load_data(file_name):
  data = None
  with open(file_name, "r") as input_file:
    data = json.load(input_file)
  return data


def isolate_attributes(data):
  isolated = {}

  for node in data["nodes"]:
    name = node["label"]
    if (name in NAME_REPLACEMENTS):
      name = NAME_REPLACEMENTS[name]

    attributes = node["attributes"]
    year = attributes["Year"]
    case_type = attributes["Type"]

    isolated[node["id"]] = {"name": name.strip(), "year": year.strip(), "type": case_type.strip()}

  for edge in data["edges"]:
    source_topic = edge["attributes"]["Source Type"].strip()
    target_topic = edge["attributes"]["Target Type"].strip()

    for decision, topic in zip([edge["source"], edge["target"]], [source_topic, target_topic]):
      if (("topic" in isolated[decision]) and (isolated[decision]["topic"] != topic)):
        print("ERROR", decision)
      else:
        isolated[decision]["topic"] = topic.strip()

  return isolated

def isolate_citations(data):
  isolated = []
  excluded = []
  for edge in data["edges"]:
    citation = (edge["source"], edge["target"])
    if (citation not in EXCLUDE_CITATIONS):
      isolated.append(citation)
    else:
      excluded.append((edge["id"], edge["attributes"]["Citation ID"], *citation))
  return (isolated, excluded)


def write_attributes(file_name, data):
  header = ["id"]
  for datum in data.values():
    header += list(datum.keys())
    break

  with open(file_name, "w") as output_file:
    writer = csv.DictWriter(output_file, fieldnames = header)
    writer.writeheader()
    for id, attributes in data.items():
      writer.writerow({"id": id, **attributes})

def write_citations(file_name, citations):
  with open(file_name, "w") as output_file:
    writer = csv.writer(output_file)
    writer.writerow(["source", "target"])
    for citation in citations:
      writer.writerow(list(citation))


def main():
  data = load_data(INPUT_FILE_NAME)
  attributes = isolate_attributes(data)
  write_attributes(OUTPUT_FILE_NAME, attributes)

  citations, excluded = isolate_citations(data)
  write_citations(CITATIONS_FILE_NAME, citations)

  print()
  print("=== Excluded Citations ===")
  for edge in excluded:
    print("Link ID %s, citation ID %s, source ID %s, target ID %s." % edge)
  print()


main()


