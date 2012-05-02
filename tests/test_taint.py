import unittest
from symbolic_engine import (Memory, Program, Assign, AddOp, Value, Interpreter, GetInput, Store, Context, Load, Goto,
                             IF, Var, UInt32, AlignmentException)


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
    def build_context(self, program):
        return a_context().with_program(program).build()

    def test_32bits(self):
        program = Program([
            Assign('foo', AddOp(Value(UInt32(2 ** 32 - 1)), Value(UInt32(1))))
        ])
        interpreter = Interpreter()
        result = interpreter.run(self.build_context(program))
        self.assertEqual(UInt32(0), result.resolve_name("foo").value)

    def test_mem_op_alignment(self):
        self.assertRaises(AlignmentException, lambda: Store(Value(UInt32(0x80000 + 1)), Value(UInt32(0))))
        self.assert_(Store(Value(UInt32(0x80000)), Value(UInt32(2))))

    def test_assign(self):
        program = Program([
            Assign('foo', AddOp(Value(UInt32(10)), Value(UInt32(20))))
        ])
        interpreter = Interpreter()
        result = interpreter.run(self.build_context(program))
        self.assertEqual(UInt32(30), result.resolve_name("foo").value)

    def test_get_input_assign(self):
        program = Program([
            Assign('foo', GetInput([UInt32(1), UInt32(2), UInt32(3), UInt32(4)])),
            Assign("blah", AddOp(Var("foo"), Value(UInt32(1))))
        ])
        context = self.build_context(program)
        interpreter = Interpreter()
        result = interpreter.run(context)
        self.assertEqual(UInt32(1), result.resolve_name("foo").value)
        self.assertEqual(UInt32(2), result.resolve_name("blah").value)

    def test_store(self):
        mem_address = UInt32(0x1000)
        program = Program([
            Store(Value(mem_address), AddOp(Value(UInt32(10)), Value(UInt32(20))))
        ])
        context = self.build_context(program)
        interpreter = Interpreter()
        interpreter.run(context)
        self.assertEqual(UInt32(30), context.get_mem_value(mem_address).value)

    def test_load(self):
        mem_address = UInt32(0x1000)
        program = Program([
            Store(Value(mem_address), AddOp(Value(UInt32(10)), Value(UInt32(20)))),
            Assign("foo", Load(Value(mem_address)))
        ])
        context = self.build_context(program)
        interpreter = Interpreter()
        interpreter.run(context)
        self.assertEqual(UInt32(30), context.resolve_name("foo").value)

    def test_goto(self):
        program = Program([
            Assign("foo", Value(UInt32(20))),
            Goto(Value(UInt32(3))),
            Assign("foo", Value(UInt32(30))),
            Assign("blah", Value(UInt32(10)))
        ])
        context = self.build_context(program)
        interpreter = Interpreter()
        interpreter.run(context)
        self.assertEqual(UInt32(20), context.resolve_name("foo").value)

    def test_if(self):
        program = Program([
            Assign("foo", Value(UInt32(10))),
            IF(AddOp(Value(UInt32(0)), Value(UInt32(1))), Value(UInt32(2)), Value(UInt32(3))),
            Assign("foo", AddOp(Var("foo"), Value(UInt32(10)))),
            Assign("blah", Value(UInt32(0)))
        ])
        context = self.build_context(program)
        interpreter = Interpreter()
        interpreter.run(context)
        self.assertEqual(UInt32(20), context.resolve_name("foo").value)


class MemoryTest(unittest.TestCase):
    def test_set_value(self):
        mem = Memory()
        value = Value(UInt32(10))
        mem_pos = UInt32(0x800000)
        mem.set_value(mem_pos, value)
        self.assertEqual(1, mem.get_page_numbers())
        self.assertEqual(value, mem.get_value(mem_pos))


class TaintTest(unittest.TestCase):
    def test_input_var(self):
        program = Program([
            Assign("foo", GetInput([UInt32(0)])),
            Assign("blah", AddOp(Var("foo"), Value(UInt32(1))))
        ])
        context = a_context().with_program(program).build()
        interpreter = Interpreter()
        interpreter.run(context)
        self.assertTrue(context.resolve_name("foo").isTainted())
        self.assertTrue(context.resolve_name("blah").isTainted())

    def test_const_cleans_taint(self):
        program = Program([
            Assign("foo", GetInput([UInt32(0)])),
            Assign("blah", AddOp(Var("foo"), Value(UInt32(1)))),
            Assign("blah", Value(UInt32(1))),
            ])
        context = a_context().with_program(program).build()
        interpreter = Interpreter()
        interpreter.run(context)
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
        interpreter = Interpreter()
        interpreter.run(context)
        self.assertTrue(context.resolve_name("blah").isTainted())
