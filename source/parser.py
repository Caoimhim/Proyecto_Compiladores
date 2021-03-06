from distutils import dir_util
import ply.yacc as yacc
import dirFunciones
import tablaVars
import tablaConst
from quadruples import *
from tablaObjetos import *
from lexer import tokens
import sys
from math import prod

curr_fun_type = ''
curr_var_type = ''
curr_var_id = ''
curr_scope = ''
curr_operand_type = ''
curr_from_var = ''
scope_global = ''
in_object = False
curr_class = None
parameter_stack = []
has_return = False
curr_array = ''


# PROGRAMA
def p_program(p):
    """program : PROGRAM ini_quads ID store_program SEMI prog1 prog2 prog3 fill_goto_main main count_temps"""
    tablaVars.print_var_table()
    print_obj_table()
    tablaConst.print_const_table()
    print("\nOperand stack:\t", operand_stack)
    print("Type stack:\t", type_stack)
    print("Operator stack:\t", operator_stack)
    # print(dirFunciones.directorio_funciones)
    print("\nQuadruples:")
    for i, q in enumerate(quad_list):
        print(i + 1, q)
    print("\nQuadruples: (machine)")
    f = open("intermediate.out", "w")

    # write constant table to output file
    constant_string = 'c'
    for key in tablaConst.tabla_const:
        constant_string += ',' + str(key) + ',' + str(tablaConst.tabla_const[key][1])
    constant_string += '\n'

    dir_fun_string = 'f'
    for key in dirFunciones.directorio_funciones:
        fun = dirFunciones.directorio_funciones[key]
        vt = fun[dirFunciones.FuncAttr.VAR_TABLE]
        int_count = 0
        float_count = 0
        char_count = 0
        object_count = 0
        for v in vt:
            v = vt[v]
            a = v[tablaVars.V.IS_ARRAY]
            t = v[tablaVars.V.DATATYPE]
            is_object = v[tablaVars.V.VAR_KIND] == 'object'
            size = 1
            if a or is_object:
                size = prod(v[tablaVars.V.DIMS])
            if t == 'int':
                int_count += 1 * size
            elif t == 'float':
                float_count += 1 * size
            elif t == 'char':
                char_count += 1 * size
            elif is_object:
                object_count += 1 * size

        tmps = fun[dirFunciones.FuncAttr.TEMP_AMOUNT]
        dir_fun_string += ',' + key + ',' + str(int_count) + ',' + str(float_count) + ',' + str(char_count) + ','  + str(object_count)
        dir_fun_string += ',' + str(tmps[0]) + ',' + str(tmps[1]) + ',' + str(tmps[2]) + ',' + str(tmps[3]) + ',' + str(fun[FuncAttr.RETURN_ADDRESS])

    dir_fun_string += '\n'

    f.write(constant_string)
    f.write(dir_fun_string)
    for i, q in enumerate(m_quad_list):
        print(i + 1, q)
        f.write(str(q[0]) + ',' +
                str(q[1]) + ',' +
                str(q[2]) + ',' +
                str(q[3]) + '\n')
    f.close()
    # print("\nInstruction Pointer:", get_instruction_pointer())
    p[0] = "\nInput is a valid program.\n"


def p_count_temps(p):
    """count_temps :"""
    f = dirFunciones.directorio_funciones[scope_global]
    f[dirFunciones.FuncAttr.TEMP_AMOUNT] = get_local_tmps()
    type_stack.clear()


def p_ini_quads(p):
    """ini_quads :"""
    quad_list.append(['GOTO', '', '', 'main'])
    m_op = tablaConst.get_oper_code('GOTO')
    m_quad_list.append([m_op, '', '', 'main'])


def p_fill_goto_main(p):
    """fill_goto_main :"""
    gen_goto_main()
    global curr_scope
    curr_scope = scope_global
    reset_temp()
    fun_start()


def p_store_program(p):
    """store_program :"""
    dirFunciones.add_function(p[-1], p[-3], p[-3])
    global curr_scope, scope_global
    curr_scope = p[-1]
    scope_global = p[-1]


def p_prog1(p):
    """prog1 : class
             | empty"""


def p_prog2(p):
    """prog2 : vars
             | empty"""


def p_prog3(p):
    """prog3 : function
             | empty"""


# CLASS
def p_class(p):
    """class : CLASS ID store_object class1 LB class2 class3 RB SEMI exit_class class4"""


def p_store_object(p):
    """store_object :"""
    global in_object, curr_class
    curr_class = p[-1]
    add_object(p[-1])  # add object to object table
    in_object = True  # now inside class definition


def p_exit_class(p):
    """exit_class :"""
    global curr_scope, in_object, curr_class
    curr_scope = scope_global  # return to global scope after class definitions
    in_object = False
    curr_class = None


def p_class1(p):
    """class1 : INHERITS ID validate_inheritance
              | empty"""


def p_validate_inheritance(p):
    """validate_inheritance :"""
    global curr_class
    validate_class(p[-1])  # make sure parent class is defined
    curr_class = p[-4]
    assign_parent(curr_class, p[-1])


def p_class2(p):
    """class2 : attrs
              | empty"""


def p_class3(p):
    """class3 : mthds
              | empty"""


def p_class4(p):
    """class4 : class
              | empty"""


def p_attrs(p):
    """attrs : ATTRIBUTES attrs1"""


def p_attrs1(p):
    """attrs1 : tipo COLON lista_ids SEMI attrs2"""


def p_attrs2(p):
    """attrs2 : attrs1
              | empty"""


def p_mthds(p):
    """mthds : METHODS function"""


# VARS
def p_vars(p):
    """vars : VARIABLES LB attrs1 RB"""


def p_tipo(p):
    """tipo : INT
            | FLOAT
            | CHAR
            | ID"""
    global curr_var_type
    curr_var_type = p[1]


def p_lista_ids(p):
    """lista_ids : ID store_id list1 list2"""


def p_store_id(p):
    """store_id :"""
    global curr_var_id
    curr_var_id = p[-1]
    if in_object:  # id read is an attribute within a class
        add_attribute(curr_class, curr_var_id, curr_var_type)
    else:
        if curr_var_type not in ['int', 'float', 'char']:  # id read is an object
            tablaVars.add_variable(curr_var_id, curr_var_type, "object", curr_scope)
            tablaVars.instantiate_obj(curr_var_id, curr_var_type, curr_scope)
        else:
            tablaVars.add_variable(curr_var_id, curr_var_type, "variable", curr_scope)


def p_list1(p):
    """list1 : LS found_array CTEI store_dim RS arr_end
             | LS found_array CTEI store_dim COMMA CTEI store_dim RS mat_end
             | empty"""


def p_found_array(p):
    """found_array :"""
    global curr_array
    curr_array = p[-3]
    tablaVars.set_array(curr_array, curr_scope)


def p_store_dim(p):
    """store_dim :"""
    tablaVars.set_dim(curr_array, curr_scope, p[-1])


def p_arr_end(p):
    """arr_end :"""
    tablaVars.arr_end(curr_array, curr_scope, scope_global)


def p_mat_end(p):
    """mat_end :"""
    tablaVars.mat_end(curr_array, curr_scope, scope_global)


def p_list2(p):
    """list2 : COMMA lista_ids
             | empty"""


# MAIN
def p_main(p):
    """main : MAIN LP RP LB main1 RB"""


def p_main1(p):
    """main1 : statement
             | empty"""


# FUNCTION
def p_function(p):
    """function : tipo_retorno FUNCTION ID store_function LP func1 RP LB func2 fun_start statement RB fun_end func3"""
    # func1 = parameters
    # func2 = variables
    # statement = body


def p_fun_start(p):
    """fun_start :"""
    if curr_fun_type != 'void':
        return_address = tablaVars.add_variable('_' + curr_scope, curr_fun_type, 'variable', scope_global)
    else:
        return_address = -1
    dirFunciones.fun_start(curr_scope, get_instruction_pointer(), return_address)
    fun_start()


def p_fun_end(p):
    """fun_end :"""
    lt = fun_end()
    dirFunciones.fun_end(curr_scope, lt)
    if has_return is False and curr_fun_type != 'void':
        print("Error: non-void function", curr_scope, "has no return statement.")
        exit()
    # at end of function, reset temporal and local addresses
    reset_temp()
    reset_local()


def p_store_function(p):
    """store_function :"""
    global curr_scope, has_return
    if in_object:  # id read is a method within a class
        add_method(curr_class, p[-1], curr_fun_type)
        dirFunciones.add_function(p[-1], curr_fun_type, "method")
    else:
        dirFunciones.add_function(p[-1], curr_fun_type, p[-2])  # add function to directory
    curr_scope = p[-1]  # update current scope
    has_return = False


def p_func1(p):
    """func1 : params
             | empty"""


def p_func2(p):
    """func2 : vars
             | empty"""


def p_func3(p):
    """func3 : function
             | empty"""


def p_tipo_param(p):
    """tipo_param : INT
                  | FLOAT
                  | CHAR"""
    global curr_var_type
    curr_var_type = p[1]  # save variable/parameter type


def p_params(p):
    """params : ID COLON tipo_param store_param par1 sign_function"""


def p_sign_function(p):
    """sign_function : """
    dirFunciones.sign_function(curr_scope)


def p_store_param(p):
    """store_param :"""
    tablaVars.add_variable(p[-3], curr_var_type, "parameter", curr_scope)  # save parameter as local variable


def p_par1(p):
    """par1 : COMMA params
            | empty"""


def p_tipo_retorno(p):
    """tipo_retorno : INT
                    | FLOAT
                    | CHAR
                    | VOID"""
    global curr_fun_type
    curr_fun_type = p[1]  # save function type
    p[0] = p[1]


# STATEMENT
def p_statement(p):
    """statement : assignment SEMI stmt1
                 | void_call SEMI stmt1
                 | read SEMI stmt1
                 | write SEMI stmt1
                 | if_st stmt1
                 | while_st stmt1
                 | from_st stmt1
                 | return_st SEMI stmt1"""


def p_stmt1(p):
    """stmt1 : statement
             | empty"""


# ASSIGNMENT
def p_assignment(p):
    """assignment : var EQ store_operator expression gen_quad5"""
    p[0] = p[1]


def p_gen_quad5(p):
    """gen_quad5 :"""
    gen_quad_assignment()


def p_var(p):
    """var : ID store_operand var_dim
           | ID DOT ID store_attr"""
    p[0] = p[1]


# LEFT HERE
def p_var_dim(p):
    """var_dim : verify_dim LS expression gen_verify1 RS end_arr
               | verify_dim LS expression gen_verify2 COMMA expression gen_verify3 RS end_mat
               | empty"""


def p_verify_dim(p):
    """verify_dim :"""
    if tablaVars.verify_dim(p[-2], curr_scope, scope_global):
        array_indexing1()
    elif not tablaVars.verify_dim(p[-2], curr_scope, scope_global):
        print("ERROR: variable", p[-2], "is not an array")
        exit()
    p[0] = p[-2]


def p_gen_verify1(p):
    """gen_verify1 :"""
    if type_stack[-1] != 'int':
        print("ERROR array indexing expression must be of type INT", p[-3])
        exit()
    lim_s = tablaVars.get_arr_dim(p[-3], 0, curr_scope, scope_global)
    tablaConst.add_constant(lim_s, 'int')
    tablaConst.add_constant(lim_s-1, 'int')
    array_verify(lim_s, True, '')


def p_gen_verify2(p):
    """gen_verify2 :"""
    if type_stack[-1] != 'int':
        print("ERROR array indexing expression must be of type INT", p[-3])
        exit()
    lim_s = tablaVars.get_arr_dim(p[-3], 0, curr_scope, scope_global)
    m = tablaVars.get_arr_m(p[-3], curr_scope, scope_global)
    tablaConst.add_constant(lim_s, 'int')
    tablaConst.add_constant(lim_s - 1, 'int')
    tablaConst.add_constant(m, 'int')
    array_verify(lim_s, False, m)


def p_gen_verify3(p):
    """gen_verify3 :"""
    if type_stack[-1] != 'int':
        print("ERROR array indexing expression must be of type INT", p[-6])
        exit()
    lim_s = tablaVars.get_arr_dim(p[-6], 1, curr_scope, scope_global)
    tablaConst.add_constant(lim_s, 'int')
    tablaConst.add_constant(lim_s - 1, 'int')
    mat_verify(lim_s)


def p_end_arr(p):
    """end_arr :"""
    addr = dirFunciones.get_var_address(p[-5], curr_scope, scope_global)
    tablaConst.add_constant(addr, 'int')
    dim_end(addr)


def p_end_mat(p):
    """end_mat :"""
    addr = dirFunciones.get_var_address(p[-8], curr_scope, scope_global)
    tablaConst.add_constant(addr, 'int')
    dim_end(addr)


def p_store_attr(p):
    """store_attr :"""
    global curr_operand_type
    name = str(p[-3] + p[-2] + p[-1])
    operand_stack.append(name)
    m_operand_stack.append(dirFunciones.get_var_address(name, curr_scope, scope_global, curr_class))
    curr_operand_type = dirFunciones.get_var_type(name, curr_scope, curr_class)
    type_stack.append(curr_operand_type)


def p_store_operand(p):
    """store_operand :"""
    global curr_operand_type
    operand_stack.append(p[-1])
    m_operand_stack.append(dirFunciones.get_var_address(p[-1], curr_scope, scope_global, curr_class))
    curr_operand_type = dirFunciones.get_var_type(p[-1], curr_scope, curr_class)
    type_stack.append(curr_operand_type)


# VOID CALL
def p_void_call(p):
    """void_call : ID call1 params_init LP call2 RP
                 | ID call1 params_init LP RP"""
    if p[2] is None: # Regular function call
        if dirFunciones.directorio_funciones[p[1]][FuncAttr.IS_GLOBAL] == 'method':
            print("ERROR: cannot call class method", p[1], "as standalone function.")
            exit()
        handle_fun_call(p[1], dirFunciones.get_dir_funciones(), parameter_stack.pop())
    else: # Method call
        addr = dirFunciones.get_var_address(p[1], curr_scope, scope_global, curr_class)
        handle_fun_call(p[2], dirFunciones.get_dir_funciones(), parameter_stack.pop(), addr)


def p_params_init(p):
    """params_init :"""
    parameter_stack.append(0)


def p_call1(p):
    """call1 : DOT ID found_method
             | empty"""
    try:
        p[0] = p[2]
    except IndexError:
        p[0] = None


def p_found_method(p):
    """found_method :"""
    obj = dirFunciones.get_var_type(p[-3], curr_scope, curr_class)
    validate_method(obj, p[-1])


def p_call2(p):
    """call2 : expression call3"""
    parameter_stack[-1] += 1


def p_call3(p):
    """call3 : COMMA call2
             | empty"""


# READ
def p_read(p):
    """read : READ LP var RP"""
    gen_quad_read()


# WRITE
def p_write(p):
    """write : WRITE LP write1 RP"""


def p_write1(p):
    """write1 : expression gen_quad_8 write2
              | CTES store_string gen_quad_8 write2"""


def p_store_string(p):
    """store_string :"""
    type_stack.append('string')
    operand_stack.append(p[-1])
    tablaConst.add_constant(p[-1], 'string')
    m_operand_stack.append(tablaConst.get_const_add(p[-1]))


def p_gen_quad_8(p):
    """gen_quad_8 :"""
    gen_quad_write()


def p_write2(p):
    """write2 : COMMA write1
              | empty"""


# IF
def p_if_st(p):
    """if_st : IF LP expression RP gen_quad_6 THEN  LB statement RB if1"""


def p_gen_quad_6(p):
    """gen_quad_6 : """
    gen_quad_if()


def p_if1(p):
    """if1 : ELSE LB gen_quad_else statement RB gen_quad_fi
           | gen_quad_fi """


def p_gen_quad_fi(p):
    """gen_quad_fi : """
    gen_end_if()


def p_gen_quad_else(p):
    """gen_quad_else : """
    gen_quad_else()


# WHILE
def p_while_st(p):
    """while_st : WHILE LP gen_while_start expression gen_while_jmp RP DO LB statement RB gen_while_end"""


def p_while_start(p):
    """gen_while_start : """
    gen_while_start()


def p_while_jmp(p):
    """gen_while_jmp : """
    gen_while_jmp()


def p_while_end(p):
    """gen_while_end : """
    gen_while_end()


# FROM
def p_from_st(p):
    """from_st : FROM assignment gen_from_start UNTIL expression gen_from_jmp DO LB statement RB gen_from_end"""


def p_gen_from_start(p):
    """gen_from_start : """
    global curr_from_var
    curr_from_var = p[-1]
    curr_from_m = dirFunciones.get_var_address(curr_from_var, curr_scope, scope_global, curr_class)
    gen_from_start(curr_from_var, curr_from_m)


def p_gen_from_jmp(p):
    """gen_from_jmp : """
    gen_from_jmp()


def p_gen_from_end(p):
    """gen_from_end : """
    gen_from_end()


# RETURN
def p_return_st(p):
    """return_st : RETURN LP expression gen_quad_9 RP"""
    global has_return
    has_return = True


def p_gen_quad_9(p):
    """gen_quad_9 :"""
    gen_quad_return(dirFunciones.directorio_funciones[curr_scope])


# EXPRESSION
def p_expression(p):
    """expression : exp gen_quad4 OR store_operator expression
                  | exp gen_quad4"""


def p_gen_quad4(p):
    """gen_quad4 :"""
    valid_operators = ['||']
    gen_quad_exp(valid_operators)


def p_exp(p):
    """exp : k_exp gen_quad3 AND store_operator exp
           | k_exp gen_quad3"""


def p_gen_quad3(p):
    """gen_quad3 :"""
    valid_operators = ['&']
    gen_quad_exp(valid_operators)


def p_k_exp(p):
    """k_exp : m_exp gen_quad2
             | m_exp gen_quad2 LT store_operator k_exp
             | m_exp gen_quad2 GT store_operator k_exp
             | m_exp gen_quad2 COMP store_operator k_exp
             | m_exp gen_quad2 NE store_operator k_exp
             | m_exp gen_quad2 GTE store_operator k_exp
             | m_exp gen_quad2 LTE store_operator k_exp"""


def p_gen_quad2(p):
    """gen_quad2 :"""
    valid_operators = ['<', '>', '==', '!=', '>=', '<=']
    gen_quad_exp(valid_operators)


def p_m_exp(p):
    """m_exp : term gen_quad1
             | term gen_quad1 PLUS store_operator m_exp
             | term gen_quad1 MIN store_operator m_exp"""


def p_gen_quad1(p):
    """gen_quad1 :"""
    valid_operators = ['+', '-']
    gen_quad_exp(valid_operators)


def p_term(p):
    """term : fact gen_quad0
            | fact gen_quad0 MUL store_operator term
            | fact gen_quad0 DIV store_operator term"""


def p_gen_quad0(p):
    """gen_quad0 :"""
    valid_operators = ['*', '/']
    gen_quad_exp(valid_operators)


def p_store_operator(p):
    """store_operator :"""
    operator_stack.append(p[-1])


def p_fact(p):
    """fact : LP store_operator expression RP paren_end
            | void_call
            | var_cte
            | var"""


def p_paren_end(p):
    """paren_end :"""
    current_operator = operator_stack[-1]
    if current_operator == '(':
        operator_stack.pop()


def p_var_cte(p):
    """var_cte : CTEI store_int
               | CTEF store_float
               | CTEC store_char"""


def p_store_int(p):
    """store_int :"""
    operand_stack.append(p[-1])
    type_stack.append('int')
    tablaConst.add_constant(p[-1], 'int')
    m_operand_stack.append(tablaConst.get_const_add(p[-1]))


def p_store_float(p):
    """store_float :"""
    operand_stack.append(p[-1])
    type_stack.append('float')
    tablaConst.add_constant(p[-1], 'float')
    m_operand_stack.append(tablaConst.get_const_add(p[-1]))


def p_store_char(p):
    """store_char :"""
    operand_stack.append(p[-1])
    type_stack.append('char')
    tablaConst.add_constant(p[-1], 'char')
    m_operand_stack.append(tablaConst.get_const_add(p[-1]))


# Error rule for syntax errors
def p_error(p):
    if p:
        print("Syntax error in input! ", p)
        exit()
    else:
        print("Syntax error at EOF!")


def p_empty(p):
    """empty :"""
    pass


def main():
    # Build the parser
    parser = yacc.yacc()
    file = open(sys.argv[1]).read()
    result = yacc.parse(file)
    print(result)


if __name__ == '__main__':
    main()
