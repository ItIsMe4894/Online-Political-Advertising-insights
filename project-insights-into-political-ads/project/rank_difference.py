#!/usr/bin/python
import sys, getopt

class RankDifference:
    """
    Given two input files of ranked terms, the class computes and outputs terms with least/largest term differences for both sets.
    """
    def __init__(self, fileA, fileB, debug=True, limit=20, listOnly=False, reverse=False):
        # store params
        self.fileA = fileA
        self.fileB = fileB
        self.debug = debug
        self.limit = limit
        self.listOnly = listOnly
        self.reverse = reverse
        # init variables
        self.listA = list()
        self.listAFrequencies = list()
        self.listB = list()
        self.listBFrequencies = list()
        # perform initialization
        self.readLists()

    def readLists(self):
        """
        Read in both lists of ranked terms from the given input files.
        """
        # read fileA
        self.listA = [line.split(' --- ')[0].rstrip('\n') for line in open(self.fileA, encoding='utf-8')]
        self.listAFrequencies = [line.split(' --- ')[1].rstrip('\n') for line in open(self.fileA, encoding='utf-8')]

        # read fileB
        self.listB = [line.split(' --- ')[0].rstrip('\n') for line in open(self.fileB, encoding='utf-8')]
        self.listBFrequencies = [line.split(' --- ')[1].rstrip('\n') for line in open(self.fileB, encoding='utf-8')]

    def computeRankDifference(self):
        sizeA = len(self.listA)
        sizeB = len(self.listB)
        # list of all terms
        dictionary = list(set(self.listA) | set(self.listB))
        differences = list()
        for term in dictionary:
            try:
                rankA = self.listA.index(term) + 1
            except ValueError:
                rankA = sizeA # sizeA + 1 instead?
            try:
                rankB = self.listB.index(term)
            except ValueError:
                rankB = sizeB
            try:
                freqA = self.listAFrequencies[rankA]
            except IndexError:
                freqA = 0
            try:
                freqB = self.listBFrequencies[rankB]
            except IndexError:
                freqB = 0
            rankDiff = 1.0*rankA/sizeA - 1.0*rankB/sizeB # in [-1,1]
            differences.append((term, rankDiff, freqA, freqB))
        if not listOnly:
            print("\nDescriptive terms for {}:".format(self.fileA))
            if self.reverse:
                print(sorted(differences, key=lambda i: i[1] if i[1] <= 0 else -1, reverse=True)[0:self.limit])
            else:
                print(sorted(differences, key=lambda i: i[1])[0:self.limit])
            print("\nDescriptive terms for {}:".format(self.fileB))
            if self.reverse:
                print(sorted(differences, key=lambda i: i[1] if i[1] >= 0 else 1)[0:self.limit])
            else:
                print(sorted(differences, key=lambda i: i[1], reverse=True)[0:self.limit])
        else:
            for item in sorted(differences, key=lambda i: i[1])[0:self.limit]:
                print(item[0])

if __name__ == "__main__":
    # parse cmdline arguments
    fileA = ''
    fileB = ''
    listOnly = False
    numTerms = 20
    errorMsg = 'rank_difference.py -a <fileA> -b <fileB> [-l] [-n <numTerms>]'
    reverse = False
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args,"ha:b:ln:r",["fileA=","fileB=","listOnly","numTerms"])
    except getopt.GetoptError:
        print(errorMsg)
        sys.exit(2)
   
    for opt, arg in opts:
        if opt == '-h':
            print(errorMsg)
            sys.exit()
        elif opt in ("-a", "--fileA"):
            fileA = arg
        elif opt in ("-b", "--fileB"):
            fileB = arg
        elif opt in ("-l", "--listOnly"): # output only the list of descriptive terms for fileA 
            listOnly = True
        elif opt in ("-n", "--numTerms"):
            numTerms = int(arg)
        elif opt in ("-r"):
            reverse = True

    if fileA == '' or fileB == '':
        print(errorMsg)
        sys.exit()

    instance = RankDifference(fileA=fileA, fileB=fileB, listOnly=listOnly, limit=numTerms, reverse=reverse)
    instance.computeRankDifference()
