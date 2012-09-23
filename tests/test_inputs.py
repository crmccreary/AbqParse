import unittest
import sys, os
import re

sys.path.insert(0,os.path.abspath(os.path.join('..','src')))

from AbqParse import abaqus_parser, abaqus_lexer

class Inputs(unittest.TestCase):
    def test_1(self):
        f = open(os.path.join('data','mmxmn.inp'),'rb')
        buf = f.read()
        f.close()
        parser = abaqus_parser.AbaqusParser(lex_optimize=False, yacc_debug=False, yacc_optimize=False)
        t = parser.parse(buf, 'mmxmn.inp', debuglevel=0)

    def test_2(self):
        f = open(os.path.join('data','test_2.inp'),'rb')
        buf = f.read()
        f.close()
        parser = abaqus_parser.AbaqusParser(lex_optimize=False, yacc_debug=False, yacc_optimize=False)
        t = parser.parse(buf, 'test_2.inp', debuglevel=0)

def suite():
    suite1 = unittest.makeSuite(Inputs)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Inputs)
    unittest.TextTestRunner(verbosity=2).run(suite)
