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