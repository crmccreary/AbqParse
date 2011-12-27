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

def list_append(lst, item):
    lst.append(item)
    return lst

class Parameter(object):
    def __init__(self, name, value = None):
        self.name = name
        self.value = value
        
class Keyword(object):
    def __init__(self, keyword, params = None, data = None):
        self.keyword = keyword
        self.params = params
        self.data = data
        
    def __str__(self):
        kwd_str_list = ['Keyword:{0}'.format(self.keyword),]
        kwd_str_list.append('\n')
        if self.params is not None:
            for param in self.params:
                kwd_str_list.append('Parameter:{0}={1}'.format(param.name, param.value))
                kwd_str_list.append('\n')
        kwd_str_list.append('Data:\n')
        if self.data is not None:
            for data in self.data:
                kwd_str_list.append('{0},'.format(data))
                kwd_str_list.append('\n')
        return ''.join([item for item in kwd_str_list])
    
    def __repr__(self):
        return str(self)
        
keywords = []

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
        p[0] = p[1] + [p[2]]

    def p_keyword(self, p):
        '''
        keyword_list : keyword
        '''
        p[0] = [p[1]]

    def p_single_keyword(self, p):
        '''
        keyword : KEYWORD
                | KEYWORD data_lines
                | KEYWORD COMMA param_list
                | KEYWORD COMMA param_list data_lines
        '''
        if len(p) == 2:
            # KEYWORD
            p[0] = Keyword(p[1])
        elif len(p) == 3:
            # KEYWORD data_list
            p[0] = Keyword(p[1], data = p[2])
        elif len(p) == 4:
            # KEYWORD COMMA param_list
            p[0] = Keyword(p[1], params = p[3])
        elif len(p) == 5:
            # KEYWORD COMMA param_list data_list
            p[0] = Keyword(p[1], params = p[3], data = p[4])
        else:
            # Error?
            pass

    def p_param_list(self, p):
        '''param_list : param_list COMMA param'''
        p[0] = p[1] + [p[3]]

    def p_param(self, p):
        '''param_list : param'''
        p[0] = [p[1]]

    def p_single_param(self, p):
        '''
        param : PARAM
              | PARAM EQUALS PARAM
              | PARAM EQUALS FLOAT_CONST
              | PARAM EQUALS INT_CONST_DEC
        '''
        if len(p) == 2:
            p[0] = Parameter(p[1])
        elif len(p) == 4:
            p[0] = Parameter(p[1], value = p[3])
            

    def p_data_lines_list(self, p):
        '''
        data_lines : data_lines data_line
        '''
        p[0] = list_append(p[1],p[2])

    def p_data_lines(self, p):
        '''
        data_lines : data_line
        '''
        p[0] = [p[1]]

    def p_data_line(self, p):
        '''
        data_line : data_list LASTTOKENONLINE
        '''
        p[0] = p[1]

    def p_data_list(self, p):
        '''
        data_list : data_list COMMA data
                  | data_list data
        '''
        if len(p) == 3:
            p[0] = p[1] + [p[2]]
        elif len(p) == 4:
            p[0] = p[1] + [p[3]]

    def p_data(self, p):
        '''
        data_list : data
        '''
        p[0] = [p[1]]

    def p_single_data(self, p):
        '''
        data : ID
             | INT_CONST_DEC
             | FLOAT_CONST
        '''
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
    *keyword,singleparam
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
    t = parser.parse(buf, 'x.c', debuglevel=0)
    for kw in t:
        print kw
