from z3 import *
init(r"C:\Users\core\Downloads\z3-4.3.0-x86\z3-4.3.0-x86\bin\libz3.dll")
# ((3) + ((2) * (s_1))) > ((s_2) - (20)) AND (((2) * (s_1)) - (5)) == (15)
s_1 = BitVec('s_1', 32)
s_2 = BitVec('s_2', 32)

v_3 = BitVecVal(3, 32)
v_2 = BitVecVal(2, 32)
v_20 = BitVecVal(20, 32)
v_5 = BitVecVal(5, 32)
v_15 = BitVecVal(15, 32)

s = And(
    v_3 + (v_2 * s_1) > (s_2 - v_20),
    ((v_2 * s_1) - v_5) == v_15
)
print solve(s)
s2 = And(
    v_3 + (v_2 * s_1) > (s_2 - v_20),
    Not(((v_2 * s_1) - v_5) == v_15)
)

print solve(s2)

s3 = And(
    Not(v_3 + (v_2 * s_1) > (s_2 - v_20)),
    Not(((v_2 * s_1) - v_5) == v_15)
)
print solve(s3)