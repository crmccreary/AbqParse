import unittest
import sys, os
import re

sys.path.insert(0,os.path.abspath(os.path.join('..','src')))

from AbqParse import abaqus_parser, abaqus_lexer

class Snippets(unittest.TestCase):
    def test_1(self):
        buf = ''' 
        *elset,elset=foo
        1,
        2,
        3,
        '''
        parser = abaqus_parser.AbaqusParser(lex_optimize=False, yacc_debug=False, yacc_optimize=False)
        t = parser.parse(buf, 'test_1_buffer', debuglevel=0)
        self.assertEqual(len(t),1)
        self.assertEqual(t[0].keyword,'elset')
        self.assertEqual(len(t[0].params),1)
        self.assertEqual(t[0].params[0].name,'elset')
        self.assertEqual(t[0].params[0].value,'foo')
        self.assertEqual(len(t[0].data),3)
        self.assertEqual(int(t[0].data[0][0]),1)
        self.assertEqual(int(t[0].data[1][0]),2)
        self.assertEqual(int(t[0].data[2][0]),3)

    def test_2(self):
        buf = ''' 
        *solid section,elset=box,material=T95
        1.0
        *solid section,elset=pin,material=T95
        1.0
        '''
        parser = abaqus_parser.AbaqusParser(lex_optimize=False, yacc_debug=False, yacc_optimize=False)
        t = parser.parse(buf, 'test_2_buffer', debuglevel=0)
        self.assertEqual(len(t),2)
        self.assertEqual(t[0].keyword,'solid section')
        self.assertEqual(len(t[0].params),2)
        self.assertEqual(t[0].params[0].name,'elset')
        self.assertEqual(t[0].params[0].value,'box')
        self.assertEqual(t[0].params[1].name,'material')
        self.assertEqual(t[0].params[1].value,'T95')
        self.assertEqual(len(t[0].data),1)
        self.assertAlmostEqual(float(t[0].data[0][0]),1.0)
        self.assertEqual(len(t[1].params),2)
        self.assertEqual(t[1].params[0].name,'elset')
        self.assertEqual(t[1].params[0].value,'pin')
        self.assertEqual(t[1].params[1].name,'material')
        self.assertEqual(t[1].params[1].value,'T95')
        self.assertEqual(len(t[1].data),1)
        self.assertAlmostEqual(float(t[1].data[0][0]),1.0)

    def test_3(self):
        buf = ''' 
        *include,input=materials.inp
        ***********************************
        *end
        '''
        parser = abaqus_parser.AbaqusParser(lex_optimize=False, yacc_debug=False, yacc_optimize=False)
        t = parser.parse(buf, 'test_2_buffer', debuglevel=0)
        self.assertEqual(len(t),2)

def suite():
    suite1 = unittest.makeSuite(Snippets)
    return unittest.TestSuite([suite1])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(Snippets)
    unittest.TextTestRunner(verbosity=2).run(suite)
