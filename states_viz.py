#!/usr/bin/env python3

import argparse
import networkx as nx
import sys


STATES_COORDS_FILE         = 'states.coords'
STATES_EDGES_FILE          = 'states.edges'
STATES_LATLONG_FILE        = 'states.latlong'


STATES_DOTFILE_PLANNED_OUT = 'states_planned.dot'
STATES_DOTFILE_SPRINGS_OUT = 'states_springs.dot'


def read_graph(nodes_file, edges_file, order='xy'):
    def read_nodes(nodes_file):
        with open(nodes_file, 'r') as f:
            for line in f.readlines():
                if line.startswith('#'): continue
                items = line.strip().split()
                assert(len(items) == 3)
                name = items[0]
                x = float(items[1])
                y = float(items[2])
                if order == 'yx':
                    x, y = y, x
                yield (name, x, y)

    def read_edges(edges_file):
        with open(edges_file, 'r') as f:
            for line in f.readlines():
                if line.startswith('#'): continue
                vals = line.strip().split(':')
                name = vals[0]
                nbrs = vals[1].split() if len(vals) > 1 else []
                yield (name, nbrs)

    result = nx.Graph()
    for name, x, y in read_nodes(nodes_file):
        result.add_node(name, x=x, y=y)
    for node, nbrs in read_edges(edges_file):
        for nbr in nbrs:
            if nbr > node:
                result.add_edge(node, nbr)
    return result


def write_dotfile_planned(g, dotfile_name):
    xs = [attrs['x'] for name, attrs in g.nodes(data=True)]
    ys = [attrs['y'] for name, attrs in g.nodes(data=True)]

    xmax = int(max(xs))
    xmin = int(min(xs))
    ymax = int(max(ys))
    ymin = int(min(ys))

    coords2state = { (attrs['x'], attrs['y']) : name
                     for name, attrs in sorted(g.nodes(data=True))
                   }
    state2coords = { name : (attrs['x'], attrs['y'])
                     for name, attrs in sorted(g.nodes(data=True))
                   }

    def get_name_isstate(x, y):
        if (x, y) in coords2state:
            return (coords2state[(x, y)], True)
        else:
            return (f'dummy_{x}_{y}', False)

    def write_nodes(f):
        for x in range(xmin, xmax + 1):
            cluster_name = f'cluster_{x}'
            f.write('  subgraph ')
            f.write(cluster_name)
            f.write('  {\n')
            f.write('    style=invis\n')
            for y in range(ymin, ymax + 1):
                scale_factor = 100
                (name, is_state) = get_name_isstate(x, y)
                pos_spec = f'pos="{scale_factor * x:.1f},{scale_factor * y:.1f}"'
                vis_spec = '' if is_state else 'style=invis'
                node_spec = f'    {name} [{pos_spec} {vis_spec}]\n'
                f.write(node_spec)
            f.write('  }\n')

    def write_edges(f):
        for a, b in sorted(g.edges(data=False)):
            if b > a:
                is4 = (a, b) in [('AZ','CO'), ('NM','UT')]
                color = 'color=red'    if is4 else ''
                style = 'style=dashed' if is4 else ''
                annotation = f'[{color} {style}]'
                f.write(f'  {a} -- {b} {annotation}\n')

#        f.write(f'\n')
#        for x in range(xmin, xmax):
#            for y in range(ymin, ymax):
#                (xy, is_xy_state) = get_name_isstate(x, y)
#                (east, is_east_state) = get_name_isstate(x + 1, y)
#                (north, is_north_state) = get_name_isstate(x, y + 1)
#
#                if not (is_xy_state and is_east_state):
#                    f.write(f'  {xy:12s} -- {east:12s}  [style=invis, weight=1000]\n')
#                if not (is_xy_state and is_north_state):
#                    f.write(f'  {xy:12s} -- {north:12s}  [style=invis, weight=1000]\n')
#                f.write('\n')

    with open(dotfile_name, 'w') as f:
        f.write('strict graph States {\n')
        # f.write('  rankdir=LR\n')
        # f.write('  node [style="rounded,filled"];\n')
        # f.write('  graph [style=filled, splines=line];\n')
        # f.write('  rank=same;\n')
        f.write('\n')
        write_nodes(f)
        f.write('\n')
        write_edges(f)
        f.write('}\n')


def write_dotfile_springs(g, dotfile_name):
    def write_nodes(f):
        for name, attrs in sorted(g.nodes(data=True)):
            is48 = name not in ['AK', 'HI']
            pos_attrs = f'[pos="{attrs["x"]:.2f},{attrs["y"]:.2f}"]' if is48 else ''
            f.write(f'    {name} {pos_attrs}\n')

    def write_edges(f):
        f.write('    AK -- HI [style=invis]\n\n')  # Appear nearby, but unlinked
        # f.write('    HI -- SC [style=invis]\n\n')  # Custom tweak to move AK, HI
        f.write('    NJ -- CT [style=invis]\n')  # Custom tweak to move NJ
        f.write('    NJ -- MD [style=invis]\n\n')  # Custom tweak to move NJ
        for a, b in sorted(g.edges(data=False)):
            if b > a:  # Avoid duplication
                is4 = (a, b) in [('AZ','CO'), ('NM','UT')]
                edge_attrs = '[color=red style=dashed]' if is4 else ''
                f.write(f'    {a} -- {b} {edge_attrs}\n')

    with open(dotfile_name, 'w') as f:
        f.write('strict graph States {\n')
        f.write('    rankdir=LR\n')
        f.write('    splines=line\n\n')
        write_nodes(f)
        f.write('\n')
        write_edges(f)
        f.write('}\n')

# ----------------------------------------

def test_graph(state_graph):
    assert(len(state_graph.nodes(data=False)) == 50)
    nbr_count = 2.0 * len(state_graph.edges(data=False))
    node_count = len(state_graph.nodes(data=False))
    avg_nbr_count = nbr_count / node_count
    # print(f'avg_nbr_count={avg_nbr_count}')
    assert(4.25 < avg_nbr_count < 4.3)

# ----------------------------------------

def make_dotfile_planned():
    src = read_graph( nodes_file=STATES_COORDS_FILE
                    , edges_file=STATES_EDGES_FILE
                    )
    test_graph(src)
    write_dotfile_planned( g=src
                         , dotfile_name=STATES_DOTFILE_PLANNED_OUT
                         )


def make_dotfile_springs():
    src = read_graph( nodes_file=STATES_LATLONG_FILE
                    , edges_file=STATES_EDGES_FILE
                    , order='yx'
                    )
    test_graph(src)
    write_dotfile_springs(g=src, dotfile_name=STATES_DOTFILE_SPRINGS_OUT)


if __name__ == '__main__':
    prog='states_viz'
    parser = argparse.ArgumentParser( prog=prog
                                    , description='Visualize layout of US states'
                                    )
    parser.add_argument('-p', '--planned', action='store_true')
    parser.add_argument('-s', '--springs', action='store_true')
    args = parser.parse_args(sys.argv[1:])

    if (not args.planned) and (not args.springs):
        print(f'{prog}: At least one output flag required.')
        parser.print_help(sys.stderr)
        sys.exit(1)
    if args.planned:
        make_dotfile_planned()
    if args.springs:
        make_dotfile_springs()
