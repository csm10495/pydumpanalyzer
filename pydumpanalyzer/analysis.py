''' this contains the Analysis class '''

class Analysis(object):
    ''' This object is used to represent an analysis that has been done by a given debugger '''
    def __init__(self, dumpFileName, stacks, rawAnalysisText):
        ''' initializer that takes in thename of the dump file, list of stacks, and the raw analysis text output '''
        if not isinstance(stacks, (list, tuple)):
            stacks = [stacks]

        self.dumpFileName = dumpFileName
        self.stacks = stacks
        self.rawAnalysisText = rawAnalysisText

    def __repr__(self):
        ''' representation function '''
        return '<Analysis for %s>' % self.dumpFileName

    def __str__(self):
        ''' to string function '''
        retStr = 'Analysis for %s:\n' % self.dumpFileName
        for s in self.stacks:
            retStr += '  ' + str(s).replace('\n', '\n  ').rstrip(' ')

        retStr += "Raw Native Analysis Text:\n"
        retStr += '  ' + self.rawAnalysisText.replace('\n', '\n  ').rstrip(' ')
        return retStr

