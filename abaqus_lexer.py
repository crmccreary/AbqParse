#-----------------------------------------------------------------
# pycparser: c_lexer.py
#
# CLexer class: lexer for the C language
#
# Copyright (C) 2008-2011, Eli Bendersky
# License: BSD
#-----------------------------------------------------------------

import re
import sys

import ply.lex
from ply.lex import TOKEN


class AbaqusLexer(object):
    """ A lexer for the C language. After building it, set the
        input text with input(), and call token() to get new 
        tokens.
        
        The public attribute filename can be set to an initial
        filaneme, but the lexer will update it upon #line 
        directives.
    """
    def __init__(self, error_func):
        """ Create a new Lexer.
        
            error_func:
                An error function. Will be called with an error
                message, line and column as arguments, in case of 
                an error during lexing.
                
        """
        self.error_func = error_func
        self.filename = ''
        
    def build(self, **kwargs):
        """ Builds the lexer from the specification. Must be
            called after the lexer object is created. 
            
            This method exists separately, because the PLY
            manual warns against calling lex.lex inside
            __init__
        """
        self.lexer = ply.lex.lex(object=self, **kwargs)

    def reset_lineno(self):
        """ Resets the internal line number counter of the lexer.
        """
        self.lexer.lineno = 1

    def input(self, text):
        self.lexer.input(text)
    
    def token(self):
        g = self.lexer.token()
        return g

    ######################--   PRIVATE   --######################
    
    ##
    ## Internal auxiliary methods
    ##
    def _error(self, msg, token):
        location = self._make_tok_location(token)
        self.error_func(msg, location[0], location[1])
        self.lexer.skip(1)
    
    def _find_tok_column(self, token):
        i = token.lexpos
        while i > 0:
            if self.lexer.lexdata[i] == '\n': break
            i -= 1
        return (token.lexpos - i) + 1
    
    def _make_tok_location(self, token):
        return (token.lineno, self._find_tok_column(token))
    
    ##
    ## All the tokens recognized by the lexer
    ##
    tokens = (
        # Keyword
        'KEYWORD', 
        
        # Identifiers
        'ID', 
        'PARAM', 
        
        # constants 
        'INT_CONST_DEC',
        'FLOAT_CONST', 
        'CHAR_CONST',
        'WCHAR_CONST',
        
        # String literals
        'STRING_LITERAL',
        'WSTRING_LITERAL',

        # Assignment
        'EQUALS',

        # Delimeters 
        'COMMA', 'PERIOD',          # . ,
        
        'LASTTOKENONLINE',
    )

    ##
    ## Regexes for use in tokens
    ##
    ##

    # valid C identifiers (K&R2: A.2.3)
    identifier = r'[a-zA-Z_][0-9a-zA-Z_]*'
    abaqus_keyword = r'\*[a-zA-Z][0-9a-zA-Z_]*'

    # integer constants (K&R2: A.2.5.1)
    integer_suffix_opt = r'(u?ll|U?LL|([uU][lL])|([lL][uU])|[uU]|[lL])?'
    decimal_constant = '(0'+integer_suffix_opt+')|([1-9][0-9]*'+integer_suffix_opt+')'
    octal_constant = '0[0-7]*'+integer_suffix_opt
    hex_constant = '0[xX][0-9a-fA-F]+'+integer_suffix_opt
    
    bad_octal_constant = '0[0-7]*[89]'

    # character constants (K&R2: A.2.5.2)
    # Note: a-zA-Z and '.-~^_!=&;,' are allowed as escape chars to support #line
    # directives with Windows paths as filenames (..\..\dir\file)
    #
    simple_escape = r"""([a-zA-Z._~!=&\^\-\\?'"])"""
    octal_escape = r"""([0-7]{1,3})"""
    hex_escape = r"""(x[0-9a-fA-F]+)"""
    bad_escape = r"""([\\][^a-zA-Z._~^!=&\^\-\\?'"x0-7])"""

    escape_sequence = r"""(\\("""+simple_escape+'|'+octal_escape+'|'+hex_escape+'))'
    cconst_char = r"""([^'\\\n]|"""+escape_sequence+')'    
    char_const = "'"+cconst_char+"'"
    wchar_const = 'L'+char_const
    unmatched_quote = "('"+cconst_char+"*\\n)|('"+cconst_char+"*$)"
    bad_char_const = r"""('"""+cconst_char+"""[^'\n]+')|('')|('"""+bad_escape+r"""[^'\n]*')"""

    # string literals (K&R2: A.2.6)
    string_char = r"""([^"\\\n]|"""+escape_sequence+')'    
    string_literal = '"'+string_char+'*"'
    wstring_literal = 'L'+string_literal
    bad_string_literal = '"'+string_char+'*'+bad_escape+string_char+'*"'

    # floating constants (K&R2: A.2.5.3)
    exponent_part = r"""([eE][-+]?[0-9]+)"""
    fractional_constant = r"""([0-9]*\.[0-9]+)|([0-9]+\.)"""
    floating_constant = '(((('+fractional_constant+')'+exponent_part+'?)|([0-9]+'+exponent_part+'))[FfLl]?)'

    ##
    ## Lexer states
    ##
    states = (
              # 
              ('keywordstate', 'inclusive'),
              ('datalinestate', 'inclusive'),
             )

    @TOKEN(abaqus_keyword)
    def t_KEYWORD(self, t):
        t.lexer.push_state('keywordstate')
        t.value = t.value[1:]
        return t

    @TOKEN(identifier)
    def t_keywordstate_PARAM(self, t):
        return t
    
    def t_keywordstate_CONTINUE(self, t):
        r',\n'
        t.value = ','
        t.type = 'COMMA'
        return t

    def t_keywordstate_NEWLINE(self, t):
        r'\n'
        t.lexer.pop_state()
        t.lexer.push_state('datalinestate')
        t.lexer.lineno += t.value.count("\n")

    t_keywordstate_ignore = ' \t'

    def t_keywordstate_error(self, t):
        msg = 'invalid keyword'
        self._error(msg, t)

    def t_datalinestate_LASTTOKENONLINE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")
        return t

    ##
    ## Rules for the normal state
    ##
    t_ignore = ' \t'

    
    def t_COMMENT(self, t):
        r'[ \t]*\*\*.*\n'
        pass

    # Newlines

    def t_NEWLINEALONE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    # Assignment operators
    t_EQUALS            = r'='

    # Delimeters
    t_COMMA             = r','
    t_PERIOD            = r'\.'

    t_STRING_LITERAL    = string_literal
    
    # The following floating and integer constants are defined as 
    # functions to impose a strict order (otherwise, decimal
    # is placed before the others because its regex is longer,
    # and this is bad)
    #
    @TOKEN(floating_constant)
    def t_FLOAT_CONST(self, t):
        return t

    @TOKEN(hex_constant)
    def t_INT_CONST_HEX(self, t):
        return t

    @TOKEN(bad_octal_constant)
    def t_BAD_CONST_OCT(self, t):
        msg = "Invalid octal constant"
        self._error(msg, t)

    @TOKEN(octal_constant)
    def t_INT_CONST_OCT(self, t):
        return t

    @TOKEN(decimal_constant)
    def t_INT_CONST_DEC(self, t):
        return t

    # Must come before bad_char_const, to prevent it from 
    # catching valid char constants as invalid
    # 
    @TOKEN(char_const)
    def t_CHAR_CONST(self, t):
        return t
        
    @TOKEN(wchar_const)
    def t_WCHAR_CONST(self, t):
        return t
    
    @TOKEN(unmatched_quote)
    def t_UNMATCHED_QUOTE(self, t):
        msg = "Unmatched '"
        self._error(msg, t)

    @TOKEN(bad_char_const)
    def t_BAD_CHAR_CONST(self, t):
        msg = "Invalid char constant %s" % t.value
        self._error(msg, t)

    @TOKEN(wstring_literal)
    def t_WSTRING_LITERAL(self, t):
        return t
    
    # unmatched string literals are caught by the preprocessor
    
    @TOKEN(bad_string_literal)
    def t_BAD_STRING_LITERAL(self, t):
        msg = "String contains invalid escape code" 
        self._error(msg, t)

    @TOKEN(identifier)
    def t_ID(self, t):
        t.type = "ID"
        return t
    
    def t_error(self, t):
        msg = 'Illegal character %s' % repr(t.value[0])
        self._error(msg, t)


if __name__ == "__main__":
    #filename = '../zp.c'
    #text = open(filename).read()
    
    #~ text = '"'+r"""ka \p ka"""+'"'
    text = ''' 
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
    def errfoo(msg, a, b):
        print(msg + "\n")
        sys.exit()
    
    clex = AbaqusLexer(errfoo)
    clex.build(reflags=re.IGNORECASE)
    clex.input(text)
    
    while 1:
        tok = clex.token()
        if not tok: break
            
        #~ print type(tok)
        print([tok.value, tok.type, tok.lineno, clex.filename, tok.lexpos])
        
        

