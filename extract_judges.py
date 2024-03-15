# extract_judges.py
# Daniele Bellutta
# 27 February 2020


import re
import os
import csv
from collections import OrderedDict

from support.judge_countries import JUDGE_COUNTRIES


PREAMBLE_REGEX = re.compile(r"BEFORE:?(.*?)PermaLink:", re.IGNORECASE | re.DOTALL)
PRESIDENT_REGEX = re.compile("^[Before:\s*?]?President:?(.*)", re.IGNORECASE)
VICE_REGEX = re.compile("Vice-President:?(.*)", re.IGNORECASE)
JUDGES_REGEX = re.compile("Judges:?(.*)", re.IGNORECASE)
AD_HOC_REGEX = re.compile("Judges? ad hoc:?(.*)", re.IGNORECASE)

PATTERNS = OrderedDict()
PATTERNS["president"] = PRESIDENT_REGEX
PATTERNS["vice-president"] = VICE_REGEX
PATTERNS["judges"] = JUDGES_REGEX
PATTERNS["ad hoc"] = AD_HOC_REGEX

JUDGE_REPLACEMENTS = {
  "badawi pasha": "badawi",
  "bed-jaoui": "bedjaoui",
  "benjaoui": "bedjaoui",
  "cancado trindade": "cançado trindade",
  "cançado trindade": "cançado trindade",
  "cançado trindade": "cançado trindade",
  "gerald fitz-maurice": "fitzmaurice",
  "gerald fitzmaurice": "fitzmaurice",
  "sepulveda": "sepúlveda-amor",
  "sepulveda-amor": "sepúlveda-amor",
  "sepúlveda-amor": "sepúlveda-amor",
  "sepúlveda‐amor": "sepúlveda-amor",
  "shahabud-deen": "shahabuddeen",
  "spiro-poulos": "spiropoulos",
  "torres bernardez": "torres bernárdez",
  "winiarsky": "winiarski",
  "zoricic": "zoričić",
  "zoričič": "zoričić",
  "benegalrau": "rau",
  "benegal rau": "rau",
  "jimenez de arechaga": "jimenez de aréchaga",
  "petren": "petrén",
  "tarassov": "tarasov",
  "tarrasov": "tarasov",
  "schwebiel": "schwebel",
  "urrutia holguin": "urrutia holguín",
  "urrutia Hholgltn": "urrutia holguín",
  "urrutia holgltn": "urrutia holguín",
  "bustamante": "bustamante y rivero",
  "sorensen": "sørensen",
  "zoricic": "zoričić",
  "zortcic": "zoričić",
  "arnold mcnair": "mcnair",
  "torres bernerdez": "torres bernárdez",
  "torres bernardez": "torres bernárdez",
  "kreca": "kreća",
  "franklin berman": "berman",
  "roberto ago": "ago",
  "manfred lachs": "lachs",
  "mohammed bedjaoui": "bedjaoui",
  "nagendra singh": "singh",
  "levi carneiro": "carneiro",
  "robert jennings": "jennings",
  "muhammad zafrulla khan": "zafrulla khan",
  "hersch lauterpacht": "lauterpacht",
  "percy spender": "spender",
  "humphrey waldock": "waldock",
  "aguilar mawdsley": "aguilar-mawdsley",
  "jose sette-camara": "sette-camara",
  "garfield barwick": "barwick",
  "jose maria ruda": "ruda",
  "ninian stephen": "stephen",
  "louis mbanefo": "mbanefo",
  "sreenivasa rao": "rao",
  "beb a don": "beb à don",
  "karim sandjabi": "sandjabi",
}

TITLE_REGEXES = [
  re.compile(r"(^|\s)Judges?(\s|$)", re.IGNORECASE),
  re.compile(r"(^|\s)Sir(\s|$)", re.IGNORECASE),
  re.compile(r"(^|\s)(Acting )?Vice( |-)President(\s|$)", re.IGNORECASE),
  re.compile(r"(^|\s)(Acting )?President(\s|$)", re.IGNORECASE),
  re.compile(r"(^|\s)ad( |-)?hoc(\s|$)", re.IGNORECASE),
]

DISSENTING_OPINION_REGEX = re.compile(r"(Joint )?Dissenting opinion (of|by) ([\w\.\s-]+?)$", re.IGNORECASE | re.MULTILINE | re.UNICODE)

INPUT_DIRECTORY = "data/decisions/"
AUTHORSHIP_FILE_NAME = "data/authorship.csv"
JUDGES_FILE_NAME = "data/judges.csv"


def load_decision(file_name):
  data = None
  with open(file_name, "r") as input_file:
    data = input_file.read()
  return data


def remove_titles(name):
  revised_name = " ".join(name.strip().strip(".").lower().replace(".", ". ").split())
  revised_name = " ".join([token for token in revised_name.split(" ") if (not token.endswith("."))])
  for title in TITLE_REGEXES:
    revised_name = re.sub(title, " ", revised_name)
  revised_name = " ".join([token for token in revised_name.split() if (token.replace(" ", ""))])
  return revised_name.strip()

def clean_name(name):
  cleaned = remove_titles(name.strip().lower())
  return JUDGE_REPLACEMENTS[cleaned] if (cleaned in JUDGE_REPLACEMENTS) else cleaned

def extract_names(judges):
  cleaned = {clean_name(name.strip()).strip() for name in re.split(",|;| and ", judges.lower())}
  return {name for name in cleaned if (name)}


def preamble_judges(decision):
  judges = set()
  ad_hoc = set()
  matched = set()

  preamble = re.search(PREAMBLE_REGEX, decision).group(1).strip().splitlines()
  preamble = [line.strip() for line in preamble]
  preamble = [line for line in preamble if (line)]

  for line in preamble:
    for office, pattern in PATTERNS.items():
      if ((office not in matched) and (not (("ad hoc" in line) and (office == "judges")))):
        matches = re.search(pattern, line)

        if (matches):
          matched.add(office)
          people = extract_names(matches.group(1).strip().strip(";").strip(".").strip(":"))
          if ("acting president" in people):
            people.remove("acting president")

          if (office == "ad hoc"):
            ad_hoc |= people
          else:
            judges |= people

          break

  return (judges, ad_hoc)

def dissenting_judges(decision):
  judges = set()
  for match in re.finditer(DISSENTING_OPINION_REGEX, decision):
    judges |= extract_names(match.group(3))
  return judges

def determine_judges(decision):
  judges, ad_hoc = preamble_judges(decision)
  judge_weights = {judge: 1 for judge in judges}
  judge_weights.update({judge: 1 for judge in ad_hoc})

  for judge in dissenting_judges(decision):
    if (judge in judge_weights):
      judge_weights[judge] = -1

  return {j: (w, (j in ad_hoc)) for j, w in judge_weights.items()}


def retrieve_judges(directory):
  decision_judges = {}
  for file_name in os.listdir(directory):
    if (file_name.endswith(".txt")):
      id = file_name[:-4]
      decision = load_decision(os.path.join(directory, file_name))
      decision_judges[id] = determine_judges(decision)
  return decision_judges


def number_judges(decision_judges):
  judge_ids = {j: i for i, j in enumerate(sorted(set.union(*[set(judges.keys()) for judges in decision_judges.values()])))}
  judge_attributes = {}
  authorship = []

  for decision, judges in decision_judges.items():
    for judge, (weight, ad_hoc) in judges.items():
      authorship.append((judge_ids[judge], decision, weight, ad_hoc))
      if (judge in judge_attributes):
        judge_attributes[judge][1].add(ad_hoc)
      else:
        judge_attributes[judge] = [judge_ids[judge], {ad_hoc}]

  return (judge_attributes, authorship)


def output_authorship(file_name, authorship):
  with open(file_name, "w") as output_file:
    writer = csv.writer(output_file)
    writer.writerow(["judge", "decision", "weight", "ad hoc"])
    for (judge, decision, weight, ad_hoc) in authorship:
      writer.writerow([judge, decision, weight, ad_hoc])


def output_judge_attributes(file_name, judge_attributes):
  with open(file_name, "w") as output_file:
    writer = csv.writer(output_file)
    writer.writerow(["id", "name", "country", "position(s)"])
    for name, (id, positions) in judge_attributes.items():
      position = 0
      if (True in positions):
        position += 1
        if (False in positions):
          position += 1
      writer.writerow([id, name, JUDGE_COUNTRIES[name], position])


def main():
  decision_judges = retrieve_judges(INPUT_DIRECTORY)
  judge_attributes, authorship = number_judges(decision_judges)
  output_authorship(AUTHORSHIP_FILE_NAME, authorship)
  output_judge_attributes(JUDGES_FILE_NAME, judge_attributes)


main()


