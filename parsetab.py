
# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'COLON COMMA CONNECT DEVICE DOT IDENTIFIER LBRACE NUMBER RBRACE STRINGprogram : statementsstatements : statement statementsstatements : statementstatement : DEVICE IDENTIFIER IDENTIFIER LBRACE attributes RBRACEstatement : CONNECT connection_listattributes : attribute attributesattributes : attributeattribute : IDENTIFIER COLON valuevalue : STRINGvalue : NUMBERvalue : IDENTIFIERconnection_list : connection COMMA connection_listconnection_list : connectionconnection : IDENTIFIER DOT IDENTIFIER'
    
_lr_action_items = {'DEVICE':([0,3,8,9,15,16,21,],[4,4,-5,-13,-12,-14,-4,]),'CONNECT':([0,3,8,9,15,16,21,],[5,5,-5,-13,-12,-14,-4,]),'$end':([1,2,3,6,8,9,15,16,21,],[0,-1,-3,-2,-5,-13,-12,-14,-4,]),'IDENTIFIER':([4,5,7,12,13,14,19,20,23,24,25,26,],[7,10,11,10,16,17,17,23,-11,-8,-9,-10,]),'COMMA':([9,16,],[12,-14,]),'DOT':([10,],[13,]),'LBRACE':([11,],[14,]),'COLON':([17,],[20,]),'RBRACE':([18,19,22,23,24,25,26,],[21,-7,-6,-11,-8,-9,-10,]),'STRING':([20,],[25,]),'NUMBER':([20,],[26,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'program':([0,],[1,]),'statements':([0,3,],[2,6,]),'statement':([0,3,],[3,3,]),'connection_list':([5,12,],[8,15,]),'connection':([5,12,],[9,9,]),'attributes':([14,19,],[18,22,]),'attribute':([14,19,],[19,19,]),'value':([20,],[24,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> program","S'",1,None,None,None),
  ('program -> statements','program',1,'p_program','NETAR.py',86),
  ('statements -> statement statements','statements',2,'p_statements_multiple','NETAR.py',91),
  ('statements -> statement','statements',1,'p_statements_single','NETAR.py',96),
  ('statement -> DEVICE IDENTIFIER IDENTIFIER LBRACE attributes RBRACE','statement',6,'p_statement_device','NETAR.py',101),
  ('statement -> CONNECT connection_list','statement',2,'p_statement_connect','NETAR.py',107),
  ('attributes -> attribute attributes','attributes',2,'p_attributes_multiple','NETAR.py',112),
  ('attributes -> attribute','attributes',1,'p_attributes_single','NETAR.py',118),
  ('attribute -> IDENTIFIER COLON value','attribute',3,'p_attribute','NETAR.py',123),
  ('value -> STRING','value',1,'p_value_string','NETAR.py',128),
  ('value -> NUMBER','value',1,'p_value_number','NETAR.py',133),
  ('value -> IDENTIFIER','value',1,'p_value_identifier','NETAR.py',138),
  ('connection_list -> connection COMMA connection_list','connection_list',3,'p_connection_list_multiple','NETAR.py',143),
  ('connection_list -> connection','connection_list',1,'p_connection_list_single','NETAR.py',148),
  ('connection -> IDENTIFIER DOT IDENTIFIER','connection',3,'p_connection','NETAR.py',153),
]
