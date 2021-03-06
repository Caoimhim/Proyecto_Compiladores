import sys
import pyparsing as pp
import vm_memory as m

TRUE = 1
FALSE = 0
ip = 0

def get_ip():
    global ip
    return ip + 1

def set_ip(target):
    global ip
    ip = target - 1

def ip_continue():
    global ip
    ip += 1

def mult(lo, ro, t):
    lo = m.memory_read(int(lo))
    ro = m.memory_read(int(ro))
    res = lo * ro
    m.memory_write(res, t)
    ip_continue()

def div(lo, ro, t):
    lo = m.memory_read(int(lo))
    ro = m.memory_read(int(ro))
    res = lo / ro
    m.memory_write(res, t)
    ip_continue()

def add(lo, ro, t):
    lo = m.memory_read(int(lo))
    ro = m.memory_read(int(ro))
    res = lo + ro
    m.memory_write(res, t)
    ip_continue()

def subtract(lo, ro, t):
    lo = m.memory_read(int(lo))
    ro = m.memory_read(int(ro))
    res = lo - ro
    m.memory_write(res, t)
    ip_continue()

def lt(lo, ro, t):
    lo = m.memory_read(int(lo))
    ro = m.memory_read(int(ro))
    res = lo < ro
    if res:
        res = TRUE
    else:
        res = FALSE
    m.memory_write(res, t)
    ip_continue()

def gt(lo, ro, t):
    lo = m.memory_read(int(lo))
    ro = m.memory_read(int(ro))
    res = lo > ro
    if res:
        res = TRUE
    else:
        res = FALSE
    m.memory_write(res, t)
    ip_continue()

def equal(lo, ro, t):
    lo = m.memory_read(int(lo))
    ro = m.memory_read(int(ro))
    res = lo == ro
    if res:
        res = TRUE
    else:
        res = FALSE
    m.memory_write(res, t)
    ip_continue()

def not_equal(lo, ro, t):
    lo = m.memory_read(int(lo))
    ro = m.memory_read(int(ro))
    res = lo != ro
    if res:
        res = TRUE
    else:
        res = FALSE
    m.memory_write(res, t)
    ip_continue()

def gte(lo, ro, t):
    lo = m.memory_read(int(lo))
    ro = m.memory_read(int(ro))
    res = lo >= ro
    if res:
        res = TRUE
    else:
        res = FALSE
    m.memory_write(res, t)
    ip_continue()

def lte(lo, ro, t):
    lo = m.memory_read(int(lo))
    ro = m.memory_read(int(ro))
    res = lo <= ro
    if res:
        res = TRUE
    else:
        res = FALSE
    m.memory_write(res, t)
    ip_continue()

def and_et(lo, ro, t):
    lo = m.memory_read(int(lo))
    ro = m.memory_read(int(ro))
    res = (lo > 0) and (ro > 0)
    if res:
        res = TRUE
    else:
        res = FALSE
    m.memory_write(res, t)
    ip_continue()

def or_vel(lo, ro, t):
    lo = m.memory_read(int(lo))
    ro = m.memory_read(int(ro))
    res = (lo > 0) or (ro > 0)
    if res:
        res = TRUE
    else:
        res = FALSE
    m.memory_write(res, t)
    ip_continue()

def assign(lo, ro, t):
    lo = m.memory_read(int(lo))
    m.memory_write_no_pointer(lo, t)
    ip_continue()

def ret(lo, ro, t):
    global ip
    new_ip  = m.end_subroutine(t)
    ip = new_ip
    ip_continue()

def read(lo, ro, t):
    i = input("Input: ")
    m.memory_write(i, t, safety = True)
    ip_continue()

def write(lo, ro, t):
    o = m.memory_read(t)
    print(o)
    ip_continue()

def goto(lo, ro, t):
    set_ip(int(t))

def gotof(lo, ro, t):
    lo = m.memory_read(int(lo))
    res = (lo == FALSE)
    if (res):
        set_ip(int(t))
    else:
        ip_continue()

def gotot(lo, ro, t):
    lo = m.memory_read(int(lo))
    res = (lo == FALSE)
    if (res):
        ip_continue()
    else:
        set_ip(int(t))

def era(lo, ro, t):
    m.prepare_context(lo, t)
    ip_continue()

def endfunc(lo, ro, t):
    global ip
    new_ip  = m.end_subroutine()
    ip = new_ip
    ip_continue()
    

def parameter(lo, ro, t):
    m.handle_param(lo, int(t))
    ip_continue()

def gosub(lo, ro, t):
    m.start_subroutine(lo, ip)
    set_ip(int(t))

def verify(lo, ro, t):
    lo = m.memory_read(lo)
    ro = m.memory_read(ro)
    t = m.memory_read(t)
    if lo < ro or lo > t:
        raise IndexError("Tried to access array out of bounds in quad " + str(get_ip()))
    ip_continue()

op_codes = [
    mult, # 0
    div, # 1
    add, # 2
    subtract, # 3
    lt, # 4
    gt, #5
    equal,
    not_equal,
    gte,
    lte,
    and_et,
    or_vel,
    assign,
    ret,
    read,
    write,
    goto,
    gotof,
    gotot,
    era,
    endfunc,
    parameter,
    gosub,
    verify
]

def eval(quad):
    '''All quadruple operations start here.'''
    op = quad.pop(0)
    op = int(op)
    left_operand = quad[0]
    right_operand = quad[1]
    target = quad[2]
    op_codes[op](left_operand, right_operand, target)


def main(ovejota):
    '''Reads thorugh the file.
    Expects the first line to be constants, the second line to be functions.
    All other lines are expected to be quads.'''
    lines = open(ovejota, "r").readlines()
    constants = lines.pop(0)
    quad = constants.strip()
    quad = pp.common.comma_separated_list.parseString(quad).asList()
    quad.pop(0)
    m.initiate_constants(quad)
    functions = lines.pop(0)
    quad = functions.strip().split(',')
    quad.pop(0)
    m.initiate_functions(quad)


    while (ip < len(lines)): 
        l = lines[ip]
        quad = l.strip().split(',')
        eval(quad)

if __name__ == '__main__':
    main(sys.argv[1])