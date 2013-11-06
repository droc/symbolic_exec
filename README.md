symbolic_exec
=============

Some experiments I did some years ago after reading about symbolic and concolic execution.

```python
        interpreter = ConcolicInterpreter(DefaultTaintPolicy(), DefaultTaintCheckHandler(), IdProvider(),
                                               print_statements=True)
        the_input = GetInput([UInt32(3), UInt32(1)])
        program = Program([
            Assign("X", MulOp(Value(UInt32(2)), the_input)),
            IF(EQ(SubOp(Var("X"), AddOp(Value(UInt32(3)), Value(UInt32(2)))), Value(UInt32(15))), Value(UInt32(2)),
               Value(UInt32(3))),
            Assign("Y", AddOp(Value(UInt32(3)), Var("X"))),
            IF(GT(Var("Y"), SubOp(the_input, Value(UInt32(20)))), Value(UInt32(4)), Value(UInt32(5)))
        ])
        interpreter.run(a_context().with_program(program).build())
        print str(interpreter.constraints)
```


will print

```
0 :  X := (2) * (get_input())
1 :  if ((X) - ((3) + (2))) == (15) then goto 2 else goto 3
2 :  Y := (3) + (X)
3 :  if (Y) > ((get_input()) - (20)) then goto 4 else goto 5
((3) + ((2) * (s_1))) > ((s_2) - (20)) AND (((2) * (s_1)) - (5)) == (15) AND True
```

Which is a pretty print of the program, plus the formula for the condition on the last IF as function of the symbolic input.

