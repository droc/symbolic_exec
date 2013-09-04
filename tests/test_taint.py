import unittest
from symbolic_engine import (Memory, Program, Assign, AddOp, Value, Interpreter, GetInput, Store, Context, Load, Goto,
                             IF, Var, UInt32, DefaultTaintPolicy, DefaultTaintCheckHandler, AttackException, MulOp,
                             SubOp, ConcolicInterpreter, EQ, GT, IdProvider)


class ContextBuilder(object):
    def __init__(self):
        self.memory = Memory()
        self.variables = {}
        self.program = None

    def with_program(self, p):
        self.program = p
        return self

    def build(self):
        return Context(self.memory, self.variables, UInt32(0), self.program)


def a_context():
    return ContextBuilder()


class TestInterpreter(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter(DefaultTaintPolicy(), DefaultTaintCheckHandler())

    def build_context(self, program):
        return a_context().with_program(program).build()

    def test_32bits(self):
        program = Program([
            Assign('foo', AddOp(Value(UInt32(2 ** 32 - 1)), Value(UInt32(1))))
        ])
        result = self.interpreter.run(self.build_context(program))
        self.assertEqual(UInt32(0), result.resolve_name("foo").value)

    #    def test_mem_op_alignment(self):
    #        self.assertRaises(AlignmentException, lambda: Store(Value(UInt32(0x80000 + 1)), Value(UInt32(0))))
    #        self.assert_(Store(Value(UInt32(0x80000)), Value(UInt32(2))))

    def test_bin_op(self):
        program = Program([
            Assign("foo", MulOp(Value(UInt32(3)), AddOp(Value(UInt32(2)), Value(UInt32(3)))))
        ])
        result = self.interpreter.run(self.build_context(program))
        self.assertEqual(UInt32(15), result.resolve_name("foo").value)

    def test_assign(self):
        program = Program([
            Assign('foo', AddOp(Value(UInt32(10)), Value(UInt32(20))))
        ])
        result = self.interpreter.run(self.build_context(program))
        self.assertEqual(UInt32(30), result.resolve_name("foo").value)

    def test_get_input_assign(self):
        program = Program([
            Assign('foo', GetInput([UInt32(1), UInt32(2), UInt32(3), UInt32(4)])),
            Assign("blah", AddOp(Var("foo"), Value(UInt32(1))))
        ])
        context = self.build_context(program)
        result = self.interpreter.run(context)
        self.assertEqual(UInt32(1), result.resolve_name("foo").value)
        self.assertEqual(UInt32(2), result.resolve_name("blah").value)

    def test_store(self):
        mem_address = UInt32(0x1000)
        program = Program([
            Store(Value(mem_address), AddOp(Value(UInt32(10)), Value(UInt32(20))))
        ])
        context = self.build_context(program)
        self.interpreter.run(context)
        self.assertEqual(UInt32(30), context.get_mem_value(mem_address).value)

    def test_load(self):
        mem_address = UInt32(0x1000)
        program = Program([
            Store(Value(mem_address), AddOp(Value(UInt32(10)), Value(UInt32(20)))),
            Assign("foo", Load(Value(mem_address)))
        ])
        print repr(program)
        print str(program)
        context = self.build_context(program)
        self.interpreter.run(context)
        self.assertEqual(UInt32(30), context.resolve_name("foo").value)

    def test_goto(self):
        program = Program([
            Assign("foo", Value(UInt32(20))),
            Goto(Value(UInt32(3))),
            Assign("foo", Value(UInt32(30))),
            Assign("blah", Value(UInt32(10)))
        ])
        context = self.build_context(program)
        self.interpreter.run(context)
        self.assertEqual(UInt32(20), context.resolve_name("foo").value)

    def test_if(self):
        program = Program([
            Assign("foo", Value(UInt32(10))),
            IF(AddOp(Value(UInt32(0)), Value(UInt32(1))), Value(UInt32(2)), Value(UInt32(3))),
            Assign("foo", AddOp(Var("foo"), Value(UInt32(10)))),
            Assign("blah", Value(UInt32(0)))
        ])
        context = self.build_context(program)
        self.interpreter.run(context)
        self.assertEqual(UInt32(20), context.resolve_name("foo").value)


    def test_taint_memory_address(self):
        mem_pos = 0x1000
        program = Program([
            Assign("EAX", GetInput([UInt32(mem_pos)])),
            Assign("EBX", Value(UInt32(1))),
            Store(Var("EAX"), Var("EBX"))
        ])
        context = self.build_context(program)
        self.interpreter.run(context)
        self.assertTrue(context.get_mem_address_taint(UInt32(0x1000)), 'Expected memory addressed tainted after writen '
                                                                       'with memory address controlled by attacker')


class MemoryTest(unittest.TestCase):
    def test_set_value(self):
        mem = Memory()
        value = Value(UInt32(10))
        mem_pos = UInt32(0x800000)
        mem.set_value(mem_pos, value)
        self.assertEqual(1, mem.get_page_numbers())
        self.assertEqual(value, mem.get_value(mem_pos))


class TaintTest(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter(DefaultTaintPolicy(), DefaultTaintCheckHandler())

    def test_input_var(self):
        program = Program([
            Assign("foo", GetInput([UInt32(0)])),
            Assign("blah", AddOp(Var("foo"), Value(UInt32(1))))
        ])
        context = a_context().with_program(program).build()
        self.interpreter.run(context)
        self.assertTrue(context.resolve_name("foo").isTainted())
        self.assertTrue(context.resolve_name("blah").isTainted())

    def test_const_cleans_taint(self):
        program = Program([
            Assign("foo", GetInput([UInt32(0)])),
            Assign("blah", AddOp(Var("foo"), Value(UInt32(1)))),
            Assign("blah", Value(UInt32(1))),
            ])
        context = a_context().with_program(program).build()
        self.interpreter.run(context)
        self.assertTrue(context.resolve_name("foo").isTainted())
        self.assertFalse(context.resolve_name("blah").isTainted())

    def test_taint_memory(self):
        mem_pos = 0x1000
        program = Program([
            Assign("foo", GetInput([UInt32(0)])),
            Store(Value(UInt32(mem_pos)), Var("foo")),
            Assign("blah", Load(Value(UInt32(mem_pos)))),
            ])
        context = a_context().with_program(program).build()
        self.interpreter.run(context)
        self.assertTrue(context.resolve_name("blah").isTainted())

    def test_positive_taint_check(self):
        mem_pos = 0x1000
        program = Program([
            Assign("foo", GetInput([UInt32(0)])),
            Store(Value(UInt32(mem_pos)), Var("foo")),
            Assign("blah", Load(Value(UInt32(mem_pos)))),
            Goto(Var("blah"))
        ])
        context = a_context().with_program(program).build()
        self.assertRaises(AttackException, lambda: self.interpreter.run(context))


class TestSymbolicExecution(unittest.TestCase):
    def setUp(self):
        self.interpreter = ConcolicInterpreter(DefaultTaintPolicy(), DefaultTaintCheckHandler(), IdProvider(),
                                               print_statements=True)

    def test_bed(self):
        program = Program([
            Assign("X", MulOp(Value(UInt32(2)), GetInput([UInt32(3)]))),
            IF(EQ(SubOp(Var("X"), AddOp(Value(UInt32(3)), Value(UInt32(2)))), Value(UInt32(15))), Value(UInt32(2)),
               Value(UInt32(3))),
            Assign("Y", AddOp(Value(UInt32(3)), Var("X"))),
            IF(GT(Var("Y"), SubOp(GetInput([]), Value(UInt32(20)))), Value(UInt32(4)), Value(UInt32(5)))
        ])
        self.interpreter.run(a_context().with_program(program).build())
        print(str(self.interpreter.constraints))
        self.fail("no assertion yet")