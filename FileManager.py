import sys
import os
import struct

block_size = 512
magic_number = b'4348PRJ3'
min_degree = 10
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
        struct.pack_into('>Q', data, offset, self.number_of_keys)
        offset += 8
        for i in range(max_keys):
            struct.pack_into('>Q', data, offset, self.keys[i])
            offset += 8
        for j in range(max_keys): 
            struct.pack_into('>Q', data, offset, self.values[j])
            offset += 8
        for i in range(max_children):
            struct.pack_into('>Q', data, offset, self.children[i])
            offset += 8
        return bytes(data)
    @staticmethod
    def deserialize(data):
        node = FileManager(block_id=0)
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
        for i in range(max_keys):
            node.values[i], = struct.unpack_from('>Q', data, offset)
            offset += 8
        for i in range(max_children):
            node.children[i], = struct.unpack_from('>Q', data, offset)
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
        with open(self.filename, 'r+b') as file:
            file.seek(node.block_id * block_size)
            file.write(node.serialize())
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
            file.write(header)
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
                    kid = self.read_node(new_child.children[j])
                    kid.parent_id = new_child.block_id
                    self.write_node(kid)
        full_child.number_of_keys = min_degree-1
        for h in range(parent.number_of_keys, index, -1):
            parent.children[h + 1] = parent.children[h]
        parent.children[index + 1] = new_child.block_id
        for g in range(parent.number_of_keys -1, index-1, -1):
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
            root.parent_id = new_root.block_id
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
    def search_node(self, node, key):
        i = 0
        while i < node.number_of_keys and key > node.keys[i]:
            i += 1
        if i < node.number_of_keys and key ==node.keys[i]:
            return (node.keys[i], node.values[i])
        if node.is_leaf:
            return None
        return self.search_node(self.read_node(node.children[i]), key)
    def print_tree(self):
        self.read_header()
        if self.root_id == 0:
            print("B-Tree is emtpy nothing to print")
            return
        self.print_node(self.read_node(self.root_id))
    def print_node(self, node):
        var = 0
        for j in range(node.number_of_keys):
            if not node.is_leaf:
                kid = self.read_node(node.children[j])
                self.print_node(kid)
            print(f"{node.keys[j]}, {node.values[j]}")
        if not node.is_leaf:
            kid = self.read_node(node.children[node.number_of_keys])
            self.print_node(kid)
    def extract_node_data(self, output):
        #check if the file already exist in the system
        if os.path.exists(output):
            print(f"Error: File '{output}' already exists")
            sys.exit(1)
        #file exists
        self.read_header()
        with open(output, 'w') as file: # open the output file with write permissions 
            if self.root_id != 0:
                self.extract_node(self.read_node(self.root_id), file)
        print(f"Extracted to the output file name: {output}")
    def extract_node(self, node, file):
        for i in range(node.number_of_keys):
            if not node.is_leaf:
                self.extract_node(self.read_node(node.children[i]), file)
            # write into the output the key and value pairs and then go to newline
            file.write(f"{node.keys[i]},{node.values[i]}\n")
        if not node.is_leaf:
            self.extract_node(self.read_node(node.children[node.number_of_keys]), file)
def main():
    if len(sys.argv) < 2:
        print("Usage: project3 <command> [arguments...]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "create":
        if len(sys.argv) < 3:
            print("Error: Missing filename argument")
            sys.exit(1)
        filename = sys.argv[2]
        btree = BTreeIndex(filename)
        btree.create_node()
    
    elif command == "insert":
        if len(sys.argv) < 5:
            print("Error: Missing arguments for insert")
            sys.exit(1)
        filename = sys.argv[2]
        
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' does not exist")
            sys.exit(1)
        
        try:
            key = int(sys.argv[3])
            value = int(sys.argv[4])
        except ValueError:
            print("Error: Key and value must be integers")
            sys.exit(1)
        
        btree = BTreeIndex(filename)
        btree.insert_value(key, value)
        print(f"Inserted: {key} -> {value}")
    
    elif command == "search":
        if len(sys.argv) < 4:
            print("Error: Missing arguments for search")
            sys.exit(1)
        filename = sys.argv[2]
        
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' does not exist")
            sys.exit(1)
        
        try:
            key = int(sys.argv[3])
        except ValueError:
            print("Error: Key must be an integer")
            sys.exit(1)
        
        btree = BTreeIndex(filename)
        result = btree.search_value(key)
        
        if result:
            print(f"{result[0]}, {result[1]}")
        else:
            print(f"Error: Key {key} not found")
    
    elif command == "load":
        if len(sys.argv) < 4:
            print("Error: Missing arguments for load")
            sys.exit(1)
        filename = sys.argv[2]
        csv_file = sys.argv[3]
        
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' does not exist")
            sys.exit(1)
        
        if not os.path.exists(csv_file):
            print(f"Error: CSV file '{csv_file}' does not exist")
            sys.exit(1)
        
        btree = BTreeIndex(filename)
        
        with open(csv_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(',')
                    if len(parts) == 2:
                        try:
                            key = int(parts[0])
                            value = int(parts[1])
                            btree.insert_value(key, value)
                        except ValueError:
                            print(f"Warning: Skipping invalid line: {line}")
        
        print(f"Loaded data from: {csv_file}")
    
    elif command == "print":
        if len(sys.argv) < 3:
            print("Error: Missing filename argument")
            sys.exit(1)
        filename = sys.argv[2]
        
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' does not exist")
            sys.exit(1)
        
        btree = BTreeIndex(filename)
        btree.print_tree()
    
    elif command == "extract":
        if len(sys.argv) < 4:
            print("Error: Missing arguments for extract")
            sys.exit(1)
        filename = sys.argv[2]
        output_file = sys.argv[3]
        
        if not os.path.exists(filename):
            print(f"Error: The file: '{filename}' does not exist")
            sys.exit(1)
        
        btree = BTreeIndex(filename)
        btree.extract_node_data(output_file)
    
    else:
        print(f"Error: Unknown command: '{command}'")
        sys.exit(1)

if __name__ == "__main__":
    main()