\* NodeModalitySelectionILP *\
Minimize
OBJ: x_(2,_'precipitation') + x_(2,_'temp_max') + x_(2,_'temp_min')
 + x_(2,_'wind')
Subject To
_C1: x_(2,_'precipitation') = 1
_C2: x_(2,_'temp_min') = 1
_C3: x_(2,_'wind') = 1
_C4: x_(2,_'temp_max') = 1
_C5: x_(2,_'precipitation') = 0
_C6: x_(2,_'wind') = 0
_C7: x_(2,_'temp_max') = 0
Binaries
x_(2,_'precipitation')
x_(2,_'temp_max')
x_(2,_'temp_min')
x_(2,_'wind')
End
