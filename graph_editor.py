import math
import os
import copy

import networkx as nx

import pyglet
from pyglet.window import key
from pyglet.window import mouse
from pyglet.gl import *

class App(pyglet.window.Window):
    def __init__(self):
        super(App, self).__init__(800, 600, "Graph Editor", resizable=True)
        self.set_minimum_size(640, 480)

        self.g = nx.Graph()

        self.mode = "node"
        self.selected = None
        self.offset = [0, 0]
        self.scale = 100.0
        self.zoom_step = 0
        self.help = False
        self.info = False
        self.drag = False
        self.box = [0, 0, 1000, 1000]
        self.history = []
        self.history_index = -1
        self.sidebar_width = 300

        # create vertex list
        self.statusbar = pyglet.graphics.vertex_list(4, 
            ('v2f', (0, 0, self.width, 0, self.width, 24, 0, 24)),
            ('c3B', (30, 30, 30) * 4)
        )
        self.line = pyglet.graphics.vertex_list(2,
            ('v2f', (self.width - 200, 2, self.width - 200, 22)),
            ('c3B', (80, 80, 80) * 2)
        )

        # labels
        self.cmd_label = pyglet.text.Label("Press 'h' for help", font_name='Sans', font_size=12, x=10, y=6)

        self.info_label = pyglet.text.Label("", multiline=True, x=50, y=self.height - 50,
            width=self.width-100, height=self.height-100, anchor_y="top", font_name="monospace", font_size=12)

        with open("help.txt") as help_file:
            self.help_label = pyglet.text.Label(help_file.read(), multiline=True, x=50, y=self.height - 50,
                    width=self.width-100, height=self.height-100, anchor_y="top", font_name="monospace", font_size=12)

        # load images
        node_img = pyglet.resource.image("node.png")
        node_img.anchor_x = 12
        node_img.anchor_y = 12
        self.node_sprite = pyglet.sprite.Sprite(node_img)

        selected_img = pyglet.resource.image("selected.png")
        selected_img.anchor_x = 12
        selected_img.anchor_y = 12
        self.selected_sprite = pyglet.sprite.Sprite(selected_img)

    def check_node(self, x, y):
        x = x - self.offset[0]
        y = y - self.offset[1]

        for node in self.g.nodes_iter():
            d = (self.g.node[node]["x"] * self.scale - x)**2 + (self.g.node[node]["y"] * self.scale - y)**2

            if d < 36:
                return node

        return False
    
    def check_edge(self, x, y):
        x = x - self.offset[0]
        y = y - self.offset[1]

        for edge in self.g.edges_iter():
            n1 = self.g.node[edge[0]]
            n2 = self.g.node[edge[1]]

            n1x = n1["x"] * self.scale
            n1y = n1["y"] * self.scale
            n2x = n2["x"] * self.scale
            n2y = n2["y"] * self.scale

            # circle containing the edge
            ccx = (n1x + n2x) / 2.0 # circle center x
            ccy = (n1y + n2y) / 2.0 # circle center y
            r = ((n1x - n2x)**2 + (n1y - n2y)**2) / 4.0 # squared radius

            # squared distance of the point (x, y) form the center of the circle above
            dp = (ccx - x)**2 + (ccy - y)**2

            if dp <= r:
                # magic, don't touch!
                a = n2y - n1y
                b = n1x - n2x
                c = n2x * n1y - n1x * n2y

                d = abs(a * x + b * y + c) / math.sqrt(a**2 + b**2)

                if d < 5:
                    return edge

        return False

    def undo(self):
        if self.history_index == -1:
            self.cmd_label.text = "There is no previous history"
        else:
            change = self.history[self.history_index]

            if change[0] == "add":
                self.g.remove_node(change[1])
            elif change[0] == "add edge":
                self.g.remove_edge(*change[1])
            elif change[0] == "del":
                self.g.add_node(change[1], **change[2])

                for node, attributes in change[3].iteritems():
                    self.g.add_edge(change[1], node, **attributes)
            elif change[0] == "del edge":
                self.g.add_edge(*change[1], **change[2])
            elif change[0] == "move":
                self.g.node[change[1]] = change[2]

                for node, attributes in change[3].iteritems():
                    self.g.add_edge(change[1], node, **attributes)

            self.history_index -= 1
            self.cmd_label.text = "'{0}' operation undone".format(change[0])

    def redo(self):
        if self.history_index == len(self.history) - 1:
            self.cmd_label.text = "Already at newest change"
        else:
            self.history_index += 1
            change = self.history[self.history_index]

            if change[0] == "add":
                self.g.add_node(change[1], **change[2])
            elif change[0] == "add edge":
                self.g.add_edge(*change[1], **change[2])
            elif change[0] == "del":
                self.g.remove_node(change[1])
            elif change[0] == "del edge":
                self.g.remove_edge(*change[1])
            elif change[0] == "move":
                self.g.node[change[1]] = change[4]

                for node, attributes in change[5].iteritems():
                    self.g.add_edge(change[1], node, **attributes)

            self.cmd_label.text = "'{0}' operation redone".format(change[0])

    def on_draw(self):
        self.clear()

        ox = self.offset[0]
        oy = self.offset[1]

        if self.help:
            # draw help on the screen
            self.help_label.draw()
        elif self.info:
            # draw info on the screen
            self.info_label.draw()
        else:
            # draw edges
            for edge in self.g.edges_iter():
                pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v2f', (
                    ox + self.g.node[edge[0]]["x"] * self.scale,
                    oy + self.g.node[edge[0]]["y"] * self.scale,
                    ox + self.g.node[edge[1]]["x"] * self.scale,
                    oy + self.g.node[edge[1]]["y"] * self.scale)))

            # draw nodes
            for node in self.g.nodes_iter():
                if node == self.selected:
                    self.selected_sprite.set_position(ox + self.g.node[node]["x"] * self.scale,
                            oy + self.g.node[node]["y"] * self.scale)
                    self.selected_sprite.draw()
                else:
                    self.node_sprite.set_position(ox + self.g.node[node]["x"] * self.scale,
                            oy + self.g.node[node]["y"] * self.scale)
                    self.node_sprite.draw()
            
            # draw borders
            pyglet.graphics.draw(4, pyglet.gl.GL_LINE_LOOP,
                ('v2f', (self.box[0] * self.scale + ox, self.box[1] * self.scale + oy,
                        self.box[2] * self.scale + ox, self.box[1] * self.scale + oy,
                        self.box[2] * self.scale + ox, self.box[3] * self.scale + oy,
                        self.box[0] * self.scale + ox, self.box[3] * self.scale + oy)))

            # draw statusbar
            self.statusbar.draw(pyglet.gl.GL_QUADS)
            self.line.draw(pyglet.gl.GL_LINES)

            # draw mode in the statusbar
            mode_label = pyglet.text.Label(self.mode, font_name='Sans', font_size=12, x=self.width - 190, y=6)
            mode_label.draw()

            # draw command
            self.cmd_label.draw()

            # if mode is modify, then show sidebar
            if self.mode == "modify":
                if self.selected != None:
                    attributes = self.g.node[self.selected]

                    # variables used not to repeat 100 times the same thing
                    sidebar_border = 10
                    sidebar_padding = 20
                    cell_height = 28
                    cell_padding = 6

                    # precompute some stuff
                    sidebar_left = self.width - self.sidebar_width - sidebar_border
                    sidebar_top = self.height - sidebar_border
                    sidebar_height = sidebar_padding * 2 + len(attributes) * cell_height
                    sidebar_content_left = sidebar_left + sidebar_padding
                    sidebar_content_top = sidebar_top - sidebar_padding
                    cell_width = self.sidebar_width / 2 - sidebar_padding
                    sidebar_middle = sidebar_content_left + cell_width
                    sidebar_content_right = sidebar_content_left + cell_width * 2

                    # draw box
                    pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                        ('v2f', (sidebar_left, sidebar_top,
                            sidebar_left + self.sidebar_width, sidebar_top,
                            sidebar_left + self.sidebar_width, sidebar_top - sidebar_height,
                            sidebar_left, sidebar_top - sidebar_height)),
                        ('c3B', (50, 50, 50) * 4)
                    )
                    
                    # draw grid
                    # compute the number of its vertices
                    vertex_num = 8 + len(attributes) * 2

                    # create vertices
                    grid_vertices = []
                    # horizontal lines
                    for n in range(len(attributes) + 1):
                        grid_vertices.extend((
                            sidebar_content_left, sidebar_content_top - n * cell_height,
                            sidebar_content_right, sidebar_content_top - n * cell_height
                        ))
                    # vertical lines
                    grid_vertices.extend((
                        sidebar_content_left, sidebar_content_top,
                        sidebar_content_left, sidebar_content_top - len(attributes) * cell_height,
                        sidebar_middle, sidebar_content_top,
                        sidebar_middle, sidebar_content_top - len(attributes) * cell_height,
                        sidebar_content_right, sidebar_content_top,
                        sidebar_content_right, sidebar_content_top - len(attributes) * cell_height,
                    ))

                    # actually draw grid
                    pyglet.graphics.draw(vertex_num, pyglet.gl.GL_LINES,
                        ('v2f', grid_vertices),
                        ('c3B', (100, 100, 100) * vertex_num)
                    )

                    for n, (key, value) in enumerate(attributes.iteritems()):
                        ly = sidebar_content_top - n * cell_height - cell_padding

                        key_label = pyglet.text.Label(str(key), font_name='Sans', font_size=12,
                            x=sidebar_content_left + cell_padding, y=ly, anchor_y="top")
                        value_label = pyglet.text.Label(str(value), font_name='Sans', font_size=12,
                            x=sidebar_middle + cell_padding, y=ly, anchor_y="top")

                        key_label.draw()
                        value_label.draw()

    def on_mouse_press(self, x, y, buttons, modifiers):
        node = self.check_node(x, y)
        # check if a node has not been clicked
        if node is not False:
            if self.mode == "modify":
                self.selected = node
        elif self.mode == "modify":
            self.selected = None

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if buttons & mouse.RIGHT:
            self.offset[0] += dx
            self.offset[1] += dy
        elif buttons & mouse.LEFT and self.mode == "modify":
            if self.selected != None:
                node = self.g.node[self.selected]
                
                if not self.drag:
                    # add to history
                    self.history_index += 1
                    del self.history[self.history_index:len(self.history)]
                    self.history.append(["move", self.selected, copy.copy(node), self.g[self.selected]])

                    self.drag = True

                node["x"] += dx / self.scale
                node["y"] += dy / self.scale
                
    def on_mouse_release(self, x, y, buttons, modifiers):
        if buttons & mouse.LEFT:
            if self.mode == "node":
                node = self.check_node(x, y)
                # check if a node has not been clicked
                if node is False:
                    self.g.add_node(len(self.g), x=float(x - self.offset[0]) / self.scale, y=float(y - self.offset[1]) / self.scale)
                    self.selected = len(self.g) - 1

                    # add to history
                    self.history_index += 1
                    del self.history[self.history_index:len(self.history)]
                    self.history.append(("add", self.selected, copy.copy(self.g.node[self.selected])))
                else:
                    self.selected = node
            elif self.mode == "edge":
                node = self.check_node(x, y)
                # check if a node has been clicked
                if node is not False:
                    # if the node was already selected deselct it
                    if self.selected == node:
                        self.selected = None
                    # if no node was selected select the current one
                    elif self.selected == None:
                        self.selected = node
                    # if a different node is already selected add an edge between the two
                    # but check if there is already an edge between the two: in this case
                    # just do nothing
                    else:
                        if node not in self.g[self.selected]:
                            n1 = self.g.node[node]
                            n2 = self.g.node[self.selected]

                            n1x = n1["x"] * self.scale
                            n1y = n1["y"] * self.scale
                            n2x = n2["x"] * self.scale
                            n2y = n2["y"] * self.scale

                            d = math.sqrt((n1x - n2x)**2 + (n1y - n2y)**2)
                            self.g.add_edge(self.selected, node, weight=d)

                            # add to history
                            self.history_index += 1
                            del self.history[self.history_index:len(self.history)]
                            self.history.append(("add edge", (self.selected, node), self.g[self.selected][node]))

                        self.selected = node
            elif self.mode == "delete":
                node = self.check_node(x, y)
                # check if a node has been clicked
                if node is not False:
                    # if the node was selected unselect it
                    if self.selected == node:
                        self.selected = None

                    # add to history
                    self.history_index += 1
                    del self.history[self.history_index:len(self.history)]
                    self.history.append(("del", node, self.g.node[node], self.g[node]))

                    # actually remove the node
                    self.g.remove_node(node)

                edge = self.check_edge(x, y)
                # check if an edge has been clicked
                if edge is not False:
                    # add to history
                    self.history_index += 1
                    del self.history[self.history_index:len(self.history)]
                    self.history.append(("del edge", edge, self.g[edge[0]][edge[1]]))

                    # actually remove the edge
                    self.g.remove_edge(*edge)
        
        # dragging of node ended update some stuff
        if self.drag:
            node = self.g.node[self.selected]

            # change weight of connected edges
            for connected_node in iter(self.g[self.selected]):
                c_node = self.g.node[connected_node]
                # compute new distance                   
                d = math.sqrt((node["x"] - c_node["x"])**2 + (node["y"] - c_node["y"])**2)

                self.g[self.selected][connected_node]["weight"] = d

            # update history
            self.history[-1].append(copy.copy(self.g.node[self.selected]))
            self.history[-1].append(copy.copy(self.g[self.selected]))

            self.drag = False

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.zoom_step += scroll_y
        self.scale = 100 * 1.2**self.zoom_step

    def on_key_press(self, symbol, modifiers):
        if symbol == key.H:
            self.help = True
        elif symbol == key.I:
            self.info = True

            # get info
            node_number = len(self.g)
            edge_number = len(self.g.edges())
            
            self.info_label.text = "Info\n\nNumber of nodes: {0}\nNumber of edges: {1}".format(node_number, edge_number)

    def on_key_release(self, symbol, modifiers):
        if symbol == key.N:
            self.mode = "node"
        elif symbol == key.E:
            self.mode = "edge"
        elif symbol == key.D:
            self.mode = "delete"
        elif symbol == key.M:
            self.mode = "modify"
        elif symbol == key.S:
            nx.write_graphml(self.g, "graph.graphml")
            # get info about the file
            stat = os.stat("graph.graphml") 
            num_nodes = len(self.g)
            size = stat.st_size / 1000.0
            # display info
            self.cmd_label.text = "{0} nodes written to graph.graphml ({1:,.1f}k)".format(num_nodes, size)
        elif symbol == key.L:
            try:
                self.g = nx.read_graphml("graph.graphml")
                # get info about the file
                stat = os.stat("graph.graphml")
                num_nodes = len(self.g)
                size = stat.st_size / 1000.0
                # display info
                self.cmd_label.text = "{0} nodes loaded from graph.graphml ({1:,.1f}k)".format(num_nodes, size)

                # clean up
                self.selected = None
            except IOError:
                # the file was missing
                self.cmd_label.text = "File graph.graphml not found"
        elif symbol == key.H:
            self.help = False
        elif symbol == key.I:
            self.info = False
        elif symbol == key.Q:
            self.close()
        elif symbol == key.Z:
            self.undo()
        elif symbol == key.Y:
            self.redo()
        elif symbol == key.F11:
            self.set_fullscreen(not self.fullscreen)
        elif symbol == key.ESCAPE:
            self.selected = None

    def on_resize(self, width, height):
        super(App, self).on_resize(width, height)
        
        self.info_label.y = self.height - 50
        self.info_label.width = self.width - 100
        self.info_label.height = self.height - 100

        self.help_label.y = self.height - 50
        self.help_label.width = self.width - 100
        self.help_label.height = self.height - 100

        self.statusbar.vertices[2] = self.width
        self.statusbar.vertices[4] = self.width

        self.line.vertices[0] = self.width - 200
        self.line.vertices[2] = self.width - 200


if __name__ == "__main__":
    window = App()
    pyglet.app.run()

