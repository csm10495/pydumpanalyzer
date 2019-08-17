import os

class Frame(object):
    def __init__(self, module, index, function=None, sourceFile=None, line=None, variables=None, warningAboutCorrectness=False):
        self.module = module.strip()
        self.index = int(index)
        self.function = function.strip() if function is not None else None
        self.sourceFile = sourceFile.strip() if sourceFile is not None else None
        self.line = int(line) if sourceFile is not None else None
        self.variables = variables

        # WARNING: Stack unwind information not available. Following frames may be wrong.
        #  would make this True
        self.warningAboutCorrectness = warningAboutCorrectness

    def __repr__(self):
        if self.sourceFile:
            return "<Frame %s - %s:%s:%s>" % (self.index, os.path.basename(self.sourceFile), self.function, self.line)

        return "<Frame %s - %s>" % (self.index, self.module)

    def __str__(self):
        retStr = "Index: %d\n" % self.index
        if self.warningAboutCorrectness:
            retStr += '  Warning: Frame may be incomplete due to stack unwind info missing.\n'

        if self.sourceFile:
            retStr += '  Location: %s:%s:%s:%s\n' % (self.module, os.path.basename(self.sourceFile), self.function, self.line)
        else:
            retStr += '  Location: %s\n' % (self.module)

        if self.variables:
            retStr += "  Locals:\n"
            for v in self.variables:
                retStr += "    " + str(v) + "\n"

        return retStr