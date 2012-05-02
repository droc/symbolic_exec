import math


class Instruction(object):
    def get_name(self):
        return self.__class__.__name__


class MemoryPage(object):
    """"""

    def __init__(self, size, base_address):
        """Constructor for MemoryPage
        @type size: int
        @type base_address: int
        """
        self.base_address = base_address
        self.size = size
        self.__contents = [0] * self.size

    def validate_address(self, address):
        if not self.base_address <= address < (self.base_address + self.size):
            raise Exception("address outside page")

    def set_value(self, address, value):
        """
        @type address: int
        @type value: int
        """
        self.validate_address(address)
        self.__contents[address - self.base_address] = value

    def get_value(self, address):
        self.validate_address(address)
        return self.__contents[address - self.base_address]


class Memory(object):
    def __init__(self, page_size=1024 * 4):
        self.page_size = page_size
        self.pages = {}

    def set_value(self, v1, v2):
        page = self.get_page(v1)
        page.set_value(v1, v2)

    def get_page(self, v1):
        page_nr = int(math.floor(v1 / self.page_size))
        if not page_nr in self.pages:
            self.pages[page_nr] = MemoryPage(self.page_size, page_nr * self.page_size)
        return self.pages[page_nr]

    def get_page_numbers(self):
        return len(self.pages)

    def get_value(self, mem_pos):
        """
        @type mem_pos: int
        """
        page = self.get_page(mem_pos)
        return page.get_value(mem_pos)


class Context(object):
    """"""

    def __init__(self, memory, variables, pc, program):
        """Constructor for Context
        @type program: Program
        @type pc: UInt32
        @type variables: dict
        @type memory: Memory
        """
        self.variables = variables
        self.memory = memory
        self.pc = pc
        self.program = program

    def current_instr(self):
        """
        @rtype Instruction
        """
        return self.program.get_stmts(self.pc)

    def get_mem_value(self, address):
        """
        @type address: UInt32
        """
        return UInt32(self.memory.get_value(address.value))

    def resolve_name(self, name):
        return self.variables[name]

    def copy(self):
        return Context(self.memory, self.variables, self.pc, self.program)

    def set_mem_value(self, v1, v2):
        """
        @type v1: UInt32
        @type v2: UInt32
        """
        self.memory.set_value(v1.value, v2.value)


class Assign(Instruction):
    def __init__(self, var_name, expression):
        """Constructor for Assign"""
        self.expression = expression
        self.var_name = var_name


class Program(object):
    """"""

    def __init__(self, stmts):
        """Constructor for Program"""
        self.stmts = stmts

    def get_stmts(self, pc):
        """
        @rtype Instruction
        """

        try:
            return self.stmts[pc.value]
        except IndexError:
            return None


class Rule(object):
    def apply(self, context):
        """
        @type context: Context
        """
        raise NotImplementedError


class Expression(Instruction):
    """"""
    pass


class BinOp(Expression):
    """"""

    def __init__(self, left, right):
        """

        @param left: l
        @param right: r
        @type left: Expression
        @type right: Expression
        """
        self.right = right
        self.left = left


class AddOp(BinOp):
    """"""

    pass


class Interpreter(object):
    def __init__(self):
        self.rules = {
            'Assign': self.assign_rule,
            'Store': self.store_rule,
            'Goto': self.goto_rule,
            'IF': self.eval_if
        }

    def eval_if(self, context):
        instr = context.current_instr()
        e = instr.e
        e1 = instr.e1
        e2 = instr.e2
        cond = self.eval_expression(e, context)
        if cond == UInt32(1):
            v1 = self.eval_expression(e1, context)
        elif cond == UInt32(0):
            v1 = self.eval_expression(e2, context)
        else:
            raise Exception("Invalid value: expected boolean (0 or 1)")
        context.pc = v1
        return context

    def goto_rule(self, context):
        instr = context.current_instr()
        v1 = self.eval_expression(instr.pc, context)
        context.pc = v1
        return context

    def store_rule(self, context):
        """

        @param context: context
        @type context: Context

        @return:
        """
        instr = context.current_instr()
        v1 = self.eval_expression(instr.e1, context)
        v2 = self.eval_expression(instr.e2, context)
        context.pc += UInt32(1)
        context.set_mem_value(v1, v2)
        return context

    def assign_rule(self, context):
        """
        @type context: Context
        """
        instr = context.current_instr()
        assert instr.get_name() == 'Assign'
        context.variables[instr.var_name] = self.eval_expression(instr.expression, context)
        context.pc += UInt32(1)
        return context


    def run(self, context):
        """
        Fetch-execute loop
        @type context: Context
        """
        next_instr = context.current_instr()
        while next_instr:
            name = next_instr.get_name()
            rule = self.rules.get(name)
            if rule is None:
                raise Exception("No rule for %s" % name)
            context = rule(context)
            next_instr = context.current_instr()
        return context

    def eval_binop(self, expression, context):
        """

        @param expression: a binop expression
        @type expression: BinOp
        @param context: the current context
        @return: the evaluation of the expression in the current context
        @type expression: BinOp
        @rtype int
        """
        if expression.get_name() == 'AddOp':
            return self.eval_expression(expression.left, context) + self.eval_expression(expression.right, context)
        else:
            raise Exception("Operation not implemented")

    def eval_expression(self, expression, context):
        name = expression.get_name()
        binops = set(['AddOp'])
        if name in binops:
            return self.eval_binop(expression, context)
        elif name == 'Value':
            return self.eval_value(expression, context)
        elif name == 'GetInput':
            return self.eval_input(expression, context)
        elif name == "Load":
            return self.eval_load(expression, context)
        elif name == 'Var':
            return self.eval_var(expression, context)
        else:
            raise NotImplementedError(name)

    def eval_var(self, expression, context):
        """

        @param expression:
        @param context:
        @type expression: Var
        @return:
        """
        return context.resolve_name(expression.var_name)

    def eval_value(self, expression, context):
        """
        @type expression: Value
        @rtype UInt32
        """
        return expression.value

    def eval_input(self, expression, context):
        """
        @type expression: GetInput
        """
        return expression.get_input()

    def eval_load(self, expression, context):
        """
        @type expression: Load
        @type context: Context
        """
        return context.get_mem_value(self.eval_expression(expression.address, context))


class UInt32(object):
    def __init__(self, value):
        assert value < (2 ** 32), "Initial value of UInt32 can't be greater than word size (32 bits)"
        self.value = value

    def __eq__(self, other):
        """
        @type other: UInt32
        """
        return self.value == other.value

    def __add__(self, other):
        """
        @type other: UInt32
        """
        return UInt32((self.value + other.value) % 32)


class Value(Expression):
    """"""

    def __init__(self, value):
        """Constructor for Value"""
        self.value = value


class GetInput(Instruction):
    """"""

    def __init__(self, source):
        """Constructor for GetInput"""
        self.source = source

    def get_input(self):
        return self.source.pop(0)


class Store(Instruction):
    """"""

    def __init__(self, e1, e2):
        """Constructor for Store"""
        self.e2 = e2
        self.e1 = e1


class Load(Instruction):
    """"""

    def __init__(self, address):
        """Constructor for Load"""
        self.address = address


class Goto(Instruction):
    """"""

    def __init__(self, pc):
        """Constructor for Goto"""
        self.pc = pc


class Var(Expression):
    """"""

    def __init__(self, var_name):
        """Constructor for Var
        @type var_name: str
        """
        self.var_name = var_name


class IF(Expression):
    """"""

    def __init__(self, e, e1, e2):
        """Constructor for IF
        @type e: Expression
        @type e1: Expression
        @type e2: Expression
        """
        self.e2 = e2
        self.e1 = e1
        self.e = e
        