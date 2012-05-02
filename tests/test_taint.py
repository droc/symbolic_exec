import unittest
from symbolic_engine import Memory, Program, Assign, AddOp, Value, Interpreter, GetInput, Store, Context, Load, Goto, IF, Var


class TestTaint(unittest.TestCase):
    def build_context(self, program):
        return Context(Memory(), {}, 0, program)

    def test_assign(self):
        program = Program([
            Assign('foo', AddOp(Value(10), Value(20)))
        ])
        interpreter = Interpreter()
        result = interpreter.run(self.build_context(program))
        self.assertEqual(30, result.resolve_name("foo"))

    def test_get_input_assign(self):
        program = Program([
            Assign('foo', GetInput([1, 2, 3, 4]))
        ])
        context = self.build_context(program)
        interpreter = Interpreter()
        result = interpreter.run(context)
        self.assertEqual(1, result.resolve_name("foo"))

    def test_store(self):
        mem_address = 0x1000
        program = Program([
            Store(Value(mem_address), AddOp(Value(10), Value(20)))
        ])
        context = self.build_context(program)
        interpreter = Interpreter()
        interpreter.run(context)
        self.assertEqual(30, context.get_mem_value(mem_address))

    def test_load(self):
        mem_address = 0x1000
        program = Program([
            Store(Value(mem_address), AddOp(Value(10), Value(20))),
            Assign("foo", Load(Value(mem_address)))
        ])
        context = self.build_context(program)
        interpreter = Interpreter()
        interpreter.run(context)
        self.assertEqual(30, context.resolve_name("foo"))

    def test_goto(self):
        program = Program([
            Assign("foo", Value(20)),
            Goto(Value(3)),
            Assign("foo", Value(30)),
            Assign("blah", Value(10))
        ])
        context = self.build_context(program)
        interpreter = Interpreter()
        interpreter.run(context)
        self.assertEqual(20, context.resolve_name("foo"))

    def test_if(self):
        program = Program([
            Assign("foo", Value(10)),
            IF(AddOp(Value(0), Value(1)), Value(2), Value(3)),
            Assign("foo", AddOp(Var("foo"), Value(10))),
            Assign("blah", Value(0))
        ])
        context = self.build_context(program)
        interpreter = Interpreter()
        interpreter.run(context)
        self.assertEqual(20, context.resolve_name("foo"))


class MemoryTest(unittest.TestCase):
    def test_set_value(self):
        mem = Memory()
        value = 10
        mem_pos = 0x800000
        mem.set_value(mem_pos, value)
        self.assertEqual(1, mem.get_page_numbers())
        self.assertEqual(value, mem.get_value(mem_pos))