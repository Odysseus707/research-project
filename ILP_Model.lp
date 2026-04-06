\* NodeModalitySelectionILP *\
Minimize
OBJ: x_(1,_'precipitation') + x_(1,_'temp_max') + x_(1,_'temp_min')
 + x_(1,_'wind') + 3 x_(10,_'precipitation') + 3 x_(10,_'temp_max')
 + 3 x_(10,_'temp_min') + 3 x_(10,_'wind') + 3 x_(11,_'precipitation')
 + 3 x_(11,_'temp_max') + 3 x_(11,_'temp_min') + 3 x_(11,_'wind')
 + 3 x_(12,_'precipitation') + 3 x_(12,_'temp_max') + 3 x_(12,_'temp_min')
 + 3 x_(12,_'wind') + 3 x_(13,_'precipitation') + 3 x_(13,_'temp_max')
 + 3 x_(13,_'temp_min') + 3 x_(13,_'wind') + 3 x_(14,_'precipitation')
 + 3 x_(14,_'temp_max') + 3 x_(14,_'temp_min') + 3 x_(14,_'wind')
 + 4 x_(15,_'precipitation') + 4 x_(15,_'temp_max') + 4 x_(15,_'temp_min')
 + 4 x_(15,_'wind') + 4 x_(16,_'precipitation') + 4 x_(16,_'temp_max')
 + 4 x_(16,_'temp_min') + 4 x_(16,_'wind') + 4 x_(17,_'precipitation')
 + 4 x_(17,_'temp_max') + 4 x_(17,_'temp_min') + 4 x_(17,_'wind')
 + 4 x_(18,_'precipitation') + 4 x_(18,_'temp_max') + 4 x_(18,_'temp_min')
 + 4 x_(18,_'wind') + 4 x_(19,_'precipitation') + 4 x_(19,_'temp_max')
 + 4 x_(19,_'temp_min') + 4 x_(19,_'wind') + x_(2,_'precipitation')
 + x_(2,_'temp_max') + x_(2,_'temp_min') + x_(2,_'wind')
 + 4 x_(20,_'precipitation') + 4 x_(20,_'temp_max') + 4 x_(20,_'temp_min')
 + 4 x_(20,_'wind') + 4 x_(21,_'precipitation') + 4 x_(21,_'temp_max')
 + 4 x_(21,_'temp_min') + 4 x_(21,_'wind') + 4 x_(22,_'precipitation')
 + 4 x_(22,_'temp_max') + 4 x_(22,_'temp_min') + 4 x_(22,_'wind')
 + 4 x_(23,_'precipitation') + 4 x_(23,_'temp_max') + 4 x_(23,_'temp_min')
 + 4 x_(23,_'wind') + 4 x_(24,_'precipitation') + 4 x_(24,_'temp_max')
 + 4 x_(24,_'temp_min') + 4 x_(24,_'wind') + 4 x_(25,_'precipitation')
 + 4 x_(25,_'temp_max') + 4 x_(25,_'temp_min') + 4 x_(25,_'wind')
 + 4 x_(26,_'precipitation') + 4 x_(26,_'temp_max') + 4 x_(26,_'temp_min')
 + 4 x_(26,_'wind') + 4 x_(27,_'precipitation') + 4 x_(27,_'temp_max')
 + 4 x_(27,_'temp_min') + 4 x_(27,_'wind') + 4 x_(28,_'precipitation')
 + 4 x_(28,_'temp_max') + 4 x_(28,_'temp_min') + 4 x_(28,_'wind')
 + 4 x_(29,_'precipitation') + 4 x_(29,_'temp_max') + 4 x_(29,_'temp_min')
 + 4 x_(29,_'wind') + 2 x_(3,_'precipitation') + 2 x_(3,_'temp_max')
 + 2 x_(3,_'temp_min') + 2 x_(3,_'wind') + 4 x_(30,_'precipitation')
 + 4 x_(30,_'temp_max') + 4 x_(30,_'temp_min') + 4 x_(30,_'wind')
 + 2 x_(4,_'precipitation') + 2 x_(4,_'temp_max') + 2 x_(4,_'temp_min')
 + 2 x_(4,_'wind') + 2 x_(5,_'precipitation') + 2 x_(5,_'temp_max')
 + 2 x_(5,_'temp_min') + 2 x_(5,_'wind') + 2 x_(6,_'precipitation')
 + 2 x_(6,_'temp_max') + 2 x_(6,_'temp_min') + 2 x_(6,_'wind')
 + 3 x_(7,_'precipitation') + 3 x_(7,_'temp_max') + 3 x_(7,_'temp_min')
 + 3 x_(7,_'wind') + 3 x_(8,_'precipitation') + 3 x_(8,_'temp_max')
 + 3 x_(8,_'temp_min') + 3 x_(8,_'wind') + 3 x_(9,_'precipitation')
 + 3 x_(9,_'temp_max') + 3 x_(9,_'temp_min') + 3 x_(9,_'wind')
Subject To
_C1: x_(1,_'temp_max') + x_(10,_'temp_max') + x_(11,_'temp_max')
 + x_(12,_'temp_max') + x_(13,_'temp_max') + x_(14,_'temp_max')
 + x_(15,_'temp_max') + x_(16,_'temp_max') + x_(17,_'temp_max')
 + x_(18,_'temp_max') + x_(19,_'temp_max') + x_(2,_'temp_max')
 + x_(20,_'temp_max') + x_(21,_'temp_max') + x_(22,_'temp_max')
 + x_(23,_'temp_max') + x_(24,_'temp_max') + x_(25,_'temp_max')
 + x_(26,_'temp_max') + x_(27,_'temp_max') + x_(28,_'temp_max')
 + x_(29,_'temp_max') + x_(3,_'temp_max') + x_(30,_'temp_max')
 + x_(4,_'temp_max') + x_(5,_'temp_max') + x_(6,_'temp_max')
 + x_(7,_'temp_max') + x_(8,_'temp_max') + x_(9,_'temp_max') = 1
_C10: x_(3,_'temp_min') = 0
_C11: x_(4,_'precipitation') = 0
_C12: x_(4,_'wind') = 0
_C13: x_(5,_'temp_max') = 0
_C14: x_(5,_'temp_min') = 0
_C15: x_(6,_'temp_max') = 0
_C16: x_(6,_'wind') = 0
_C17: x_(7,_'temp_max') = 0
_C18: x_(7,_'wind') = 0
_C19: x_(8,_'wind') = 0
_C2: x_(1,_'precipitation') + x_(10,_'precipitation')
 + x_(11,_'precipitation') + x_(12,_'precipitation') + x_(13,_'precipitation')
 + x_(14,_'precipitation') + x_(15,_'precipitation') + x_(16,_'precipitation')
 + x_(17,_'precipitation') + x_(18,_'precipitation') + x_(19,_'precipitation')
 + x_(2,_'precipitation') + x_(20,_'precipitation') + x_(21,_'precipitation')
 + x_(22,_'precipitation') + x_(23,_'precipitation') + x_(24,_'precipitation')
 + x_(25,_'precipitation') + x_(26,_'precipitation') + x_(27,_'precipitation')
 + x_(28,_'precipitation') + x_(29,_'precipitation') + x_(3,_'precipitation')
 + x_(30,_'precipitation') + x_(4,_'precipitation') + x_(5,_'precipitation')
 + x_(6,_'precipitation') + x_(7,_'precipitation') + x_(8,_'precipitation')
 + x_(9,_'precipitation') = 1
_C20: x_(8,_'temp_min') = 0
_C21: x_(9,_'temp_max') = 0
_C22: x_(9,_'temp_min') = 0
_C23: x_(10,_'precipitation') = 0
_C24: x_(10,_'wind') = 0
_C25: x_(11,_'precipitation') = 0
_C26: x_(11,_'wind') = 0
_C27: x_(12,_'precipitation') = 0
_C28: x_(12,_'temp_min') = 0
_C29: x_(13,_'temp_max') = 0
_C3: x_(1,_'wind') + x_(10,_'wind') + x_(11,_'wind') + x_(12,_'wind')
 + x_(13,_'wind') + x_(14,_'wind') + x_(15,_'wind') + x_(16,_'wind')
 + x_(17,_'wind') + x_(18,_'wind') + x_(19,_'wind') + x_(2,_'wind')
 + x_(20,_'wind') + x_(21,_'wind') + x_(22,_'wind') + x_(23,_'wind')
 + x_(24,_'wind') + x_(25,_'wind') + x_(26,_'wind') + x_(27,_'wind')
 + x_(28,_'wind') + x_(29,_'wind') + x_(3,_'wind') + x_(30,_'wind')
 + x_(4,_'wind') + x_(5,_'wind') + x_(6,_'wind') + x_(7,_'wind')
 + x_(8,_'wind') + x_(9,_'wind') = 1
_C30: x_(13,_'temp_min') = 0
_C31: x_(14,_'precipitation') = 0
_C32: x_(14,_'temp_min') = 0
_C33: x_(15,_'temp_max') = 0
_C34: x_(15,_'temp_min') = 0
_C35: x_(16,_'wind') = 0
_C36: x_(16,_'temp_min') = 0
_C37: x_(17,_'precipitation') = 0
_C38: x_(17,_'wind') = 0
_C39: x_(18,_'temp_max') = 0
_C4: x_(1,_'temp_min') + x_(10,_'temp_min') + x_(11,_'temp_min')
 + x_(12,_'temp_min') + x_(13,_'temp_min') + x_(14,_'temp_min')
 + x_(15,_'temp_min') + x_(16,_'temp_min') + x_(17,_'temp_min')
 + x_(18,_'temp_min') + x_(19,_'temp_min') + x_(2,_'temp_min')
 + x_(20,_'temp_min') + x_(21,_'temp_min') + x_(22,_'temp_min')
 + x_(23,_'temp_min') + x_(24,_'temp_min') + x_(25,_'temp_min')
 + x_(26,_'temp_min') + x_(27,_'temp_min') + x_(28,_'temp_min')
 + x_(29,_'temp_min') + x_(3,_'temp_min') + x_(30,_'temp_min')
 + x_(4,_'temp_min') + x_(5,_'temp_min') + x_(6,_'temp_min')
 + x_(7,_'temp_min') + x_(8,_'temp_min') + x_(9,_'temp_min') = 1
_C40: x_(18,_'wind') = 0
_C41: x_(19,_'precipitation') = 0
_C42: x_(19,_'temp_min') = 0
_C43: x_(20,_'temp_max') = 0
_C44: x_(20,_'wind') = 0
_C45: x_(21,_'temp_max') = 0
_C46: x_(21,_'precipitation') = 0
_C47: x_(22,_'wind') = 0
_C48: x_(22,_'temp_min') = 0
_C49: x_(23,_'wind') = 0
_C5: x_(1,_'temp_max') = 0
_C50: x_(23,_'temp_min') = 0
_C51: x_(24,_'temp_max') = 0
_C52: x_(24,_'temp_min') = 0
_C53: x_(25,_'temp_max') = 0
_C54: x_(25,_'precipitation') = 0
_C55: x_(26,_'precipitation') = 0
_C56: x_(26,_'wind') = 0
_C57: x_(27,_'precipitation') = 0
_C58: x_(27,_'wind') = 0
_C59: x_(28,_'temp_max') = 0
_C6: x_(1,_'wind') = 0
_C60: x_(28,_'wind') = 0
_C61: x_(29,_'temp_max') = 0
_C62: x_(29,_'wind') = 0
_C63: x_(30,_'temp_max') = 0
_C64: x_(30,_'wind') = 0
_C7: x_(2,_'temp_max') = 0
_C8: x_(2,_'wind') = 0
_C9: x_(3,_'wind') = 0
Binaries
x_(1,_'precipitation')
x_(1,_'temp_max')
x_(1,_'temp_min')
x_(1,_'wind')
x_(10,_'precipitation')
x_(10,_'temp_max')
x_(10,_'temp_min')
x_(10,_'wind')
x_(11,_'precipitation')
x_(11,_'temp_max')
x_(11,_'temp_min')
x_(11,_'wind')
x_(12,_'precipitation')
x_(12,_'temp_max')
x_(12,_'temp_min')
x_(12,_'wind')
x_(13,_'precipitation')
x_(13,_'temp_max')
x_(13,_'temp_min')
x_(13,_'wind')
x_(14,_'precipitation')
x_(14,_'temp_max')
x_(14,_'temp_min')
x_(14,_'wind')
x_(15,_'precipitation')
x_(15,_'temp_max')
x_(15,_'temp_min')
x_(15,_'wind')
x_(16,_'precipitation')
x_(16,_'temp_max')
x_(16,_'temp_min')
x_(16,_'wind')
x_(17,_'precipitation')
x_(17,_'temp_max')
x_(17,_'temp_min')
x_(17,_'wind')
x_(18,_'precipitation')
x_(18,_'temp_max')
x_(18,_'temp_min')
x_(18,_'wind')
x_(19,_'precipitation')
x_(19,_'temp_max')
x_(19,_'temp_min')
x_(19,_'wind')
x_(2,_'precipitation')
x_(2,_'temp_max')
x_(2,_'temp_min')
x_(2,_'wind')
x_(20,_'precipitation')
x_(20,_'temp_max')
x_(20,_'temp_min')
x_(20,_'wind')
x_(21,_'precipitation')
x_(21,_'temp_max')
x_(21,_'temp_min')
x_(21,_'wind')
x_(22,_'precipitation')
x_(22,_'temp_max')
x_(22,_'temp_min')
x_(22,_'wind')
x_(23,_'precipitation')
x_(23,_'temp_max')
x_(23,_'temp_min')
x_(23,_'wind')
x_(24,_'precipitation')
x_(24,_'temp_max')
x_(24,_'temp_min')
x_(24,_'wind')
x_(25,_'precipitation')
x_(25,_'temp_max')
x_(25,_'temp_min')
x_(25,_'wind')
x_(26,_'precipitation')
x_(26,_'temp_max')
x_(26,_'temp_min')
x_(26,_'wind')
x_(27,_'precipitation')
x_(27,_'temp_max')
x_(27,_'temp_min')
x_(27,_'wind')
x_(28,_'precipitation')
x_(28,_'temp_max')
x_(28,_'temp_min')
x_(28,_'wind')
x_(29,_'precipitation')
x_(29,_'temp_max')
x_(29,_'temp_min')
x_(29,_'wind')
x_(3,_'precipitation')
x_(3,_'temp_max')
x_(3,_'temp_min')
x_(3,_'wind')
x_(30,_'precipitation')
x_(30,_'temp_max')
x_(30,_'temp_min')
x_(30,_'wind')
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
