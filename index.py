#!/usr/bin/python3
import re
import nltk
import os
import sys
import getopt
import pickle


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


def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print("indexing...")

    # Read in documents to index
    doc_ids = os.listdir(in_dir)  # Read in paths of all documents in the in_dir
    doc_ids = [int(doc_id) for doc_id in doc_ids]
    doc_ids.sort()

    # Save all the document IDs into its own file for NOT queries in search
    f_doc_ids = open(os.path.join(os.path.dirname(__file__), "doc_ids"), "wb")

    # Save all docIDs out to a doc_ids file
    pickle.dump(doc_ids, f_doc_ids)

    # Close the doc_ids file
    f_doc_ids.close()

    # Create a dictionary of terms
    dictionary = {}

    # Initialize porter stemmer
    ps = nltk.stem.PorterStemmer()

    # Process every document and create a dictionary of posting lists
    for doc_id in doc_ids[:100]:  # TODO: REMOVE THE LIMIT
        f = open(os.path.join(in_dir, str(doc_id)), "r")  # Open the document file
        text = f.read()  # Read the document in fulltext
        text = text.lower()  # Convert text to lower case
        sentences = nltk.sent_tokenize(text)  # Tokenize by sentence

        for sentence in sentences:
            words = nltk.word_tokenize(sentence)  # Tokenize by word
            words_stemmed = [ps.stem(w) for w in words]  # Stem every word

            for word in words_stemmed:
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

        # Close file
        f.close()

    # TODO: TEST PRINT FOR POSTINGS LISTS
    # for key in dictionary.keys():
    #     print("{}:".format(key))
    #     curr = dictionary[key].head
    #     while curr != None:
    #         print(curr.doc_id, curr.term_freq, end=" | ")
    #         curr = curr.next
    #     print()


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
