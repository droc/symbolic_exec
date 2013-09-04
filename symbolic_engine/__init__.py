try:
    #noinspection PyUnresolvedReferences
    from exceptions import Exception, NotImplementedError
except Exception:
    pass

class UInt32(object):
    def __init__(self, value):
        """
        @type value: int
        """
        assert type(value) == int or type(value) == long, "UInt32 expects int, received %s" % type(value)
        assert value < (2 ** 32), "Initial value of UInt32 can't be greater than word size (32 bits)"
        self.value = value

    def __div__(self, other):
        """
        @type other: UInt32
        """
        return UInt32(self.value / other.value)

    def __divmod__(self, other):
        """
        @type other: UInt32
        """
        return UInt32(self.value % other.value)

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


    def __mul__(self, other):
        return UInt32((self.value * other.value) % 32)


    def __str__(self):
        return "%d" % (self.value)
        #return "<%s 0x%08x>" % (self.__class__.__name__, self.value)

    def isAligned(self):
        return (self.value % 32) == 0


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
        self.__contents = [Value(0)] * self.size
        self.__tainting = [0] * self.size

    def validate_address(self, address):
        """
        @type address: int
        """
        if not self.base_address <= address < (self.base_address + self.size):
            raise Exception("address %s outside page" % address)

    def set_value(self, address, value):
        """
        @type address: int
        @type value: Value
        """
        self.validate_address(address)
        self.__contents[address - self.base_address] = value

    def get_value(self, address):
        """
        @type address: int
        """
        self.validate_address(address)
        return self.__contents[address - self.base_address]

    def get_taint(self, address):
        return self.__tainting[address - self.base_address]

    def set_taint(self, address, taint):
        """
        @type address: int
        @type taint: int
        """
        self.__tainting[address - self.base_address] = taint


class Memory(object):
    def __init__(self, page_size=None):
        """
        @type page_size: int
        """
        if page_size is None: page_size = 1024 * 4
        self.page_size = page_size
        self.pages = {}

    def set_value(self, address, value):
        """
        @type address: UInt32
        @type value: Value
        """
        page = self.get_page(address)
        page.set_value(address.value, value)

    def get_page(self, v1):
        """
        @type v1: UInt32
        @rtype MemoryPage
        """
        page_nr = v1.value / self.page_size
        if not page_nr in self.pages:
            self.pages[page_nr] = MemoryPage(self.page_size, (page_nr * self.page_size))
        return self.pages[page_nr]

    def get_page_numbers(self):
        return len(self.pages)

    def get_value(self, mem_pos):
        """
        @type mem_pos: UInt32
        """
        page = self.get_page(mem_pos)
        return page.get_value(mem_pos.value)

    def get_taint(self, address):
        """
        @type address: UInt32
        """
        page = self.get_page(address)
        assert isinstance(page, MemoryPage)
        return page.get_taint(address.value)

    def set_taint(self, address, taint):
        """
        @type address: UInt32
        @type taint: int
        """
        page = self.get_page(address)
        assert isinstance(page, MemoryPage)
        page.set_taint(address.value, int(taint))


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
        return self.memory.get_value(address)

    def resolve_name(self, name):
        """
        @rtype Value
        """
        return self.variables[name]

    def copy(self):
        return Context(self.memory, self.variables, self.pc, self.program)

    def set_mem_value(self, v1, v2):
        """
        @type v1: UInt32
        @type v2: Value
        """
        self.memory.set_value(v1, v2)

    def get_mem_address_taint(self, address):
        """
        @type address: UInt32
        """
        return bool(self.memory.get_taint(address))

    def set_mem_address_taint(self, address, is_tainted):
        """
        @type address: UInt32
        @type is_tainted: bool
        """
        self.memory.set_taint(address, int(is_tainted))


class Assign(Instruction):
    def __init__(self, var_name, expression):
        """Constructor for Assign
        @type var_name: str
        @type expression: Expression
        """
        self.expression = expression
        self.var_name = var_name

    def __str__(self):
        return "%s := %s" % (self.var_name, str(self.expression))


class Program(object):
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


class Expression(Instruction):
    pass


class BinOp(Expression):
    SYM = "ERROR"

    def __init__(self, left, right):
        """
        @param left: l
        @param right: r
        @type left: Expression
        @type right: Expression
        """
        self.right = right
        self.left = left

    def __str__(self):
        return "(%s) %s (%s)" % (str(self.left), self.SYM, str(self.right))


class AddOp(BinOp):
    SYM = "+"


class MulOp(BinOp):
    SYM = "*"


class SubOp(BinOp):
    SYM = "-"


class EQ(BinOp):
    SYM = "=="


class GT(BinOp):
    SYM = ">"


class TaintPolicy(object):
    def input_policy(self, src):
        raise NotImplementedError

    def goto_check(self, v1):
        """
        @type v1: Value
        """
        raise NotImplementedError

    def tainted_address(self, address, value):
        """

        @param address: memory address
        @param value: value in that address
        @type address: Value
        @type value: Value
        @return: bool
        """
        raise NotImplementedError


class AttackException(Exception):
    pass


class TaintCheckHandler(object):
    def handle_goto(self, pc, instr):
        pass


class DefaultTaintCheckHandler(TaintCheckHandler):
    def handle_goto(self, pc, instr):
        raise AttackException("Probable attack detected, instruction %s at pc %s" % (pc, instr))


class DefaultTaintPolicy(TaintPolicy):
    def input_policy(self, src):
        return True

    def goto_check(self, v1):
        """
        @type v1: Value
        """
        return not v1.isTainted()

    def tainted_address(self, address, value):
        return address.isTainted()


class BaseInterpreter(object):
    def __init__(self, taint_policy, taint_check_handler, print_statements=False):
        """
        @type taint_policy: TaintPolicy
        @type taint_check_handler: TaintCheckHandler
        """
        self.rules = {
            'Assign': self.assign_rule,
            'Store': self.store_rule,
            'Goto': self.goto_rule,
            'IF': self.eval_if
        }
        self.taint_policy = taint_policy
        self.taint_check_handler = taint_check_handler
        self.print_statements = print_statements

    def eval_if(self, context):
        """
        @type context: Context
        """
        instr = context.current_instr()
        assert isinstance(instr, IF)
        e = instr.e
        e1 = instr.e1
        e2 = instr.e2
        cond = self.eval_expression(e, context)
        if cond.value == UInt32(1):
            v1 = self.eval_expression(e1, context)
        elif cond.value == UInt32(0):
            v1 = self.eval_expression(e2, context)
        else:
            raise Exception("Invalid value: expected boolean (0 or 1)")
        context.pc = v1.value
        return context

    def goto_rule(self, context):
        instr = context.current_instr()
        assert isinstance(instr, Goto)
        v1 = self.eval_expression(instr.pc, context)
        if not self.taint_policy.goto_check(v1):
            self.taint_check_handler.handle_goto(context.pc, instr)
        context.pc = v1.value
        return context

    def store_rule(self, context):
        """

        @param context: context
        @type context: Context

        @return:
        """
        instr = context.current_instr()
        assert isinstance(instr, Store)
        v1 = self.eval_expression(instr.address, context)
        v2 = self.eval_expression(instr.value, context)
        context.pc += UInt32(1)
        context.set_mem_value(v1.value, v2)
        context.set_mem_address_taint(v1.value, self.taint_policy.tainted_address(v1, v2)) # v1.isTainted()
        return context

    def assign_rule(self, context):
        """
        @type context: Context
        """
        instr = context.current_instr()
        assert isinstance(instr, Assign)
        context.variables[instr.var_name] = self.eval_expression(instr.expression, context)
        context.pc += UInt32(1)
        return context

    def run(self, context):
        """
        Fetch-execute loop
        @type context: Context
        """
        next_instr = context.current_instr()
        assert isinstance(next_instr, Instruction)
        while next_instr:
            if self.print_statements:
                print context.pc.value, ": ", str(next_instr)
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
        # TODO: the rest of the binary operations (MUL, DIV, SUB, etc.)
        name = expression.get_name()
        left_value = self.eval_expression(expression.left, context)
        right_value = self.eval_expression(expression.right, context)
        if not (isinstance(left_value, Value) and isinstance(right_value, Value)):
            return expression.__class__(self.eval_expression(left_value, context),
                self.eval_expression(right_value, context))
        else:
            if name == 'AddOp':
                inner_value = left_value.value + right_value.value
            elif name == 'MulOp':
                inner_value = left_value.value * right_value.value
            elif name == 'SubOp':
                inner_value = left_value.value - right_value.value
            elif name == 'EQ':
                inner_value = 1 if left_value.value == right_value.value else 0
            elif name == 'GT':
                inner_value = 1 if left_value.value > right_value.value else 0
            else:
                raise Exception("Operation not implemented")
            return Value(inner_value, right_value.isTainted() or left_value.isTainted())

    def eval_expression(self, expression, context):
        name = expression.get_name()
        binops = set(['AddOp', 'MulOp', 'SubOp', 'EQ', 'GT'])
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

    def eval_value(self, expression, _):
        """
        @type expression: Value
        @rtype UInt32
        """
        return expression

    def eval_input(self, expression, _):
        """
        @type expression: GetInput
        """
        return Value(expression.get_input(), tainted=self.taint_policy.input_policy(expression.input_name))

    def eval_load(self, expression, context):
        """
        @type expression: Load
        @type context: Context
        """
        return context.get_mem_value(self.eval_expression(expression.address, context).value)


class Interpreter(BaseInterpreter):
    pass


class SymExpression(object):
    pass


class _SymTrue(SymExpression):
    def __str__(self):
        return "True"


class _SymFalse(SymExpression):
    def __str__(self):
        return "False"

SymTrue = _SymTrue()
SymFalse = _SymFalse()

class SymInput(Expression):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class And(SymExpression):
    def __init__(self, left, right):
        self.right = right
        self.left = left

    def __str__(self):
        return "%s AND %s" % (str(self.right), str(self.left))


class IdProvider(object):
    def __init__(self):
        self.base_name = "s"
        self.__last_id = 0

    def get_next_name(self):
        self.__last_id += 1
        return "%s_%d" % (self.base_name, self.__last_id)


class ConcolicInterpreter(BaseInterpreter):
    def __init__(self, taint_policy, taint_check_handler, id_provider, print_statements=False):
        super(ConcolicInterpreter, self).__init__(taint_policy, taint_check_handler, print_statements)
        self.constraints = SymTrue
        self.id_provider = id_provider

    def eval_input(self, expression, context):
        return SymInput(self.id_provider.get_next_name())

    def eval_if(self, context):
        if_instr = context.current_instr()
        assert isinstance(if_instr, IF)
        e = if_instr.e
        e1 = if_instr.e1
        #e2 = if_instr.e2
        e_v = self.eval_expression(e, context)
        self.constraints = And(self.constraints, e_v)
        e1_v = self.eval_expression(e1, context)
        context.pc = e1_v.value
        return context

    def eval_expression(self, expression, context):
        name = expression.get_name()
        if name == "SymInput":
            return expression
        return super(ConcolicInterpreter, self).eval_expression(expression, context)


class Value(Expression):
    """"""

    def __init__(self, value, tainted=False):
        """Constructor for Value"""
        self.value = value
        self.tainted = tainted

    def isTainted(self):
        return self.tainted

    def __str__(self):
        return str(self.value)


class GetInput(Expression):
    """"""

    def __init__(self, source, input_name="default"):
        """Constructor for GetInput"""
        self.source = source
        self.input_name = input_name

    def get_input(self):
        return self.source.pop(0)

    def __str__(self):
        return "get_input()"


class AlignmentException(Exception):
    pass


class Store(Instruction):
    """"""

    def __init__(self, address, value):
        """Constructor for Store
        @type address: Expression
        @type value: Expression
        """
        self.address = address
        self.value = value


class Load(Expression):
    """"""

    def __init__(self, address):
        """Constructor for Load
        @type address: Expression
        """
        self.address = address


class Goto(Instruction):
    """"""

    def __init__(self, pc):
        """Constructor for Goto
        @type pc: Expression
        """
        self.pc = pc


class Var(Expression):
    """"""

    def __init__(self, var_name):
        """Constructor for Var
        @type var_name: str
        """
        self.var_name = var_name

    def __str__(self):
        return "%s" % (self.var_name)


class IF(Expression):
    """"""

    def __init__(self, e, e1, e2):
        """Constructor for IF
        @param e: An expression to be evaluated for truth value. Must evaluate to either 0 (false) or 1 (true)
        @param e1: If e is true (1), the "pc" will take the value resulting from evaluating this expression
        @param e2: If e is false (0), the "pc" will take the value resulting from evaluating this expression
        @type e: Expression
        @type e1: Expression
        @type e2: Expression
        """
        self.e2 = e2
        self.e1 = e1
        self.e = e

    def __str__(self):
        return "if %s then goto %s else goto %s" % (self.e, self.e1, self.e2)