import random, re, sys
variable_line_locations = {}
variable_name_locations = {}
variables = []

# each line is a variable
# each line has a unique ID
# each variable is the value of the line

# variable setting:
# f6e3c56e a            # new variable called 'a'
# 4e1f9859              # new variable
# e1052463 b 1          # new variable called 'b' set to 1
# 4c7101c0 1            # new variable set to 1
# 3d48442c c 'hi'       # new variable called 'c' set to 'hi'
# e7dc3c9b e1052463     # new variable set to value of b (1)
# 7c815a62 b            # new variable set to the value of b (1)
# 32a72757 b 3          # set variable b to 3
# 599f3028 b 3d48442c   # set variable b to 'hi'
# 8d96c463 

def line_hash(line:str, hashlength:int=None):
    if hashlength:
        return line[:hashlength], line[hashlength:].split('#')[0].strip() if len(line) > hashlength else None
    s = line.split('#')[0].strip().split(' ', 1)
    return s[0], s[1] if len(s) > 1 else None

def get_first_val(segment:str):
    if not segment:
        return 'empty', '', (0, 0)
    segment = segment.strip()
    m = re.match("'.*?[^\\\\]'", segment)
    if m:
        return 'str', m[0][1:-1], m.span() # string
    m = re.match('\d+( |$)', segment)
    if m:
        return 'int', int(m[0]), m.span() # integer
    m = re.match('\d*?\.\d+', segment)
    if m:
        return 'float', float(m[0]), m.span() # float
    m = re.match('[a-z]+', segment)
    if m:
        return 'name', m[0], m.span() # text
    m = re.match('![a-z0-9]+', segment)
    if m:
        return 'get', m[0][1:], m.span() # get another variable
    m = re.match('&[a-z][a-z0-9]+', segment)
    if m:
        return 'ref', m[0], m.span() # pointer
    return None, None, (0, 0)

def read_line(line:str, hashlength:int=None):
    h, line = line_hash(line, hashlength) # split into hash and rest of the line
    print('\nread_line', h, line)
    val_type, val, val_span = get_first_val(line) # get the first word
    print(f'val_type {val_type}, val {val}, val_span {val_span}')
    if val_type == 'get': # we're referencing another variable by hash or name
        print(get_var(val, val))
        new_var(h, None, get_var(val, val)) # set the hash to the value of the var
        return
    elif val_type == 'empty':
        new_var(h)
    elif val_type == 'ref': # set the hash variable to a reference (which may not even exist yet)
        new_var(h, None, val)
    elif val_type == 'name': # it's likely a name of variable
        if val in variable_name_locations: # it already exists
            vset = val
            if len(line) > val_span[1]: # there's more
                val_type, val, val_span = get_first_val(line[val_span[1]:])
                if val_type in ['str', 'int', 'float', 'ref']: # change the old variable value
                    set_var(None, vset, val)
                elif val_type == 'get':
                    set_var(None, vset, get_var(val, val))
                else:
                    raise FurtaxError
            new_var(h, None, get_var(None, vset)) # set the hash to the variable's value
            return
        vname = val
        if len(line) > val_span[1]: # there's more
            val_type, val, val_span = get_first_val(line[val_span[1]:])
            if val_type in ['str', 'int', 'float']:
                new_var(h, vname, val)
                return
            elif val_type == 'get':
                new_var(h, vname, get_var(val, val))
                return
        else:
            new_var(h, vname)
            return
    elif val_type in ['str', 'int', 'float']: # no name for the variable
        new_var(h, None, val)
        return

class FurtaxError(Exception): # syntax
    pass
class NoFurError(Exception): # variable doesn't exist
    pass

def new_var(h:str, name:str=None, value=None):
    print(f'new_var({h}, {name}, {value})')
    global variable_line_locations, variable_name_locations, variables
    i = len(variables)
    variables.append({'line': h, 'name': name, 'value': value})
    variable_line_locations[h] = i
    if name:
        variable_name_locations[name] = i

def set_var(h:str=None, name:str=None, value=None):
    print(f'set_var({h}, {name}, {value})')
    global variables
    if h:
        if not name and h not in variable_line_locations:
            raise NoFurError
        m = re.match('&[a-z0-9]+$', str(value))
        if m:
            variables[variable_line_locations[h]]['value'] = get_var(value, value)
        else:
            variables[variable_line_locations[h]]['value'] = value
        return
    if name:
        if name not in variable_name_locations:
            raise NoFurError
        m = re.match('&[a-z0-9]+$', str(value))
        if m:
            variables[variable_name_locations[name]]['value'] = get_var(value, value)
        else:
            variables[variable_name_locations[name]]['value'] = value
        return
    raise FurtaxError

def get_var(h:str=None, name:str=None):
    print(f'get_var({h}, {name})')
    if h:
        if h not in variable_line_locations:
            if not name:
                raise NoFurError
        else:
            val = variables[variable_line_locations[h]]['value']
            m = re.match('&[a-z0-9]+$', str(val))
            if m: # TODO: account for recursion errors
                return get_var(m[0], m[0])
            return val
    if name:
        if name not in variable_name_locations:
            raise NoFurError
        val = variables[variable_name_locations[name]]['value']
        m = re.match('&[a-z0-9]+$', str(val))
        if m:
            return get_var(m[0], m[0])
        return val
    raise FurtaxError

def read_file(name, limit=None):
    with open(name, 'r', encoding='utf-8') as f:
        lines= f.readlines()
    if not limit:
        limit = len(lines)
    for i in range(limit):
        read_line(lines[i])

def gen_file(name, length:int=50):
    random.seed(name)
    out = []
    for i in range(length):
        out.append(random.randbytes(4).hex() + ' \n')
    with open(name, 'w', encoding='utf-8') as f:
        f.writelines(out)

#gen_file('1.fur')
if __name__ == '__main__':
    if len(sys.argv) > 1:
        print('reading', sys.argv[1])
        read_file(sys.argv[1])
    else:
        read_file('1.fur', 10)
        for var in variables:
            print(var)