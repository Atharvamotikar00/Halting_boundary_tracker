"""Built-in example machines."""
EXAMPLES = [
    {"name": "1 - Halting TM (111)", "tape": "111", "start": "q0", "halt": "HALT", "k": 10,
     "rules": "q0,1 -> q0,1,R\nq0,_ -> HALT,_,R"},
    {"name": "2 - Non-Halting TM (TIMEOUT)", "tape": "1", "start": "q0", "halt": "HALT", "k": 10,
     "rules": "q0,1 -> q0,1,R\nq0,_ -> q0,1,R"},
    {"name": "3 - Move Left and Right", "tape": "11", "start": "q0", "halt": "HALT", "k": 50,
     "rules": "# go right to the end, then come back left\n"
              "q0,1 -> q0,1,R\nq0,_ -> q1,_,L\nq1,1 -> q1,1,L\nq1,_ -> HALT,_,R"},
]
