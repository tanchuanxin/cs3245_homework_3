#!/usr/bin/python3
import re
import nltk
import sys
import getopt
import pickle
import math
import os

from progress.bar import Bar


def usage():
    print(
        "usage: "
        + sys.argv[0]
        + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"
    )


# Loads in the term dictionary from file
def load_dictionary(dict_file):
    # Open our dictionary file
    f_dict = open(dict_file, "rb")

    # Read in dictionary into object
    term_dict = pickle.load(f_dict)

    # Close our dictionary file
    f_dict.close()

    # Return term dictionary
    return term_dict


# Loads in a dictionary of document lengths
def load_doc_lengths():
    # Open our doc lengths file
    f_doc_lengths = open(
        os.path.join(os.path.dirname(__file__), "doc_lengths.txt"), "rb"
    )

    # Read in dictionary into object
    doc_lengths = pickle.load(f_doc_lengths)

    # Close our doc lengths file
    f_doc_lengths.close()

    # Return doc lengths dictionary
    return doc_lengths


# Loads in a PostingsList given the address offset in the postings file
def load_postings_list(postings_file, address):
    # Open our doc lengths file
    f_postings = open(postings_file, "rb")

    # Read in PostingsList
    f_postings.seek(address, 0)  # Seek to start of PostingsList
    postings_list = pickle.load(f_postings)  # Read in PostingsList

    # Close our doc lengths file
    f_postings.close()

    # Return the postings list for that term
    return postings_list


# Returns an array of queries (each element is a query)
def load_queries(queries_file):
    # Open our queries file
    f_queries = open(queries_file, "r")

    # Read all queries in
    all_queries = f_queries.readlines()

    load_queries_bar = Bar("Loading in queries", max=len(all_queries))

    # Read in queries into an array
    queries = []
    for query in all_queries:
        queries.append(query.rstrip())  # Remove trailing newline characters
        load_queries_bar.next()

    load_queries_bar.finish()

    # Close our queries file
    f_queries.close()

    # Return the queries array
    return queries


def run_search(dict_file, postings_file, queries_file, results_file):
    """
    Using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print("Running search on the queries...")

    # Load in term dictionary
    dictionary = load_dictionary(dict_file)

    print("Term dictionary loaded. Loading in document lengths...")

    # Load in document lengths
    doc_lengths = load_doc_lengths()

    print("Document lengths loaded.")

    # Load in queries
    queries = load_queries(queries_file)

    print("Queries loaded. Now querying...")

    queries_progress_bar = Bar("Querying", max=len(queries))

    # For each query, conduct lnc.ltc ranking scheme with cosine normalization and take top 10 results
    for query in queries:
        # Create scores dictionary to store scores of each relevant document
        scores = {}

        # Get terms in each query
        query = query.split()

        for term in query:
            

        # Update progress bar
        queries_progress_bar.next()

    queries_progress_bar.finish()

    print("Querying complete. Find your results at `{}`.".format(results_file))


dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "d:p:q:o:")
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == "-d":
        dictionary_file = a
    elif o == "-p":
        postings_file = a
    elif o == "-q":
        file_of_queries = a
    elif o == "-o":
        file_of_output = a
    else:
        assert False, "unhandled option"

if (
    dictionary_file == None
    or postings_file == None
    or file_of_queries == None
    or file_of_output == None
):
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
