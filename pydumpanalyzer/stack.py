''' this contains the Stack class '''

class Stack(object):
    ''' This class represents a stack for a given thread. It includes associated frames. '''
    def __init__(self, frames, threadId):
        ''' Initializer takes in a list of Frame objects and a thread id '''
        self.frames = frames
        self.threadId = threadId

    def __repr__(self):
        ''' representation function '''
        return "<Stack - %d frames - Id: %s>" % (len(self.frames), self.threadId)

    def __str__(self):
        ''' to string function '''
        retStr = "Stack for thread %s\n" % self.threadId
        for f in self.frames:
            retStr += '  ' + str(f).replace('\n', '\n  ').rstrip(' ')
        return retStr