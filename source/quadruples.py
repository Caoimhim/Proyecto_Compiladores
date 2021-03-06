import tablaConst
from cuboSemantico import *
from memoria import *
from dirFunciones import FuncAttr

m_operand_stack = []
operand_stack = []
operator_stack = []
type_stack = []
instruction_pointer = 2
temporal_counter = 1  # total
temporal_pointer = 1
local_temporal_int = 0
local_temporal_float = 0
local_temporal_char = 0
local_temporal_pointer = 0
total_temporal_int = 0
total_temporal_float = 0
total_temporal_char = 0
total_temporal_pointer = 0
quad_list = []  # quadruplos con IDs
jump_list = []
from_tmp = []
m_quad_list = []  # quadruplos con direcciones
m_from_tmp = []

m_prefix = ''


def get_instruction_pointer():
    '''Returns the instruction pointer'''
    return instruction_pointer

def add_local_temp(t):
    '''Adds to the current count of temporary variables'''
    global local_temporal_int, local_temporal_char, local_temporal_float, total_temporal_char, total_temporal_float, total_temporal_int, local_temporal_pointer, total_temporal_pointer
    if t == 'int':
        local_temporal_int += 1
        total_temporal_int += 1
    if t == 'float':
        local_temporal_float += 1
        total_temporal_float += 1
    if t == 'char':
        local_temporal_char += 1
        total_temporal_char += 1
    if t == 'pointer':
        local_temporal_pointer +=1
        total_temporal_pointer += 1


def get_total_tmps():
    '''Gets the current count of all temporary varuiables as a single tuple
    (ints, floats, chars, pointers)'''
    return (total_temporal_int, total_temporal_float, total_temporal_char, total_temporal_pointer)


def get_local_tmps():
    '''Gets the current count for the current context of local temporary variables as a single tuple
    (ints, floats, chars, pointers)'''
    return (local_temporal_int, local_temporal_float, local_temporal_char, local_temporal_pointer)


# gen_quad 0-4
def gen_goto_main():
    '''Corrects the instruction pointer of the first quad (GOTO main)'''
    global instruction_pointer
    quad_list[0][-1] = instruction_pointer
    m_quad_list[0][-1] = instruction_pointer


# EXPRESSIONS
def gen_quad_exp(valid_operators):
    '''Generates quads for expresssions.
    Must input valid_operators, which are determinded by the parser.
    Stops compilation with an error in case of a type mismatch'''
    global temporal_counter, instruction_pointer
    if operator_stack:
        current_operator = operator_stack[-1]
        if current_operator in valid_operators:
            right_operand = operand_stack.pop()
            right_type = type_stack.pop()
            left_operand = operand_stack.pop()
            left_type = type_stack.pop()
            operator = operator_stack.pop()
            result_type = validateOperation(left_type, right_type, operator)
            if result_type != 'ERROR':
                # IDs
                temp_result = "t" + str(temporal_counter)
                new_quad = [operator, left_operand, right_operand, temp_result]
                quad_list.append(new_quad)
                type_stack.append(result_type)
                operand_stack.append(temp_result)
                # ADDRESSES
                m_temp = get_avail('temporal', result_type)
                m_op = tablaConst.get_oper_code(operator)
                m_right = m_operand_stack.pop()
                m_left = m_operand_stack.pop()
                m_quad = [m_op, m_left, m_right, m_temp]
                m_quad_list.append(m_quad)
                m_operand_stack.append(m_temp)

                instruction_pointer += 1
                temporal_counter += 1
                add_local_temp(result_type)

            else:
                raise TypeError("ERROR: Type mismatch in expression!")


# ASSIGNMENT
def gen_quad_assignment():
    '''generates a quad for an assignment
    Uses latest operations in the operator stack.
    Stops compilation with an error in case of a type mismatch'''
    global temporal_counter, instruction_pointer
    if operator_stack:
        current_operator = operator_stack[-1]
        if current_operator == '=':
            right_operand = operand_stack.pop()
            right_type = type_stack.pop()
            left_operand = operand_stack.pop()
            left_type = type_stack.pop()
            operator = operator_stack.pop()
            result_type = validateOperation(left_type, right_type, operator)
            if result_type != 'ERROR':
                # IDs
                new_quad = [operator, right_operand, '', left_operand]
                quad_list.append(new_quad)
                type_stack.append(result_type)
                # ADDRESS
                m_op = tablaConst.get_oper_code(operator)
                m_right = m_operand_stack.pop()
                m_left = m_operand_stack.pop()
                m_quad = [m_op, m_right, '', m_left]
                m_quad_list.append(m_quad)
                instruction_pointer += 1
            else:
                raise TypeError("ERROR: Type mismatch in assignment:", left_operand, operator, right_operand)


# IF
def gen_quad_if():
    '''Generates quads for the start of an if.
    Performs typechecking for the expression inside the if.
    Uses latest values in the type_stack and operand_stack'''
    global instruction_pointer
    exp_type = type_stack.pop()
    if exp_type != 'int':
        raise TypeError("ERROR Type mismatch!")
    else:
        # ID
        result = operand_stack.pop()
        quad_list.append(['GotoF', result, '', 'pending'])
        jump_list.append(instruction_pointer)
        # Memory
        m_res = m_operand_stack.pop()
        m_op = tablaConst.get_oper_code('GOTOF')
        m_quad_list.append([m_op, m_res, '', 'pending'])

        instruction_pointer += 1


def gen_end_if():
    '''Ends an if that has no else statement.
    Updates the GOTO generated by gen_quad_if()'''
    global instruction_pointer
    start = jump_list.pop()
    start -= 1
    quad_list[start][-1] = instruction_pointer
    m_quad_list[start][-1] = instruction_pointer


def gen_quad_else():
    '''else statement. Updates the GOTO generated by gen_quad_if()'''
    global instruction_pointer
    start = jump_list.pop()
    start -= 1
    # ID
    quad_list[start][-1] = instruction_pointer + 1
    result = quad_list[start][1]
    quad_list.append(['GoTo', '', '', 'pending'])
    # Memory
    m_quad_list[start][-1] = instruction_pointer + 1
    m_res = m_quad_list[start][1]
    m_op = tablaConst.get_oper_code('GOTO')
    m_quad_list.append([m_op, '', '', 'pending'])

    jump_list.append(instruction_pointer)
    instruction_pointer += 1


# WHILE
def gen_while_start():
    '''Called at the start of a while. '''
    global instruction_pointer
    jump_list.append(instruction_pointer)


def gen_while_jmp():
    '''Called after the expression inside the while is solved.
    Generates the GOTO for looping'''
    global instruction_pointer
    exp_type = type_stack.pop()
    if exp_type != 'int':
        print("ERROR Type mismatch!")
        raise TypeError
    else:
        result = operand_stack.pop()
        m_res = m_operand_stack.pop()
        m_op = tablaConst.get_oper_code('GOTOF')
        quad_list.append(['GotoF', result, '', 'pending'])
        m_quad_list.append([m_op, m_res, '', 'pending'])
        jump_list.append(instruction_pointer)
        instruction_pointer += 1


def gen_while_end():
    '''Called when the end of a while is found by the parser.
    Fills the GOTO created during gen_while_jmp()'''
    global instruction_pointer
    exit_jmp = jump_list.pop()
    exit_jmp -= 1
    quad_list[exit_jmp][-1] = instruction_pointer + 1
    m_quad_list[exit_jmp][-1] = instruction_pointer + 1
    w_start = jump_list.pop()
    quad_list.append(['GoTo', '', '', w_start])
    m_op = tablaConst.get_oper_code('GOTO')
    m_quad_list.append([m_op, '', '', w_start])
    instruction_pointer += 1


# FROM
def gen_from_start(s, m):
    '''Called by the parser at the start of a from.
    Adds the starting value to be used for the comparison to a
    from stack.'''
    global instruction_pointer
    exp_type = type_stack.pop()
    if exp_type != 'int':
        print('ERROR Type mismatch!')
        raise TypeError
    from_tmp.append(s)
    from_tmp.append('int')
    m_from_tmp.append(m)  # Memory


def gen_from_jmp():
    '''Called by the parser after the end value of the from statement has been resolved.
    Adds the comparison quad to the quad_list, using the variable saved in
    gen_from_start(). Ends the compilation with an error in case of a type mismatch.'''
    global instruction_pointer, temporal_counter
    start_type = from_tmp.pop()
    start = from_tmp.pop()
    m_start = m_from_tmp.pop()  # Memory
    target = operand_stack.pop()
    target_type = type_stack.pop()
    m_target = m_operand_stack.pop()  # Memory

    result_type = validateOperation(start_type, target_type, '<')

    if result_type != 'int':
        print('ERROR Type mismatch!')
        raise TypeError('type was: ' + result_type)

    temp_result = "t" + str(temporal_counter)
    m_temp = get_avail('temporal', result_type)
    temporal_counter += 1
    add_local_temp(result_type)

    add_local_temp(temp_result)
    quad_list.append(['<', start, target, temp_result])
    m_op = tablaConst.get_oper_code('<')
    m_quad_list.append([m_op, m_start, m_target, m_temp])
    instruction_pointer += 1
    type_stack.append(result_type)
    operand_stack.append(temp_result)
    m_operand_stack.append(m_temp)
    jump_list.append(instruction_pointer)
    quad_list.append(['GoToF', operand_stack.pop(), '', 'pending'])
    m_op = tablaConst.get_oper_code('GOTOF')
    m_quad_list.append([m_op, m_operand_stack.pop(), '', 'pending'])
    instruction_pointer += 1


def gen_from_end():
    '''Called when the from of a from loop is found. pops the jump_list stack to
    create the GOTO quad that causes the loop.'''
    global instruction_pointer
    start = jump_list.pop()
    start -= 1
    quad_list[start][-1] = instruction_pointer + 1
    quad_list.append(['GoTo', '', '', start])
    m_quad_list[start][-1] = instruction_pointer + 1
    m_op = tablaConst.get_oper_code('GOTO')
    m_quad_list.append([m_op, '', '', start])
    instruction_pointer += 1


# READ
def gen_quad_read():
    '''Generates quad for a read() statement'''
    global instruction_pointer
    # ID
    read_operand = operand_stack.pop()
    read_type = type_stack.pop()
    quad_list.append(['READ', '', '', read_operand])
    # Memory
    m_op = tablaConst.get_oper_code('READ')
    m_operand = m_operand_stack.pop()
    m_quad = [m_op, '', '', m_operand]
    m_quad_list.append(m_quad)
    instruction_pointer += 1


# WRITE
def gen_quad_write():
    '''Generates the quad for a write() statement'''
    global instruction_pointer
    # ID
    write_operand = operand_stack.pop()
    write_type = type_stack.pop()
    quad_list.append(['WRITE', '', '', write_operand])
    # Memory
    m_op = tablaConst.get_oper_code('WRITE')
    m_operand = m_operand_stack.pop()
    m_quad = [m_op, '', '', m_operand]
    m_quad_list.append(m_quad)
    instruction_pointer += 1


# RETURN
def gen_quad_return(f):
    '''Generate quads for when a return statement is found.
    Ends the compilation with an error if a type mismatch is found.'''
    global instruction_pointer
    curr_type = type_stack.pop()
    res = operand_stack.pop()

    m_res = m_operand_stack.pop()  # Memory
    

    if curr_type != f[FuncAttr.RETURN_TYPE]:  # catches void function with return
        print("ERROR: Type mismatch in function return!", f[FuncAttr.RETURN_TYPE], "returns", curr_type)
        exit()
    else:
        quad_list.append(['RETURN', '', '', res])
        # Memory
        m_op = tablaConst.get_oper_code('RETURN')
        m_quad_list.append([m_op, '', '', m_res])  # Memory

        instruction_pointer += 1


# FUNCTIONS
def fun_start():
    '''Called by the parser when a new function is found. It resets all temprary
    counters that will be used in the function directory.'''
    global local_temporal_char, local_temporal_float, local_temporal_int, local_temporal_pointer
    local_temporal_int = 0
    local_temporal_float = 0
    local_temporal_char = 0
    local_temporal_pointer = 0


def fun_end():
    '''Called when a function end is found. Generates the ENDFUNC quad.
    Returns a tuple with the temporary context for the function.'''
    global instruction_pointer
    quad_list.append(['ENDFunc', '', '', ''])
    # Memory
    m_op = tablaConst.get_oper_code('ENDFUNC')
    m_quad_list.append([m_op, '', '', ''])
    instruction_pointer += 1
    return (local_temporal_int, local_temporal_float, local_temporal_char, local_temporal_pointer)


def handle_fun_call(fun_id, df, params_count, object_address = ''):
    '''Generates all quads associated with a function call.
    Checks if the calleed function is declared,
    next, validates parameter amount and types, using the latest expressions
    from the operand stack, and finally calls the the GoSub.
    If the function is not void, also assigns the result to a temporary variable.'''
    global instruction_pointer, temporal_counter
    if fun_id not in df:
        raise Exception('Attempted to call undeclared function', fun_id)
    f = df[fun_id]
    signature = (f[FuncAttr.RETURN_TYPE], fun_id, f[FuncAttr.PARAMETERS])
    is_void = signature[0] == 'void'
    # GENERATE ERA
    quad_list.append(['ERA', object_address, '', fun_id])  # TODO: methods?
    # Memory
    m_op = tablaConst.get_oper_code('ERA')
    m_quad_list.append([m_op, object_address, '', fun_id])
    instruction_pointer += 1
    # Verify parameters
    # first, verify correct amount
    if len(signature[2]) != params_count:
        raise Exception("Function call doesn't match function signature")
    # now check types
    p_types = []
    for i in range(params_count):
        p_types.append(type_stack.pop())

    p_types.reverse()
    if tuple(p_types) != signature[2]:
        raise TypeError('Mismatch in expected parameters type')
    # Now, initiate parameters with expression result

    m_op = tablaConst.get_oper_code('PARAMETER')
    quad_stack = []
    m_quad_stack = []
    for i in range(params_count):
        quad_stack.append(['PARAMETER', operand_stack.pop(), '', params_count - i])
        m_quad_stack.append([m_op, m_operand_stack.pop(), '', params_count - i])

    for i in range(params_count):
        q = quad_stack.pop()
        m = m_quad_stack.pop()
        quad_list.append(q)
        m_quad_list.append(m)
        instruction_pointer += 1
    # OK, try to execute
    quad_list.append(['GoSub', fun_id, '', f[FuncAttr.START]])
    # Memory
    m_op = tablaConst.get_oper_code('GOSUB')
    m_quad_list.append([m_op, fun_id, '', f[FuncAttr.START]])
    instruction_pointer += 1
    if not is_void:  # No es una expresion si es void
        m_temp = get_avail('temporal', f[FuncAttr.RETURN_TYPE])
        temp_result = "t" + str(temporal_counter)
        temporal_counter += 1
        add_local_temp(f[FuncAttr.RETURN_TYPE])
        m_op = tablaConst.get_oper_code('=')
        m_quad_list.append([m_op, f[FuncAttr.RETURN_ADDRESS], '', m_temp])
        quad_list.append(['=', '_' + signature[1], '', temp_result])
        instruction_pointer += 1
        type_stack.append(signature[0])
        operand_stack.append(temp_result)
        m_operand_stack.append(m_temp)


def array_indexing1():
    '''Saves the lower bound of an array in the constant table.
    Also prepares the operand and type stack for access.'''
    id = operand_stack.pop()
    m_id =m_operand_stack.pop()
    type = type_stack.pop()
    operator_stack.append('(')
    tablaConst.add_constant(0, 'int')  # in case 0 has not been declared, used for lower lim


def array_verify(lim_s, last_dim, m):
    '''Generates the VERIFY quad, for checking array limits during runtime.'''
    global temporal_counter, instruction_pointer
    # ID
    quad_list.append(['VERIFY', operand_stack[-1], 0, lim_s-1])
    instruction_pointer += 1
    # MEMORY
    m_op = tablaConst.get_oper_code('VERIFY')
    m_inf = tablaConst.get_const_add(0)
    m_sup = tablaConst.get_const_add(lim_s-1)
    m_quad_list.append([m_op, m_operand_stack[-1], m_inf, m_sup])
    if not last_dim:
        # ID
        aux = operand_stack.pop()
        m_aux = m_operand_stack.pop()
        temp_result = "t" + str(temporal_counter)
        temporal_counter += 1
        add_local_temp('int')
        quad_list.append(['*', aux, m, temp_result])
        instruction_pointer += 1
        operand_stack.append(temp_result)
        m_op = tablaConst.get_oper_code('*')
        m_m = tablaConst.get_const_add(m)
        m_res = get_avail('temporal', 'int')
        m_quad_list.append([m_op, m_aux, m_m, m_res])
        m_operand_stack.append(m_res)


def mat_verify(lim_s):
    '''Generates verify quad for matrices, to check bounds during runtime.'''
    global temporal_counter, instruction_pointer
    # ID
    quad_list.append(['VERIFY', operand_stack[-1], 0, lim_s-1])
    instruction_pointer += 1
    # MEMORY
    m_op = tablaConst.get_oper_code('VERIFY')
    m_inf = tablaConst.get_const_add(0)
    m_sup = tablaConst.get_const_add(lim_s-1)
    m_quad_list.append([m_op, m_operand_stack[-1], m_inf, m_sup])

    aux2 = operand_stack.pop()
    aux1 = operand_stack.pop()
    m_aux2 = m_operand_stack.pop()
    m_aux1 = m_operand_stack.pop()
    temp_result = "t" + str(temporal_counter)
    temporal_counter += 1
    add_local_temp('int')
    m_res = get_avail('temporal', 'int')
    m_op = tablaConst.get_oper_code('+')
    quad_list.append(['+', aux1, aux2, temp_result])
    m_quad_list.append([m_op, m_aux1, m_aux2, m_res])
    instruction_pointer += 1
    operand_stack.append(temp_result)
    m_operand_stack.append(m_res)


def dim_end(vir_addr):
    '''Intermediate step of array validation. Creates temporal pointer'''
    global temporal_pointer, instruction_pointer
    aux1 = operand_stack.pop()
    m_aux1 = m_operand_stack.pop()
    tp = "tp" + str(temporal_pointer)
    temporal_pointer += 1
    add_local_temp('pointer')
    m_res = get_avail('temporal', 'pointer')  # TEMPORAL POINTER
    m_op = tablaConst.get_oper_code('+')
    quad_list.append(['+', aux1, vir_addr, tp])
    m_addr = tablaConst.get_const_add(vir_addr)
    m_quad_list.append([m_op, m_aux1, m_addr, m_res])
    instruction_pointer += 1
    operand_stack.append(tp)
    m_operand_stack.append(m_res)
    operator_stack.pop()  # eliminate fake bottom


def print_id_q():
    print("\nQuadruples:")
    for i, q in enumerate(quad_list):
        print(i + 1, q)


def print_mem_q():
    print("\nQuadruples:")
    for i, q in enumerate(m_quad_list):
        print(i + 1, q)


def print_all_q():
    print("\nQuadruples:")
    for i in range(len(quad_list)):
        print(i + 1, str(quad_list[i]) + "\t " + str(m_quad_list[i]))


def set_prefix(p):
    global m_prefix
    m_prefix = p
