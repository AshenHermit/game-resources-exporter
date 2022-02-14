from io import StringIO
import os.path, sys, types

import xml.etree.ElementTree as ET

__version__ = '0.0.1'
__all__ = ['path', 'xml', 'xpath']

# XML support
#
class HandyXmlWrapper:
    """ This class wraps an XML element to give it convenient
        attribute access.
        <element attr1='foo' attr2='bar'>
            <child attr3='baz' />
        </element>
        element.attr1 == 'foo'
        element.child.attr3 == 'baz'
    """
    def __init__(self, node:ET.Element):
        self.node = node

    def __getattr__(self, attr):
        if hasattr(self.node, attr):
            return getattr(self.node, attr)

        if attr[0:2] != '__':        
            #print "Looking for "+attr, self.node, dir(self.node)
            if hasattr(self.node, '__getitem__'):
                if attr in self.node.attrib:
                    return self.node.attrib[attr]
            else:
                raise Exception("Can't look for attributes on node?")

            els = None
            if hasattr(self.node, 'childNodes'):
                els = []
                for e in self.node:
                    if e.localName == attr:
                        els.append(e)
            else:
                raise Exception("Can't look for children on node?")
            if els:
                # Save the attribute, since this could be a hasattr
                # that will be followed by getattr
                els = map(HandyXmlWrapper, els)
                if type(self.node) is ET.Element:
                    setattr(self.node, attr, els)
                return els

        raise AttributeError("Couldn't find %s for node" % attr)

# The path on which we look for XML files.
path = ['.']

def _findFile(filename):
    """ Find files on path.
    """
    ret = None
    searchPath = path
    # If cog is in use, then use its path as well.
    if 'cog' in sys.modules:
        searchPath += sys.modules['cog'].path
    # Search the directories on the path.
    for dir in searchPath:
        p = os.path.join(dir, filename)
        if os.path.exists(p):
            ret = os.path.abspath(p)
    return ret

# A dictionary from full file paths to parsed XML.
_xmlcache = {}

def xml(xmlin):
    """ Parse some XML.
        Argument xmlin can be a string, the filename of some XML;
        or an open file, from which xml is read.
        The return value is the parsed XML as DOM nodes.
    """

    filename = None

    # A string argument is a file name.
    if type(xmlin) is str:
        filename = _findFile(xmlin)
        if not filename:
            raise Exception("Couldn't find XML to parse: %s" % xmlin)

    if filename:
        if filename in _xmlcache:
            return _xmlcache[filename]
        xmlin = open(filename)
    
    xmldata = xmlin.read()


    doc = ET.parse(StringIO(xmldata))

    parsedxml = HandyXmlWrapper(doc.getroot())

    if filename:
        _xmlcache[filename] = parsedxml

    return parsedxml

def xpath(input, expr):
    """ Evaluate the xpath expression against the input XML.
    """
    if isinstance(input, str) or hasattr(input, 'read'):
        # If input is a filename or an open file, then parse the XML.
        input = xml(input)
    return map(HandyXmlWrapper, input.node.findall(expr))