import main

f = main.FST()
s = f.add_string(0, 'abc', 'defg')
f.add_final(s)
s = f.add_arc(0, '', 'l')
s = f.add_string(s, 'xy', 'z')
s = f.add_arc(s, '', 'q')
f.add_final(s)

print('down abc')
print(f.apply_down('abc'))
print(f.apply_down('abc', mode='path'))

print('down xy')
print(f.apply_down('xy'))
print(f.apply_down('xy', mode='path'))

print('up defg')
print(f.apply_up('defg'))
print(f.apply_up('defg', mode='path'))

print('up lzq')
print(f.apply_up('lzq'))
print(f.apply_up('lzq', mode='path'))

g = main.FST()
for c in 'defglq':
    g.add_arc(0, c, c, end=0)
g.add_final(0)
s = g.add_arc(0, '', 'N')
s = g.add_arc(s, 'z', 'O')
g.add_arc(s, '', 'P', end=0)

h = f.compose(g)

print('h down abc', h.apply_down('abc'))
print('h down xy', h.apply_down('xy'))

l = main.compile_lexc('''
LEXICON Root
A ;
b: A ;
:c A ;
d:e A ;
LEXICON A
f:g # ;
''')
print(l.transitions)

print('l down f', l.apply_down('f'))
print('l down bf', l.apply_down('bf'))
print('l down df', l.apply_down('df'))
