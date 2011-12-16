#-----------------------------------------------------------------
# pycparser: c_parser.py
#
# AbaqusParser class: Parser and AST builder for the C language
#
# Copyright (C) 2008-2011, Eli Bendersky
# License: BSD
#-----------------------------------------------------------------
import re

import ply.yacc

from abaqus_lexer import AbaqusLexer
from plyparser import PLYParser, Coord, ParseError


class AbaqusParser(PLYParser):    
    def __init__(
            self, 
            lex_optimize=True,
            lextab='pycparser.lextab',
            yacc_optimize=True,
            yacctab='pycparser.yacctab',
            yacc_debug=False):
        """ Create a new AbaqusParser.
        
            Some arguments for controlling the debug/optimization
            level of the parser are provided. The defaults are 
            tuned for release/performance mode. 
            The simple rules for using them are:
            *) When tweaking AbaqusParser/CLexer, set these to False
            *) When releasing a stable parser, set to True
            
            lex_optimize:
                Set to False when you're modifying the lexer.
                Otherwise, changes in the lexer won't be used, if
                some lextab.py file exists.
                When releasing with a stable lexer, set to True
                to save the re-generation of the lexer table on 
                each run.
            
            lextab:
                Points to the lex table that's used for optimized
                mode. Only if you're modifying the lexer and want
                some tests to avoid re-generating the table, make 
                this point to a local lex table file (that's been
                earlier generated with lex_optimize=True)
            
            yacc_optimize:
                Set to False when you're modifying the parser.
                Otherwise, changes in the parser won't be used, if
                some parsetab.py file exists.
                When releasing with a stable parser, set to True
                to save the re-generation of the parser table on 
                each run.
            
            yacctab:
                Points to the yacc table that's used for optimized
                mode. Only if you're modifying the parser, make 
                this point to a local yacc table file
                        
            yacc_debug:
                Generate a parser.out file that explains how yacc
                built the parsing table from the grammar.
        """
        self.clex = AbaqusLexer(
            error_func=self._lex_error_func)
            
        self.clex.build(
            optimize=lex_optimize,
            lextab=lextab)
        self.tokens = self.clex.tokens
        
        self.cparser = ply.yacc.yacc(
            module=self, 
            start='keyword_list',
            debug=yacc_debug,
            optimize=yacc_optimize,
            tabmodule=yacctab)
        
    
    def parse(self, text, filename='', debuglevel=0):
        """ Parses C code and returns an AST.
        
            text:
                A string containing the C source code
            
            filename:
                Name of the file being parsed (for meaningful
                error messages)
            
            debuglevel:
                Debug level to yacc
        """
        self.clex.filename = filename
        self.clex.reset_lineno()
        return self.cparser.parse(text, lexer=self.clex, debug=debuglevel)
    
    ######################--   PRIVATE   --######################
    

    def _lex_error_func(self, msg, line, column):
        self._parse_error(msg, self._coord(line, column))
    
    ##
    ## Grammar productions
    ##

    def p_keyword_list(self, p):
        '''
        keyword_list : keyword_list keyword
        '''
        p[0] = p[1]

    def p_keyword(self, p):
        '''
        keyword_list : keyword
        '''
        p[0] = p[1]

    def p_single_keyword(self, p):
        '''
        keyword : KEYWORD
                | KEYWORD COMMA param_list
                | KEYWORD data_list
                | KEYWORD COMMA param_list data_list
        '''
        print('p_keyword - len(p):{0}'.format(len(p)))
        p[0] = p[1]

    def p_param_list(self, p):
        '''param_list : param_list COMMA param'''
        print('p_param_list - len(p):{0}'.format(len(p)))
        p[0] = p[1] + [p[2]]

    def p_param(self, p):
        '''param_list : param'''
        print('p_param - len(p):{0}'.format(len(p)))
        p[0] = [p[1]]

    def p_single_param(self, p):
        '''
        param : PARAM
              | PARAM EQUALS PARAM
              | PARAM EQUALS FLOAT_CONST
              | PARAM EQUALS INT_CONST_DEC
        '''
        print('p_single_param - len(p):{0}'.format(len(p)))
        if len(p) == 2:
            p[0] = p[1]
        else:
            print('len(p):{0}'.format(len(p)))

    def p_data_list(self, p):
        '''
        data_list : data_list COMMA data
                  | data_list data
        '''
        print('p_data_list - len(p):{0}'.format(len(p)))
        p[0] = p[1] + [p[2]]

    def p_data(self, p):
        '''data_list : data'''
        print('p_data - len(p):{0}'.format(len(p)))
        print('p:{0}:{0}'.format(p))
        p[0] = [p[1]]

    def p_single_data(self, p):
        '''
        data : ID
             | INT_CONST_DEC
             | FLOAT_CONST
        '''
        print('p_single_data - len(p):{0}'.format(len(p)))
        print('p:{0}:{0}'.format(p))
        p[0] = p[1]

    def p_error(self, p):
        if p:
            self._parse_error(
                'before: %s' % p.value, 
                self._coord(p.lineno))
        else:
            self._parse_error('At end of input', '')


if __name__ == "__main__":
    import pprint
    import time, sys
    
    t1 = time.time()
    parser = AbaqusParser(lex_optimize=True, yacc_debug=True, yacc_optimize=False)
    print(time.time() - t1)
    
    buf = ''' 
    *heading
    word1 word2
    line2
    ** comment
    *KEYword,
    param=continue
    *KEYword,param=coffee,param=1.0,param=3,param=4.0e-3
    *node,nset=all_nodes
    1,1.0,1.0e-5,1.0E+6
    2,1.0,1.0e-5,1.0E+6
    3,1.0,1.0e-5,1.0E+6
    4,1.0,1.0e-5,1.0E+6
    *element,type=c3d4,elset=foo
    1,1,2,3,4
    2,3,4,5,6
    *end
    '''
    
    # set debuglevel to 2 for debugging
    t = parser.parse(buf, 'x.c', debuglevel=2)
    for kw in t:
        print kw
