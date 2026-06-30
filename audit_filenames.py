import re, os
os.chdir('backend')
files = {
    'quercus': 'api/quercus.py',
    'ldap': 'api/ldap.py',
    'google': 'api/google.py',
    'canvas': 'api/canvas.py',
    'library': 'api/library.py',
    'athens': 'api/athens.py',
    'export': 'api/export.py',
}
for name, path in files.items():
    with open(path) as f:
        c = f.read()
    outer = re.findall(r'filename[=:].*?"([^"]+)"', c)
    inner = re.findall(r'writestr\("([^"]+)"', c)
    print(f'--- {name} ---')
    for m in outer: print(f'  outer: {m}')
    for m in inner: print(f'  inner: {m}')
    print()
