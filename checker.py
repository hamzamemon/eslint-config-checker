from bs4 import BeautifulSoup
import urllib3
import argparse
import json

URL = "https://eslint.org/docs/rules/"


# Main function
def main(json_file):
    # Get page contents
    req = urllib3.PoolManager()
    res = req.request("GET", URL)
    soup = BeautifulSoup(res.data, "html.parser")

    # Get deprecated table's contents
    deprecated_table = soup.find("h2", text="Deprecated").find_next("table")
    deprecated_dict = loop_through_2_table(deprecated_table)

    # Get removed table's contents
    removed_table = soup.find("h2", text="Removed").find_next("table")
    removed_dict = loop_through_2_table(removed_table)

    # Open file passed in
    with open(json_file) as f:
        data = json.load(f)
        parse_json(data, deprecated_dict, removed_dict)


# Parse eslintrc.json
def parse_json(data, deprecated_dict={}, removed_dict={}):
    # Read in eslintrc options
    parser_options = data["parserOptions"]
    env = data["env"]
    extends = data["extends"]
    plugins = data["plugins"]
    rules = data["rules"]

    # Output options that can be changed
    compare_rules_to_deprecated_and_removed(rules, deprecated_dict)
    compare_rules_to_deprecated_and_removed(rules, removed_dict)


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
