from bs4 import BeautifulSoup
import urllib3
import argparse
import json

URL = "https://eslint.org/docs/rules/"
recommended_set = set()
fix_set = set()


# Main function
def main(json_file):
    # Get page contents
    req = urllib3.PoolManager()
    res = req.request("GET", URL)
    soup = BeautifulSoup(res.data, "html.parser")

    # Open file passed in
    with open(json_file) as f:
        data = json.load(f)
        parse(data, soup)


# Parse eslintrc.json and eslint
def parse(data, soup):
    # Read in eslintrc options
    parser_options = data["parserOptions"]
    env = data["env"]
    extends = data["extends"]
    plugins = data["plugins"]
    rules = data["rules"]

    # Get deprecated table's contents
    deprecated_table = soup.find("h2", text="Deprecated").find_next("table")
    deprecated_dict = loop_through_2_table(deprecated_table)

    # Get removed table's contents
    removed_table = soup.find("h2", text="Removed").find_next("table")
    removed_dict = loop_through_2_table(removed_table)

    # Output options that can be changed
    compare_rules_to_deprecated_and_removed(rules, deprecated_dict)
    compare_rules_to_deprecated_and_removed(rules, removed_dict)

    # Get ECMAScript 6 if it's set in the env object
    if "es6" in env and env["es6"]:
        ecmaScript_table = soup.find("h2", text="ECMAScript 6").find_next("table")
        ecmaScript_dict = loop_through_4_table(ecmaScript_table)

    # Check if we should check if recommended rules are in the config
    if "eslint:recommended" in extends:
        compare_rules_to_recommended(rules)


# See if any of the user's rules are in the deprecated or removed tables
def compare_rules_to_deprecated_and_removed(rules, table_dict):
    # Loop through deprecated/removed tables
    for key in table_dict:
        # If rule is in user's rules
        if key in rules:
            rules_value = rules[key]
            table_dict_value = table_dict[key]

            output_string = 'Please remove "{}" as it is now outdated.'.format(key)
            # If there is a replacement, suggest it
            if table_dict_value != "":
                output_string += ' Please replace it with "{}".'.format(
                    table_dict_value
                )
            else:
                output_string += " There is currently no replacement."
            print(output_string)


# See if any of the user's rules are in the deprecated or removed tables
def compare_rules_to_recommended(rules):
    # Loop through recommended list
    for key in recommended_set:
        # If rule is in user's rules
        if key in rules:
            print(key, 'is already part of "eslint:recommended".')


# Loop through and process active tables
def loop_through_4_table(table):
    dictionary = {}

    # Loop through all rows in the tables
    rows = table.find_all("tr")
    for tr in rows:
        cols = tr.find_all("td")

        # Table rows should only have two columns: the rule and the replaced by rule
        if len(cols) == 4:
            recommended = cols[0]
            fix = cols[1]
            rule = cols[2].text
            description = cols[3].text

            # Verify recommended value exists
            span_recommended = recommended.find("span")
            if span_recommended and span_recommended.get("title") == "recommended":
                recommended_set.add(rule)

            # Verify fixable value exists
            span_fix = fix.find("span")
            if span_fix and span_fix.get("title") == "fixable":
                fix_set.add(rule)

            # Add to dictionary
            dictionary[rule] = description
    return dictionary


# Loop through and process deprecated and removed tables
def loop_through_2_table(table):
    dictionary = {}

    # Loop through all rows in the tables
    rows = table.find_all("tr")
    for tr in rows:
        cols = tr.find_all("td")

        # Table rows should only have two columns: the rule and the replaced by rule
        if len(cols) == 2:
            rule = cols[0].text
            replaced_by = cols[1].text

            # Update default value
            if replaced_by == "(no replacement)":
                replaced_by = ""

            # Add to dictionary
            dictionary[rule] = replaced_by
    return dictionary


# Main entry point for program
if __name__ == "__main__":
    message = "Checks the configuration of an eslintrc.json file."
    parser = argparse.ArgumentParser(description=message)

    # Add required file command line argument
    parser.add_argument("-f", "--file", help="JSON file to check.", required=True)
    args = parser.parse_args()

    main(args.file)
