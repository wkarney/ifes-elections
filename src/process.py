"""Utilities for processing raw json exports.
"""
import json
import pandas as pd
from src import utils


def extract_results(raw):
    """Extract results from raw data JSON.

    Args:
        raw (list): Pages of raw elections JSON.

    Returns:
        list: Results extracted from all pages.
    """
    results = []
    for page in raw:
        results.extend(page["results"])
    return results


def process_elections(results):
    """Process elections data from raw results json.

    Args:
        results (list): Results from elections json.

    Returns:
        pandas.DataFrame: election data, indexed by election ID.
    """
    e = tidy_elections(results)
    n = tidy_names(results)
    d = tidy_districts(results)
    v = tidy_verified(results)
    return pd.concat([e, n, d, v], axis=1)


def process_voting_methods(results):
    """Process voting methods data from raw results json.

    Args:
        results (list): Resuts from elections json.

    Returns:
        pandas.DataFrame: voting methods, indexed by election and method ID.
    """
    return tidy_voting_methods(results)


def tidy_names(results):
    """Extract names from elections json.

    Args:
        results (list): Results from elections json.

    Returns:
        pandas.Series: election names, indexed by election ID.
    """
    # Extract election names.
    records = dict()
    for result in results:
        records[result["election_id"]] = result["election_name"]["en_US"]

    # Make an election name series.
    return (pd.Series(records, name="election_name")
              .rename_axis(index="election_id"))


def tidy_districts(results):
    """Extract district information from elections json.

    Args:
        results (list): Results from elections json.

    Returns:
        pandas.DataFrame: election district information, indexed by election ID.
    """
    # Extract district information.
    records = dict()
    for result in results:
        records[result["election_id"]] = result["district"]

    # Make a districts dataframe.
    return (pd.DataFrame.from_dict(records, orient="index")
              .rename_axis("election_id"))


def tidy_elections(results):
    """Extract elections information from elections json.

    Args:
        results (list): Results from elections json.

    Returns:
        pandas.DataFrame: election information, indexed by election ID.
    """
    # Identify the unique election index.
    index = "election_id"

    # Exclude nested data structures.
    exclude = [
        "election_name",
        "district",
        "voting_methods",
        "third_party_verified"
    ]

    # Return a dataframe of election data.
    return (pd.DataFrame.from_records(results, index=index, exclude=exclude)
              .rename_axis(index="election_id"))


def tidy_verified(results):
    """Extract verification information from elections json.

    Args:
        results (list): Results from elections json.

    Returns:
        pandas.DataFrame: verification information, indexed by election ID.
    """
    # Extract district information.
    records = dict()
    for result in results:
        records[result["election_id"]] = result["third_party_verified"]

    # Make a districts dataframe.
    columns = {"is_verified": "verified", "date": "verified_date"}
    return (pd.DataFrame.from_dict(records, orient="index")
              .rename_axis(index="election_id")
              .rename(columns=columns))


def tidy_voting_methods(results):
    """Extract voting methods information from elections json.

    Args:
        results (list): Results from elections json.

    Returns:
        pandas.DataFrame: voting methods, indexed by election ID and method.
    """
    # Extract voting methods information.
    records = dict()
    for result in results:
        if result["voting_methods"]:
            for i, method in enumerate(result["voting_methods"]):
                flat_method = flatten_voting_method(method)
                records[(result["election_id"], i)] = flat_method

    # Make a voting methods dataframe.
    return (pd.DataFrame.from_dict(records, orient="index")
              .rename_axis(["election_id", "method_id"])
              .rename(columns=lambda x: f"method_{x}".replace("-", "_")))


def flatten_voting_method(method):
    """Flatten a voting method data structure.

    The incoming ``method`` data structure is as follows. At the time of
    writing, all elections have an identical structure. In practice. the None
    values could be different scalars. ::

      {
        "instructions": {
          "voting-id": {
            "en_US": None,
          },
        },
        "excuse-required":  None,
        "start": None,
        "end": None,
        "primary": None,
        "type": None,
      }

    This function flattens the US English voting ID instructions to become a top
    level item like all of the others.

    Args:
        method (dict): A nested voting method data structure.

    Returns:
        dict: A flat voting method data structure.
    """
    flat_method = {k: v for k, v in method.items() if k != "instructions"}
    flat_method["instructions"] = method["instructions"]["voting-id"]["en_US"]
    return flat_method


if __name__ == "__main__":

    # Paths to inputs and outputs.
    paths = {
        "raw": utils.PATHS["raw"] / "elections.json",
        "elections": utils.PATHS["processed"] / "elections.csv",
        "methods": utils.PATHS["processed"] / "voting_methods.csv",
    }

    # Read the raw JSON.
    with open(paths["raw"]) as f:
        raw = json.load(f)

    # Get just the election cases from the json.
    results = extract_results(raw)

    # Process election results into tables.
    elections = process_elections(results)
    methods = process_voting_methods(results)

    # Write the results.
    elections.to_csv(paths["elections"])
    methods.to_csv(paths["methods"])
