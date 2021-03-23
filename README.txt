This is the README file for A0228402N and A0230521Y's submission

== Python Version ==

We're using Python Version 3.8.5 for this assignment. We are operating on a Windows 10 environment
Standard python packages were used
	nltk		for nlp functions of tokenization and stemming
	string		for punctuation removal
	progress	for console loading bars
	pickle		for saving files as binary objects
	math		for math stuff
	heapq		for constructing heap in selecting top10 docs

== General Notes about this assignment ==

Running index.py
Please provide the path to the reuters data in the command prompt
>>>	python index.py -i <path_to_reuters_data_here> -d dictionary.txt -p postings.txt

Running search.py
Please provide the target input file for the queries, and the target output file for the output
>>>	python search.py -d dictionary.txt -p postings.txt -q queries.txt -o outputs.txt 

Additional notes 
1. Document processing
	We have opted for the following process and libraries for document processing
		stemmer: ps = nltk.stem.PorterStemmer() # porter stemmer
		sentences: nltk.sent_tokenize() # sentence tokenizer
		words: words = nltk.tokenize.WordPunctTokenizer().tokenize(sentence) # Tokenize by word using WordPunct
			words = [w for w in words if w not in string.punctuation] # clean out isolated punctuations
			words = [w for w in words if w.strip() != ''] # clean out whitespaces            
			words_stemmed = [ps.stem(w) for w in words]  # Stem every word
	Our document processing did not remove numbers

2. Reading postings.txt
	We have noted the requirement to read postings.txt through pointer seeks instead of loading the whole file into memory

3. doc_lengths.txt
	We have created an auxilliary file through index.py that contains the doc_lengths for all the documents
	This is utilised in search.py when we run our normalization step in score calculations

4. Cosine score
	We have followed the algorithms outlined in lecture slides for week 7 and week 8 of CS3245
	In particular, our cosine score computation followed the redux version found on slide 5, week 8 lecture slides

5. heapq and maxheap
	Our heap structure was created through the library heapq
	It has been noted that heapq defaults to create a minimum heap, not a maximum heap like we want
	We have employed a very simple workaround, which is to convert the scores into its negative version before pushing onto the heap
	In this manner, our "minheap" has become a "maxheap". Therefore we can continue as per normal and popping the top of the heap functinos as expected of a maxheap
	Indeed, this is the standard way to implement maxheap with the heapq library

6. top 10 results
	We have taken care to follow the assignment requirements
	For top results, if the score is identical, the doc_ids will be sorted in increasing order
	We will obtain the top results by popping from the heap
	Note that more than 10 results may be popped off the heap, in cases of identical scores. 
	We perform a simple array slice to return only 10


== Files included with this submission ==

index.py		implementation of index construction. also creates doc_lengths.txt
search.py		implementation of the freetext search function
dictionary.txt		the corpus, obtained from parsing reuters data
postings.txt		the postings file, pointed to by dictionary entries
README.txt		this file you are reading
dictionary.txt		auxilliary file used to support cosine score calculation in search.py

== Statement of individual work ==

Please put a "x" (without the double quotes) into the bracket of the appropriate statement.

[x] We, A0228402N and A0230521Y, certify that we have followed the CS 3245 Information
Retrieval class guidelines for homework assignments.  In particular, we
expressly vow that we have followed the Facebook rule in discussing
with others in doing the assignment and did not take notes (digital or
printed) from the discussions.  

[ ] We, A0228402N and A0230521Y did not follow the class rules regarding homework
assignment, because of the following reason:

We suggest that we should be graded as follows:

Normal

== References ==

Tokenizing - https://pythonspot.com/tokenizing-words-and-sentences-with-nltk/
Stemming - https://www.geeksforgeeks.org/python-stemming-words-with-nltk/
Heap - https://stackoverflow.com/questions/3954530/how-to-make-heapq-evaluate-the-heap-off-of-a-specific-attribute
       https://stackoverflow.com/questions/2501457/what-do-i-use-for-a-max-heap-implementation-in-python
CS3245 lecture notes
Homework 2