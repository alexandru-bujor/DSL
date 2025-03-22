#TOKENS


TT_INT = 'TT_INT'
TT_FLOAT = 'TT_FLOAT'
TT_STRING = 'TT_STRING'
TT_BOOL = 'TT_BOOL'
TT_LIST = 'TT_LIST'
TT_DICT = 'TT_DICT'
TT_SET = 'TT_SET'
TT_PLUS = 'PLUS'
TT_MINUS = 'MINUS'
TT_TIMES = 'TIMES'
TT_DIVIDE = 'DIVIDE'
TT_MODULO = 'MODULO'
TT_EQUALS = ''
TT_NOT_EQUALS = ''
TT_LESS_THAN = ''

class Token:
    def __init__(self,type_ , value):
        self.type_ = type_
        self.value = value

    def __repr__(self):
        if self.value: return f'{self.type}: {self.value}'
        return f'{self.type}'