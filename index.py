#!/usr/bin/python3
import re
import nltk
import os
import sys
import getopt
import pickle
import math

from progress.bar import Bar
from progress.spinner import Spinner


def usage():
    print(
        "usage: "
        + sys.argv[0]
        + " -i directory-of-documents -d dictionary-file -p postings-file"
    )


# Create a list node containing docID and term frequency within the document
class Posting:
    def __init__(self, doc_id=None, term_freq=None):
        self.doc_id = doc_id
        self.term_freq = term_freq


# Create a postings list class with the total length of the postings list (doc_freq)
class PostingsList:
    def __init__(self):
        self.doc_freq = 0
        self.postings_list = []  # Stores the postings for this term

    # Appends a new node to the end of the linked list
    def append(self, new_posting: Posting):
        # Add to postings list
        self.postings_list.append(new_posting)
        self.doc_freq += 1  # Increment document frequency for this linked list

    # Prints out a postings list for debugging
    def display(self):
        if len(self.postings_list) > 0:
            for posting in self.postings_list[:-1]:
                print("{}, {}".format(posting.doc_id, posting.term_freq), end=" | ")
            print(
                "{}, {}".format(
                    self.postings_list[-1].doc_id, self.postings_list[-1].term_freq
                )
            )
        else:
            print("Empty postings list!")
        print("========================")


# Writes out the total number of documents in the collection to the postings file
# This is basically N, to compute inverse document frequency
def write_collection_size_to_disk(collection_size: int, out_postings):
    # Open our postings file
    f_postings = open(out_postings, "wb")

    # Writes out PostingsList for this term to postings file
    pickle.dump(collection_size, f_postings)

    # Close our postings file
    f_postings.close()


# Writes out the length of each document as a dictionary to a file
def write_doc_lengths_to_disk(doc_lengths: dict):
    # Open our document lengths file
    f_doc_lengths = open(
        os.path.join(os.path.dirname(__file__), "doc_lengths.txt"), "wb"
    )

    # Write out document lengths dictionary to the document lengths file
    pickle.dump(doc_lengths, f_doc_lengths)

    # Close the file
    f_doc_lengths.close()


# Takes in a PostingsList for a term and writes it out to our postings file
# Returns an address to the PostingsList on disk
def write_postings_list_to_disk(postings_list: PostingsList, out_postings):
    # Open our postings file
    f_postings = open(out_postings, "a+b")

    # Get the byte offset of the final position in our postings file on disk
    # This will be where the PostingsList is appended to
    f_postings.seek(0, 2)  # Bring the pointer to the very end of the postings file
    pointer = f_postings.tell()

    # Writes out PostingsList for this term to postings file
    pickle.dump(postings_list, f_postings)

    # Close our postings file
    f_postings.close()

    # Return address of PostingsList we just wrote out
    return pointer


# Writes our the term dictionary {term: Address of PostingsList for that term} to disk
def write_dictionary_to_disk(term_dict: dict, out_dict):
    # Open our dictionary file
    f_dict = open(out_dict, "wb")

    # Writes out the term dictionary to dictionary file
    pickle.dump(term_dict, f_dict)

    # Close our dictionary file
    f_dict.close()


def build_index(in_dir, out_dict, out_postings):
    """
    Build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print("Indexing...")

    # Read in documents to index
    file_doc_ids = os.listdir(in_dir)  # Read in paths of all documents in the in_dir

    load_documents_bar = Bar("Loading in documents", max=len(file_doc_ids))

    doc_ids = []
    for doc_id in file_doc_ids:
        doc_ids.append(int(doc_id))
        load_documents_bar.next()

    doc_ids.sort()
    load_documents_bar.finish()

    print("Documents loaded. Writing out total collection size to disk...")

    # Write out collection size (number of documents) to disk
    write_collection_size_to_disk(len(doc_ids), out_postings)

    print("Total collection size is {}.".format(len(doc_ids)))

    # Initialize porter stemmer
    ps = nltk.stem.PorterStemmer()

    print("Stemming terms and tracking document lengths...")

    # Track progress while indexing
    processing_bar = Bar("Processing documents", max=len(doc_ids))

    # Create a dictionary of terms and another dictionary for document lengths
    dictionary = {}
    doc_lengths = {}

    # Process every document and create a dictionary of posting lists
    for doc_id in doc_ids:
        f = open(os.path.join(in_dir, str(doc_id)), "r")  # Open the document file

        text = f.read()  # Read the document in fulltext
        text = text.lower()  # Convert text to lower case
        sentences = nltk.sent_tokenize(text)  # Tokenize by sentence

        terms = []  # Keep track of unique terms in document

        for sentence in sentences:
            words = nltk.word_tokenize(sentence)  # Tokenize by word
            words_stemmed = [ps.stem(w) for w in words]  # Stem every word

            for word in words_stemmed:
                # Track unique terms
                terms.append(word)

                # If new term, add term to dictionary and initialize new postings list for that term
                if word not in dictionary:
                    dictionary[word] = PostingsList()
                    new_posting = Posting(doc_id=doc_id, term_freq=1)
                    dictionary[word].append(new_posting)
                # If term in dictionary, check if document for that term is already inside
                else:
                    # If doc_id already exists in postings list, simply increment term frequency in doc
                    if dictionary[word].postings_list[-1].doc_id == doc_id:
                        dictionary[word].postings_list[-1].term_freq += 1
                    # Else, create new document in postings list and set term frequency to 1
                    else:
                        new_posting = Posting(doc_id=doc_id, term_freq=1)
                        dictionary[word].append(new_posting)

        # Make set only unique terms
        terms = list(set(terms))

        # Calculate document length (sqrt of all weights squared)
        doc_length = 0
        for term in terms:
            # If term appears in doc, calculate its weight in the document W(t,d)
            if dictionary[term].postings_list[-1].doc_id == doc_id:
                term_weight_in_doc = 0
                if dictionary[term].postings_list[-1].term_freq > 0:
                    # Take the log frequecy weight of term t in doc
                    # Note that we ignore inverse document frequency for documents
                    term_weight_in_dic = 1 + math.log(
                        dictionary[term].postings_list[-1].term_freq, 10
                    )

                # Add term weight in document squared to total document length
                doc_length += term_weight_in_doc ** 2

        # Take sqrt of doc_length for final doc length
        doc_length = math.sqrt(doc_length)

        # Add final doc_length to doc_lengths dictionary
        doc_lengths[doc_id] = doc_length

        # Close file and update progress bar
        f.close()
        processing_bar.next()

    # Update progress bar
    processing_bar.finish()
    print("Pre-processing complete. Writing document lengths to disk...")

    # Save doc_lengths to disk
    write_doc_lengths_to_disk(doc_lengths)

    print("{} document lengths written to disk.".format(len(doc_ids)))

    # Create dictionary of K:V {term: Address to PostingsList of that term}
    term_dict = {}

    # Track progress while indexing
    print("Indexing terms and saving each postings list to disk...")
    indexing_bar = Bar("Indexing terms", max=len(dictionary.keys()))

    # For each term, split into term_dict and PostingsList, and write out to their respective files
    for term in dictionary.keys():
        # Write PostingsList for each term out to disk and get its address
        ptr = write_postings_list_to_disk(dictionary[term], out_postings)

        # Update term_dict with the address of the PostingsList for that term
        term_dict[term] = ptr

        # Update progress bar
        indexing_bar.next()

    # Update progress bar
    indexing_bar.finish()
    print("Posting lists saved to disk.")

    # Track progress while indexing
    print("Saving term dictionary to disk...")

    # Now the term_dict has the pointers to each terms' PostingsList
    # Write out the dictionary to the dictionary file on disk
    write_dictionary_to_disk(term_dict, out_dict)

    print("Indexing complete.")


input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], "i:d:p:")
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == "-i":  # input directory
        input_directory = a
    elif o == "-d":  # dictionary file
        output_file_dictionary = a
    elif o == "-p":  # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if (
    input_directory == None
    or output_file_postings == None
    or output_file_dictionary == None
):
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
