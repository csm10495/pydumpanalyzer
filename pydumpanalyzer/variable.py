''' this contains the variable class '''

class Variable(object):
    ''' the variable class is used to represent a single variable within a stack frame '''
    def __init__(self, typ, name, value):
        ''' initializer that takes in the type, name, value, for the variable.
            Likely best to use a str for value '''
        self.type = typ
        self.name = name
        self.value = value

    def __eq__(self, other):
        ''' returns True if self == other '''
        return self.type == other.type and self.name == other.name and self.value == other.value

    def __repr__(self):
        ''' representation function '''
        return "<%s of %s: %s>" % (self.name, self.type, self.value)

    def __str__(self):
        ''' to string function '''
        return '%s %s = %s' % (self.type, self.name, self.value)