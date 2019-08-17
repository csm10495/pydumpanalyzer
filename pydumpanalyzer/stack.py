class Stack(object):
    def __init__(self, frames, threadId):
        self.frames = frames
        self.threadId = threadId

    def __repr__(self):
        return "<Stack - %d frames - Id: %s>" % (len(self.frames), self.threadId)

    def __str__(self):
        retStr = "Stack for thread %s\n" % self.threadId
        for f in self.frames:
            retStr += '  ' + str(f).replace('\n', '\n  ').rstrip(' ')
        return retStr