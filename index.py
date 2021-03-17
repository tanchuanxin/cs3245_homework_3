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


# Create a linked list node containing docID and term frequency within the document
class ListNode:
    def __init__(self, doc_id=None, term_freq=None, skip_ptr=None):
        self.doc_id = doc_id
        self.term_freq = term_freq
        self.skip_ptr = skip_ptr
        self.next = None


# Create a linked list class with the total length of the postings list (doc_freq)
class PostingsList:
    def __init__(self):
        self.doc_freq = None
        self.head = None  # Head of linked list
        self.end = None  # Last node in linked list

    # Appends a new node to the end of the linked list
    def append(self, new_node: ListNode):
        # If nothing in linked list, add to head
        if self.end == None:
            self.head = new_node
            self.end = new_node
            self.doc_freq = 1
        else:
            self.end.next = new_node
            self.end = new_node  # Change last node in linked list
            self.doc_freq += 1  # Increment document frequency for this linked list

    # Creates skip pointers within a completed postings list
    def create_skip_ptrs(self):
        skip_ptrs_num = int(math.sqrt(self.doc_freq))
        skip_ptrs_interval = self.doc_freq // skip_ptrs_num

        # If it's the only element in the postings list, we don't need skip pointers
        if self.doc_freq <= 1:
            skip_ptrs_num = 0

        # Add skip pointers into linked list
        skip_ptrs_added = 0

        # Interval between prev and curr to see if we should add a skip pointer
        interval = 0
        curr_index = 0  # Checks which node we are at
        prev_index = 0  # Tracks which node we are inserting the skip pointer for

        curr = self.head
        prev = curr

        while curr != None:
            # If added all skip pointers already, just end function
            if skip_ptrs_added >= skip_ptrs_num:
                break

            # Add new skip pointer if interval matches or we are at the end of the linked list
            if interval >= skip_ptrs_interval or curr == self.end:
                prev.skip_ptr = curr  # Set prev's skip pointer to curr
                prev = curr
                prev_index = curr_index  # Update prev's new index to curr
                skip_ptrs_added += 1
                interval = 0  # Reset

            # If we are not adding a skip pointer, simply increment curr
            curr = curr.next
            curr_index += 1

            # Update interval
            interval = curr_index - prev_index

    # Prints out a postings list for debugging
    def display(self):
        curr = self.head
        while curr.next != None:
            print(
                "{}, {}, ({})".format(curr.doc_id, curr.term_freq, curr.skip_ptr),
                end=" | ",
            )
            curr = curr.next
        if curr != None:
            print("{}, {}, ({})".format(curr.doc_id, curr.term_freq, curr.skip_ptr))
        print("=============================")


# Writes out the total number of documents in the collection to the postings file
# This is basically N, to compute inverse document frequency
def write_collection_size_to_disk(collection_size: int, out_postings):
    # Open our postings file
    f_postings = open(os.path.join(os.path.dirname(__file__), out_postings), "wb")

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
    f_postings = open(os.path.join(os.path.dirname(__file__), out_postings), "a+b")

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
    f_dict = open(os.path.join(os.path.dirname(__file__), out_dict), "wb")

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

        doc_length = 0  # Track number of words in this document

        for sentence in sentences:
            words = nltk.word_tokenize(sentence)  # Tokenize by word
            words_stemmed = [ps.stem(w) for w in words]  # Stem every word

            for word in words_stemmed:
                # Update document length
                doc_length += 1

                # If new term, add term to dictionary and initialize new postings list for that term
                if word not in dictionary:
                    dictionary[word] = PostingsList()
                    new_node = ListNode(doc_id=doc_id, term_freq=1)
                    dictionary[word].append(new_node)
                # If term in dictionary, check if document for that term is already inside
                else:
                    # If doc_id already exists in postings list, simply increment term frequency in doc
                    if dictionary[word].end.doc_id == doc_id:
                        dictionary[word].end.term_freq += 1
                    # Else, create new document in postings list and set term frequency to 1
                    else:
                        new_node = ListNode(doc_id=doc_id, term_freq=1)
                        dictionary[word].append(new_node)

        # Update document length in doc_length dictionary
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
        # Add skip pointers for each of the terms' posting lists
        dictionary[term].create_skip_ptrs()

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
