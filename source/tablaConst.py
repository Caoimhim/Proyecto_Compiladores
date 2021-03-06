from memoria import *

tabla_const = {}

# lesser number, greater precedence
tabla_oper = {
    '*': 0,
    '/': 1,
    '+': 2,
    '-': 3,
    '<': 4,
    '>': 5,
    '==': 6,
    '!=': 7,
    '>=': 8,
    '<=': 9,
    '&': 10,
    '||': 11,
    '=': 12,
    'RETURN': 13,
    'READ': 14,
    'WRITE': 15,
    'GOTO': 16,
    'GOTOF': 17,
    'GOTOT': 18,
    'ERA': 19,
    'ENDFUNC': 20,
    'PARAMETER': 21,
    'GOSUB': 22,
    'VERIFY': 23
}


def add_constant(value, const_type):
    '''Asks for memory for a new constant and adds it to memory.'''
    value = str(value)
    if value not in tabla_const:
        address = get_avail('constant', const_type)
        tabla_const[value] = [const_type, address]
        # new_constant_log(value)  # log info
    else:  # constante ya existe
        pass
        # print("Constant", value, "already exists in constants table.")


def get_const_add(value):
    '''Gets the virtual memory address of a constant.'''
    if tabla_const:
        return tabla_const[str(value)][1]
    else:
        return 'undefined'


def get_const_type(value):
    '''Gets the type of a given contant'''
    if tabla_const:
        return tabla_const[str(value)][0]
    else:
        return 'undefined'


def get_oper_code(operator):
    '''Gets an opcode given a human-readable operation'''
    return tabla_oper[operator]


def new_constant_log(value):
    print('New entry in constants table:')
    print("Value:", value, "\tType:", tabla_const[value][0], "\tAddress:", tabla_const[value][1], "\n")


def print_const_table():
    if tabla_const:
        print("Constants table")
        for key in tabla_const:
            print("Value:", key, "\tType:", tabla_const[key][0], "\tAddress:", tabla_const[key][1])
        print("---------------------------------------------------------------")
