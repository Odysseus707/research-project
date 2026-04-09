\* NodeModalitySelectionILP *\
Minimize
OBJ: x_(1,_'precipitation') + x_(1,_'temp_max') + x_(1,_'temp_min')
 + x_(1,_'wind') + x_(10,_'precipitation') + x_(10,_'temp_max')
 + x_(10,_'temp_min') + x_(10,_'wind') + x_(2,_'precipitation')
 + x_(2,_'temp_max') + x_(2,_'temp_min') + x_(2,_'wind')
 + x_(3,_'precipitation') + x_(3,_'temp_max') + x_(3,_'temp_min')
 + x_(3,_'wind') + x_(4,_'precipitation') + x_(4,_'temp_max')
 + x_(4,_'temp_min') + x_(4,_'wind') + x_(5,_'precipitation')
 + x_(5,_'temp_max') + x_(5,_'temp_min') + x_(5,_'wind')
 + x_(6,_'precipitation') + x_(6,_'temp_max') + x_(6,_'temp_min')
 + x_(6,_'wind') + x_(7,_'precipitation') + x_(7,_'temp_max')
 + x_(7,_'temp_min') + x_(7,_'wind') + x_(8,_'precipitation')
 + x_(8,_'temp_max') + x_(8,_'temp_min') + x_(8,_'wind')
 + x_(9,_'precipitation') + x_(9,_'temp_max') + x_(9,_'temp_min')
 + x_(9,_'wind')
Subject To
_C1: x_(1,_'temp_max') + x_(10,_'temp_max') + x_(2,_'temp_max')
 + x_(3,_'temp_max') + x_(4,_'temp_max') + x_(5,_'temp_max')
 + x_(6,_'temp_max') + x_(7,_'temp_max') + x_(8,_'temp_max')
 + x_(9,_'temp_max') = 1
_C10: x_(3,_'temp_max') = 0
_C11: x_(3,_'wind') = 0
_C12: x_(4,_'wind') = 0
_C13: x_(4,_'precipitation') = 0
_C14: x_(5,_'temp_min') = 0
_C15: x_(5,_'precipitation') = 0
_C16: x_(6,_'temp_max') = 0
_C17: x_(6,_'wind') = 0
_C18: x_(6,_'temp_min') = 0
_C19: x_(7,_'wind') = 0
_C2: x_(1,_'wind') + x_(10,_'wind') + x_(2,_'wind') + x_(3,_'wind')
 + x_(4,_'wind') + x_(5,_'wind') + x_(6,_'wind') + x_(7,_'wind')
 + x_(8,_'wind') + x_(9,_'wind') = 1
_C20: x_(7,_'precipitation') = 0
_C21: x_(8,_'temp_max') = 0
_C22: x_(8,_'precipitation') = 0
_C23: x_(9,_'temp_min') = 0
_C24: x_(10,_'temp_min') = 0
_C25: x_(10,_'precipitation') = 0
_C3: x_(1,_'temp_min') + x_(10,_'temp_min') + x_(2,_'temp_min')
 + x_(3,_'temp_min') + x_(4,_'temp_min') + x_(5,_'temp_min')
 + x_(6,_'temp_min') + x_(7,_'temp_min') + x_(8,_'temp_min')
 + x_(9,_'temp_min') = 1
_C4: x_(1,_'precipitation') + x_(10,_'precipitation') + x_(2,_'precipitation')
 + x_(3,_'precipitation') + x_(4,_'precipitation') + x_(5,_'precipitation')
 + x_(6,_'precipitation') + x_(7,_'precipitation') + x_(8,_'precipitation')
 + x_(9,_'precipitation') = 1
_C5: x_(1,_'temp_min') = 0
_C6: x_(1,_'precipitation') = 0
_C7: x_(2,_'temp_max') = 0
_C8: x_(2,_'wind') = 0
_C9: x_(2,_'temp_min') = 0
Binaries
x_(1,_'precipitation')
x_(1,_'temp_max')
x_(1,_'temp_min')
x_(1,_'wind')
x_(10,_'precipitation')
x_(10,_'temp_max')
x_(10,_'temp_min')
x_(10,_'wind')
x_(2,_'precipitation')
x_(2,_'temp_max')
x_(2,_'temp_min')
x_(2,_'wind')
x_(3,_'precipitation')
x_(3,_'temp_max')
x_(3,_'temp_min')
x_(3,_'wind')
x_(4,_'precipitation')
x_(4,_'temp_max')
x_(4,_'temp_min')
x_(4,_'wind')
x_(5,_'precipitation')
x_(5,_'temp_max')
x_(5,_'temp_min')
x_(5,_'wind')
x_(6,_'precipitation')
x_(6,_'temp_max')
x_(6,_'temp_min')
x_(6,_'wind')
x_(7,_'precipitation')
x_(7,_'temp_max')
x_(7,_'temp_min')
x_(7,_'wind')
x_(8,_'precipitation')
x_(8,_'temp_max')
x_(8,_'temp_min')
x_(8,_'wind')
x_(9,_'precipitation')
x_(9,_'temp_max')
x_(9,_'temp_min')
x_(9,_'wind')
End
