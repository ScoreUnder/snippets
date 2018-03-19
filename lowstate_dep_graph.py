#!/usr/bin/env python3
import itertools
import yaml
import sys

class MultiDict(dict):
    def add(self, key, value):
        if key not in self:
            self[key] = []
        self[key].append(value)

deps = MultiDict()
states = MultiDict()


def find_state(name):
    return states.get(name, ["<!!!>" + name])


def foreach_dep(action, dep_list):
    for dep in dep_list:
        if not isinstance(dep, str):
            key, val = next(iter(dep.items()))
            dep = "{}.{}".format(key, val)
        action(dep)


if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = 'lowstate'

lowstate = yaml.load(open(filename))['local']

for state in lowstate:
    state_id = '{state}.{__id__}'.format(**state)
    states.add(state['__id__'], state_id)
    states.add(state_id, state_id)
    states.add('sls.' + state['__sls__'], state_id)

    for key in 'require watch prereq use onchanges onfail listen'.split():
        foreach_dep(lambda n: deps.add(state_id, n), state.get(key, {}))
        foreach_dep(lambda n: deps.add(n, state_id), state.get(key + '_in', {}))

print("digraph { node[shape=rectangle]")
for key, vals in deps.items():
    key = find_state(key)
    vals = itertools.chain(*map(find_state, vals))
    for state in set(key):
        for val in set(vals):
            print('"{}" -> "{}"'.format(state, val))
print("}")
