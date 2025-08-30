class FST:
    def __init__(self):
        self.transitions = [{}]
        self.finals = {}
    def add_state(self):
        self.transitions.append({})
        return len(self.transitions) - 1
    def add_arc(self, start, up, down, weight=0.000, end=None):
        if start not in range(len(self.transitions)):
            raise ValueError('No state %s' % start)
        if end is None:
            end = self.add_state()
        if end not in range(len(self.transitions)):
            raise ValueError('No state %s' % end)
        if (up, down) not in self.transitions[start]:
            self.transitions[start][(up, down)] = {}
        self.transitions[start][(up, down)][end] = min(
            weight, self.transitions[start][(up, down)].get(end, weight))
        return end
    def add_string(self, start, up, down, weight=0.000, end=None):
        if start not in range(len(self.transitions)):
            raise ValueError('No state %s' % start)
        ul = list(up)
        dl = list(down)
        if len(ul) > len(dl):
            dl += [''] * (len(ul) - len(dl))
        elif len(dl) > len(ul):
            ul += [''] * (len(dl) - len(ul))
        if not ul and end is not None and end != start:
            return self.add_arc(start, '', '', weight=weight, end=end)
        st = start
        for i in range(len(ul)):
            if i + 1 == len(ul):
                st = self.add_arc(st, ul[i], dl[i], weight=weight,
                                  end=end)
            else:
                st = self.add_arc(st, ul[i], dl[i])
        return st
    def add_final(self, state, weight=0.000):
        self.finals[state] = weight
    def remove_final(self, state):
        if state in self.finals:
            del self.finals[state]
    def iter_transitions(self, state, up=None, down=None):
        for u, d in self.transitions[state]:
            if up is not None and up != u:
                continue
            if down is not None and down != d:
                continue
            for t, w in self.transitions[state][(u, d)].items():
                yield u, d, t, w
    def compose(self, other):
        ret = FST()
        queue = [(0, 0, 0)]
        seen = set()
        while queue:
            ss, so, sr = queue.pop()
            if (ss, so) in seen:
                continue
            for us, ds, ts, ws in self.iter_transitions(ss):
                if ds == '':
                    tr = ret.add_arc(sr, us, ds, weight=ws)
                    queue.append((ts, so, tr))
                    continue
                for uo, do, to, wo in other.iter_transitions(so, up=ds):
                    tr = ret.add_arc(sr, us, do, weight=ws+wo)
                    queue.append((ts, to, tr))
            for uo, do, to, wo in other.iter_transitions(so, up=''):
                tr = ret.add_arc(sr, uo, do, weight=wo)
                queue.append((ss, to, tr))
            seen.add((ss, so))
            if ss in self.finals and so in other.finals:
                ret.add_final(sr, weight=self.finals[ss]+other.finals[so])
        return ret
    def _closure(self, state, seen=None, prefix=None, up=None, down=None):
        if not seen:
            yield state, (prefix or [])
            seen = set([state])
        for trans in self.iter_transitions(state, up=up, down=down):
            path = (prefix or []) + [trans]
            yield trans[2], path
            if trans[2] in seen:
                continue
            seen.add(trans[2])
            yield from self._closure(trans[2], seen, path)
    def _closure_up(self, state, seen=None, prefix=None):
        yield from self._closure(state, seen, prefix, down='')
    def _closure_down(self, state, seen=None, prefix=None):
        yield from self._closure(state, seen, prefix, up='')
    def apply_up(self, inp, mode='string'):
        states = list(self._closure_up(0))
        for ch in inp:
            next_states = []
            for state, path in states:
                for trans in self.iter_transitions(state, down=ch):
                    next_states += list(self._closure_up(
                        trans[2], prefix=path+[trans]))
            states = next_states
        if mode == 'all':
            return states
        states = [(s, p) for s, p in states if s in self.finals]
        if mode == 'string':
            ret = set()
            for state, path in states:
                s = ''
                w = self.finals[state]
                for u, d, t, w in path:
                    s += u
                    w += w
                ret.add((s, w))
            return ret
        return states
    def apply_down(self, inp, mode='string'):
        states = list(self._closure_down(0))
        for ch in inp:
            next_states = []
            for state, path in states:
                for trans in self.iter_transitions(state, up=ch):
                    next_states += list(self._closure_down(
                        trans[2], prefix=path+[trans]))
            states = next_states
        if mode == 'all':
            return states
        states = [(s, p) for s, p in states if s in self.finals]
        if mode == 'string':
            ret = set()
            for state, path in states:
                s = ''
                w = self.finals[state]
                for u, d, t, w in path:
                    s += d
                    w += w
                ret.add((s, w))
            return ret
        return states

# TODO: escaped colons
# TODO: multichar_symbols
def tokenize_lexc(line):
    ret = []
    cur = ''
    esc = False
    for c in line:
        if esc:
            cur += c
            esc = False
        elif c == '%':
            esc = True
        elif c.isspace():
            if cur:
                ret.append(cur)
            cur = ''
        elif c == '!':
            break
        elif c in ':;':
            if cur:
                ret.append(cur)
            ret.append(c)
            cur = ''
        # TODO: regex in <>
        else:
            cur += c
    if cur:
        ret.append(cur)
    return ret
def compile_lexc(text, errors=True):
    ret = FST()
    lexicons = {'Root': 0}
    start = 0
    for lineno, line in enumerate(text.splitlines(), 1):
        toks = tokenize_lexc(line)
        if not toks:
            continue
        if len(toks) == 2 and toks[0].lower() == 'lexicon':
            name = toks[1]
            if name not in lexicons:
                lexicons[name] = FST.add_state()
            start = lexicons[name]
        elif len(toks) > 1 and toks[-1] == ';':
            tgt = toks[-2]
            if tgt not in lexicons:
                lexicons[tgt] = ret.add_state()
            end = lexicons[tgt]
            content = toks[:-2]
            if len(content) == 0 or content == [':']:
                ret.add_arc(start, '', '', end=end)
            elif len(content) == 1:
                ret.add_string(start, content[0], content[0], end=end)
            elif len(content) == 2 and content[0] == ':':
                ret.add_string(start, '', content[1], end=end)
            elif len(content) == 2 and content[1] == ':':
                ret.add_string(start, content[0], '', end=end)
            elif len(content) == 3 and content[1] == ':':
                ret.add_string(start, content[0], content[2], end=end)
            elif errors:
                raise ValueError('Unable to parse line %d: "%s"' % (lineno, line))
        elif errors:
            raise ValueError('Unable to parse line %d: "%s"' % (lineno, line))
    if '#' in lexicons:
        ret.add_final(lexicons['#'])
    return ret
