class Variable(object):
    def __init__(self, typ, name, value):
        self.type = typ
        self.name = name
        self.value = value

    def __repr__(self):
        return "<%s of %s: %s>" % (self.name, self.type, self.value)

    def __str__(self):
        return '%s %s = %s' % (self.type, self.name, self.value)