#!/usr/bin/env python

class Node(object):

  def __init__(self, desc):
    self.name = self._parse(desc)
    self.desc = desc
    self.children = []
    self.childrenCheck = set()
    self.refs = set()

  def __str__(self):
    return self.name

  def __repr__(self):
    return '{}[{}]'.format(self.__class__.__name__, self.name)

  def __iter__(self):
    return iter(self.children)

  def _parse(self, desc):
    if desc.startswith('Set#'):
      return desc[:desc.find(',')]
    elif desc.strip().startswith('rel#'):
      return desc[:desc.find(':')].strip()

    return desc

  def add(self, child):
    if child not in self.childrenCheck:
      self.children.append(child)
      self.childrenCheck.add(child)

  def accept(self, visitor):
    if visitor(self):
      for c in self:
        c.accept(visitor)

  def clone(self):
    clone = Node(self.desc)
    clone.childrenCheck = set(self.childrenCheck)
    clone.children = []
    for ch in self.children:
      clone.children.append(ch.clone())

    return clone


class RegistryVisitor(object):
  def __init__(self):
    self.mappings = {}

  def register(self, node):
    self.mappings[node.name] = node
    return 1


class ConnectingVisitor(object):

  def __init__(self, mappings):
    self.mappings = mappings
    self.visited = set()

  def connect(self, node):
    self.visited.add(node)
    for stmt in ('child=', 'left=', 'right='):
      refStart = node.desc.find(stmt)
      if refStart > -1:
        refStart += len(stmt)
        refEnd = node.desc.find(':', refStart)
        ref = node.desc[refStart:refEnd]
        refNode = self.mappings[ref]
        if refNode in self.visited:
          cycle = Node('cycle to '+refNode.name)
          node.add(cycle)

    return 1


class Graph(object):
  INDENT = '  '
  def __init__(self, root):
    self.root = root
    self.mappings = {}
    self.visited = set()

  def __iter__(self):
    return iter(self.root)

  def __str__(self):
    return '{}[{} plan/s]'.format(self.__class__.__name__, len(self.root.children))

  def output(self, dest, node, route, level=0):
    if node in route:
      cycle = Node('cycle to '+ node.name)
      dest.append(dict(node=cycle, level=level))
      return

    dest.append(dict(node=node, level=level))
    for child in node:
      self.output(dest, child, route, level+1)

  def dump(self, indent=INDENT):
    result = []
    for plan in self:
      out, route = [], set()
      self.output(out, plan, route)
      result.append('\n'.join((indent*n['level'] + n['node'].desc for n in out)))

    return '---\n'.join(result)

  def clone(self):
    return Graph(self.root.clone())

  @classmethod
  def fromDesc(cls, trace):
    root = Node('root')
    parents = [root]
    lastLevel, lastNode = 0, None
    for line in trace:
      if line.strip().startswith('Importances:'):
        break

      if line.strip().startswith('Set#') or line.strip().startswith('rel#'):
        curLevel = (line.find('Set#') + 1 or line.find('rel#') + 1) - 1
        if curLevel > lastLevel:
          parents.append(lastNode)

        while curLevel < lastLevel:
          parents.pop()
          lastLevel -= 1

        curNode = Node(line.strip())
        parents[-1].add(curNode)

        lastLevel, lastNode = curLevel, curNode

    return Graph(root) if root.children else None


class Trace(object):

  def __init__(self, rounds):
    self.rounds = rounds

  def __iter__(self):
    return iter(self.rounds)

  def __str__(self):
    return '{}[{} iteration(s)]'.format(self.__class__.__name__, len(self.rounds))

  @classmethod
  def parse(cls, path):
    rounds = []
    with open(path, 'r') as trace:
      for line in trace:
        if line.startswith('Sets:'):
          it = Graph.fromDesc(trace)
          if it is not None:
            rounds.append(it)

    return Trace(rounds)


import json

class TraceEncoder(json.JSONEncoder):

  def default(self, o):
    if isinstance(o, Node):
      return {'name': o.name, 'desc': o.desc, 'children': o.children}
    elif isinstance(o, Graph):
      return {'name': o.root.name, 'children': o.root.children}

    try:
      iterable = iter(o)
    except TypeError:
      pass
    else:
      return list(iterable)

    return json.JSONEncoder.default(self, o)

def dumps(obj):
  return json.dumps(obj, cls=TraceEncoder, indent=2)

def main(opt):
  if opt.web:
    import bottle
    import web
    app = bottle.Bottle()
    bottle.run(web.WebApp.create(app), host='0.0.0.0', port=9090, debug=1, reloader=1)
  elif opt.trace:
    trace = Trace.parse(opt.trace)
    if opt.json:
      print dumps(trace)
    else:
      for plan in  trace:
        plan.dump()

if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='optiq trace visualizer')
  parser.add_argument('-f', dest='trace', metavar='PATH', help='path to trace file')
  parser.add_argument('-j', dest='json', action='store_true', help='dump trace as json')
  parser.add_argument('-w', dest='web', action='store_true', help='run embedded webserver')

  args = parser.parse_args()
  main(args)