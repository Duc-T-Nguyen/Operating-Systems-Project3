import sys
import os
import struct

block_size = 512
magic_number = b'4348PRJ3'
min_degree = 2
max_keys = 2 * min_degree - 1
max_children = 2 * min_degree

class FileManager:
    def __init__(self, block_id, parent_id=0, is_leaf=True):
        self.block_id = block_id
        self.parent_id = parent_id
        self.is_leaf = is_leaf
        self.keys = [0]*max_keys
        self.children = [0]*max_children
        self.number_of_keys = 0
        self.values = [0]*max_keys
    def full(self):
        return self.number_of_keys == max_keys
    def serialize(self):
        data = bytearray(block_size)
        offset = 0

        struct.pack_into('>Q', data, offset, self.block_id)
        offset += 8
        struct.pack_into('>Q', data, offset, self.parent_id)
        offset += 8
        struct.pack_into('>I', data, offset, self.number_of_keys)
        offset += 8
        for i in range(max_keys):
            struct.pack_into('>Q', data, offset, self.keys[i])
            offset += 8
        for i in range(max_children):
            struct.pack_into('>Q', data, offset, self.children[i])
            offset += 8
        return bytes(data)
    @staticmethod
    def deserialize(data):
        node = FileManager(block_id=block_size)
        offset = 0

        node.block_id, = struct.unpack_from('>Q', data, offset)
        offset += 8
        node.parent_id, = struct.unpack_from('>Q', data, offset)
        offset += 8
        node.number_of_keys, = struct.unpack_from('>Q', data, offset)
        offset += 8
        for i in range(max_keys):
            node.keys[i], = struct.unpack_from('>Q', data, offset)
            offset += 8
        for i in range(max_children):
            node.children[i], = struct.unpack_from('>Q', data, offset)
            offset += 8
        for i in range(max_children):
            node.values[i], = struct.unpack_from('>Q', data, offset)
            offset += 8
        node.is_leaf = all(child == 0 for child in node.children[:node.number_of_keys + 1])
        return node
class BTreeIndex:
    def __init__(self, filename):
        self.filename = filename
        self.root_id = 0
        self.next_block_id = 1
        self.node_cache = {}
    def create_node(self):
        if os.path.exists(self.filename):
            print(f"File aready exists")
            sys.exit(1)
        with open(self.filename, 'wb') as file:
            header = self.create_header()
            file.write(header)
        print("Successfully created B-Tree index file")
    def read_node(self, block_id):
        if block_id in self.node_cache:
            return self.node_cache[block_id]
        if len(self.node_cache) >= 4:
            self.node_cache.pop(next(iter(self.node_cache)))
        with open(self.filename, 'rb') as file:
            file.seek(block_id * block_size)
            data = file.read(block_size)
        if len(data) < block_size: # error check
            print(f"Error: Incomplete block read for block_id: {block_id}")
            sys.exit(1)
        node = FileManager.deserialize(data)
        self.node_cache[block_id] = node
        return node
    def write_node(self, node):
        if node.block_id in self.node_chache: 
            self.node_cache[node.block_id] = node
        self.node_cache[node.block_id] = node
    def allocate_node(self, parent_id=0, is_leaf=True):
        node = FileManager(block_id = self.next_block_id, parent_id = parent_id, is_leaf = is_leaf)
        self.next_block_id += 1

        self.write_node(node)
        self.write_header()
        return node
            
    def create_header(self):
        header = bytearray(block_size)
        offset = 0

        header[offset:offset+8] = magic_number
        offset += 8
        struct.pack_into('>Q', header, offset, self.root_id)
        offset += 8
        struct.pack_into('>Q', header, offset, self.next_block_id)
        offset += 8
        return bytes(header)
    def read_header(self):
        with open(self.filename, 'rb') as file:
            header = file.read(block_size)
            if len(header) < block_size:
                print("Error: Incomplete header")
                sys.exit(1)
        magic = header[0:8]
        if magic != magic_number:
            print("Error: Invalid file format")
            sys.exit(1)
        self.root_id, = struct.unpack_from('>Q', header, 8)
        self.next_block_id, = struct.unpack_from('>Q', header, 16)
    def write_header(self):
        with open(self.filename, 'r+b') as file:
            header = self.create_header()
            file.seek(0)
            self.write(header)
    def insert_non_full_value(self, node, key, value):
        i = node.number_of_keys - 1 
        if node.is_leaf:
            while i >= 0 and key < node.keys[i]:
                 node.keys[i + 1] = node.keys[i]
                 node.values[i + 1] = node.values[i]
                 i -=1
            node.keys[i + 1] = key
            node.values[i + 1] = value
            node.number_of_keys += 1
            self.write_node(node)
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            child = self.read_node(node.children[i])
            if child.full():
                self.split_child(node, i)
                if key > node.keys[i]:
                    i += 1
                child = self.read_node(node.children[i])
            self.insert_non_full_value(child, key, value)
                 
    def split_child(self, parent, index):
        full_child = self.read_node(parent.children[index])
        new_child = self.allocate_node(parent_id = parent.block_id, is_leaf = full_child.is_leaf)
        mid = min_degree - 1
        new_child.number_of_keys = min_degree - 1
        for i in range(min_degree - 1):
            new_child.keys[i] = full_child.keys[i + min_degree]
            new_child.values[i] = full_child.values[i + min_degree]
        if not full_child.is_leaf:
            for j in range(min_degree):
                new_child.children[j] = full_child.children[j + min_degree]
                if new_child.children[j] != 0: 
                    kid = self.read_node(new_child.children[i])
                    kid.parent_id = new_child.block_id
                    self.write_node(kid)
        full_child.number_of_keys = mid-1
        for h in range(parent.number_of_keys, index, -1):
            parent.children[h + 1] = parent.children[h]
        parent.children[index + 1] = new_child.block_id
        for g in range(parent.number_of_keys -1, index-1, -1, -1):
            parent.keys[g + 1] = parent.keys[g]
            parent.values[g + 1] = parent.values[g]
        parent.keys[index ]= full_child.keys[mid]
        parent.values[index] = full_child.values[mid]
        parent.number_of_keys += 1
        self.write_node(full_child)
        self.write_node(new_child)
        self.write_node(parent)
    def insert_value(self, key, value):
        self.read_header()
        if self.root_id == 0:
            root = self.allocate_node(parent_id=0, is_leaf=True)
            root.keys[0] = key
            root.values[0] = value
            root.number_of_keys = 1
            self.root_id = root.block_id
            self.write_node(root)
            self.write_header()
            return
        root = self.read_node(self.root_id)
        if root.full():
            new_root = self.allocate_node(parent_id=0, is_leaf=False)
            new_root.children[0] = self.root_id
            self.parent_id = new_root.block_id
            self.write_node(root)
            self.split_child(new_root, 0)
            self.root_id = new_root.block_id
            self.write_header()
            self.insert_non_full_value(new_root, key, value)
        else:
            self.insert_non_full_value(root, key, value)
    def search_value(self, key):
        self.read_header()
        if self.root_id == 0:
            return None
        return self.search_node(self.read_node(self.root_id), key)