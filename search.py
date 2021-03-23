#!/usr/bin/python3
import re
import nltk
import sys
import getopt
import pickle
import math
import os
import string
import heapq
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


# Loads in the number of documents N
def load_num_docs(postings_file):
    # Number of documents stored as an integer in postings file
    f_postings = open(postings_file, "rb")
    num_docs = pickle.load(f_postings)  # Read in number of docs
    f_postings.close()

    return num_docs


# Loads in a postings list given the address offset in the postings file
def load_postings_list(postings_file, address):
    # Open our postings file
    f_postings = open(postings_file, "rb")

    # Read in PostingsList
    f_postings.seek(address, 0)  # Seek to start of PostingsList
    postings_list = pickle.load(f_postings)  # Read in PostingsList

    # Close our postings file
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

    # Initialize porter stemmer
    ps = nltk.stem.PorterStemmer()

    # Need to carry out stemming on query terms
    for query in all_queries:
        query = query.rstrip()  # Remove trailing newline characters
        query = query.lower()  # Convert text to lower case

        query = nltk.tokenize.WordPunctTokenizer().tokenize(query)  # Tokenize by word using WordPunct

        query = [term for term in query if term not in string.punctuation] # clean out isolated punctuations
        query = [term for term in query if term.strip() != ''] # clean out whitespaces            
        query_stemmed = [ps.stem(term) for term in query]  # Stem every term

        queries.append(query_stemmed)
        load_queries_bar.next()

    load_queries_bar.finish()

    # Close our queries file
    f_queries.close()

    # Return the queries array
    return queries


# Writes out the results
def write_results_to_disk(results: list, results_file):
    f_results = open(results_file, "w")

    # Write each result as a line
    for i, result in enumerate(results):
        output = ""
        for doc_id in result:
            output += str(doc_id) + " "

        if i < len(results) - 1:
            output = output.rstrip() + "\n"  # Remove trailing spaces and add newline
        else:
            output = output.rstrip()  # No need newline, just remove trailing spaces

        f_results.write(output)

    f_results.close()


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

    # Load in number of documents
    num_docs = load_num_docs(postings_file)
    print(num_docs)

    # Load in queries
    queries = load_queries(queries_file)

    print("Queries loaded. Now querying...")

    queries_progress_bar = Bar("Querying", max=len(queries))

    # Store results of each query
    results = []

    # For each query, conduct lnc.ltc ranking scheme with cosine normalization and take top 10 results
    for query in queries:
        # Create scores dictionary to store scores of each relevant document
        scores = {}

        # Count term frequencies for each term in query
        term_freqs = {}

        for term in query:
            if term in term_freqs:
                term_freqs[term] += 1
            else:
                term_freqs[term] = 1

        # Calculate w(t, q) for each term
        for term in query:
            # Term not found, skip it
            if term not in dictionary:
                continue

            # Load in PostingsList of term
            term_postings_list = load_postings_list(postings_file, dictionary[term])
            postings_list = term_postings_list["postings_list"]  # Actual postings list
            term_doc_freq = term_postings_list["doc_freq"]  # Document frequency of term

            # Get term frequency
            term_freq = 1 + math.log(term_freqs[term], 10)

            # Get inverted document frequency
            inv_doc_freq = math.log(num_docs / term_doc_freq, 10)

            # Calculate weight for term in query 
            weight_term_query = term_freq * inv_doc_freq

            # Iterate through postings list for the term and compute w(t, d)
            for posting in postings_list:
                # Calculate w(t, d). Again, we ignore idf. posting[1] is term_freq
                weight_term_doc = 1 + math.log(posting[1], 10)

                # Add to the document's scores the dot product of w(t, d) and w(t, q).
                # posting[0] is doc_id
                if posting[0] not in scores:
                    scores[posting[0]] = weight_term_doc * weight_term_query
                else:
                    scores[posting[0]] += weight_term_doc * weight_term_query

        # Normalize the scores using doc_length       
        scores_heap = []

        for doc_id in scores.keys():
            scores[doc_id] = scores[doc_id] / doc_lengths[doc_id]

            # heapq is by default a minheap
            # we push into the heap the negative of the score, to facilitate us forming a maxheap
            heapq.heappush(scores_heap, (-scores[doc_id], doc_id))
            # sorted_scores.append((doc_id, scores[doc_id]))

        # Store result of this query
        result = []

        # curr values we are checking against, in case of the same score for multiple documents
        curr_score = None
        curr_doc_id_list = []

        # pop the top of the heap. loop until we have >=10 elements in result. consider repeated scores as well
        while (len(result) < 10):
            # no more in the heap, exit while loop
            if len(scores_heap) == 0:
                break

            # curr[0] is the score, curr[1] is the doc_id
            # we pop the heap to get the maximum score. remember that it is represented by a negative number now
            curr = heapq.heappop(scores_heap)
            
            # we have no score to compare against at the moment
            if curr_score == None:
                curr_score = curr[0]
                curr_doc_id_list.append(curr[1])
            # there are scores to compare against
            else:
                # if it is a repeated score, append to list
                if curr[0] == curr_score:
                    curr_doc_id_list.append(curr[1])
                # if it is not a repeated score, push values into the 'result' container
                else:
                    # sort in increasing order of doc_ids for repeated scores and output 
                    curr_doc_id_list.sort()
                    for doc_id in curr_doc_id_list:
                        result.append(doc_id)
                    
                    # clear up and replace with new curr
                    curr_score = curr[0]
                    curr_doc_id_list = [curr[1]]
        
        # result might have more than 10 elements, just slice the first 10
        if len(result) > 10:
            result = result[:10]

        # Add to overall results
        results.append(result)

        # Update progress bar
        queries_progress_bar.next()

    # Write out results to disk
    write_results_to_disk(results, results_file)

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
