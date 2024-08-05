#!/usr/bin/python3

import os
import sys
import subprocess
import re
import shlex

if len(sys.argv) < 2:
    print("Please provide a filepath as the first argument.")
    sys.exit(1)

# Get all the paths in sys.path
paths = os.environ['PATH'].split(':')

# Collect the results from calling ls on each path
results = []
for path in paths:
    try:
        if path.startswith('/mnt'):
            continue
        # Call ls on the path and collect the output
        output = os.listdir(path)
        results.append(output)
    except OSError:
        # Handle any errors that occur while calling ls
        results.append([])  # Add an empty list if an error occurs

shell = os.environ.get('SHELL') or '/bin/sh'
bin = tuple(['cd', 'echo', 'exit', 'export', 'set', 'unset', 'alias', 'unalias', 'ulimit', 'typeset', \
            'source', 'readarray', 'printf', 'mapfile', 'logout', 'local', 'let', 'help', 'enable', \
            'disown', 'dirs', 'echo', 'declare', 'command', 'caller', 'builtin', 'bind', 'alias', \
            'wait', 'times', 'suspend', 'shift', 'unshift', 'return', 'read', 'pushd', 'popd', \
            'source', 'hash', 'fc', 'bg', 'fg', 'jobs', 'umask'] + sum([result for result in results], []))
if 'zsh' in bin:
    shell = 'zsh'
elif 'bash' in bin:
    shell = 'bash'

#print(bin)

#print(bin.index('pwd'))

filepath = sys.argv[1]
lines = []
with open(filepath, 'r') as f:
    lines = f.readlines()

def handle_candidate(line, len, index):
    depth = 1
    end = index 
    c = line[index]
    while end < len:
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        if depth == 0:
            break
        end += 1
        c = line[end]
    return end+1 - index, line[index:end]


def macro_interpolate(line):
    ln = len(line)
    builder = '_I = "' + shell + ' -c " + shlex.quote("'
    i = 0
    while i < ln:
        c = line[i]
        if i+4 < ln and c == 'P' and line[i+1] == 'Y' and line[i+2] == '?':
            end, res = handle_candidate(line, ln, i+4)
            builder += '" + ' + res + ' + "'
            i += end + 4
        else:
            builder += c
            i += 1
    builder += '")\n'
    return builder
            
    #return re.sub(r'PY\?{([a-zA-Z0-9_]+)}', lambda x: str(x.group(1)), line)

def macro_substitute(line):
    if line[-1] == '|':
        repl = f'{line[:-1]}_P = subprocess.Popen(_I, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)\n'
    else:
        repl = f'{line}_P = subprocess.Popen(_I, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)\n'
        repl += '_O, _E = _P.communicate()\n'
    return repl

if not lines[0].startswith('#!'):
    lines.insert(0, '#!/usr/bin/python3\n')

imports_subprocess = False
imports_shlex = False
for i, line in enumerate(lines):
    if line.startswith(bin):
        line = macro_interpolate(line.strip())
        #print(line)
        lines[i] = macro_substitute(line)
    elif line.find('import subprocess') >= 0:
        imports_subprocess = True
    elif line.find('import shlex') >= 0:
        imports_shlex = True

if not imports_subprocess:
    lines.insert(1, 'import subprocess\n')
if not imports_shlex:
    lines.insert(2, 'import shlex\n')

with open(filepath+'.pysh', 'w') as f:
    f.writelines(lines)
    #print(lines)

# todo: exec()?
subprocess.call(['chmod', '+x', filepath+'.pysh'])
subprocess.call(['./'+filepath+'.pysh'], shell=True)
subprocess.call(['rm', filepath+'.pysh'])