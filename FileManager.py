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
    
