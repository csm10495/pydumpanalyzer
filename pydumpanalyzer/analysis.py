from stack import Stack

class Analysis(object):
    def __init__(self, dumpFileName, stacks, rawAnalysisText):
        if isinstance(stacks, Stack):
            stacks = [stacks]

        self.dumpFileName = dumpFileName
        self.stacks = stacks
        self.rawAnalysisText = rawAnalysisText

    def __str__(self):
        retStr = 'Analysis for %s:\n' % self.dumpFileName
        for s in self.stacks:
            retStr += '  ' + str(s).replace('\n', '\n  ').rstrip(' ')

        retStr += "Raw Native Analysis Text:\n"
        retStr += '  ' + self.rawAnalysisText.replace('\n', '\n  ').rstrip(' ')
        return retStr

