- 12/06/2025: Session 1 11:46 am
    - created intial project and did first push
    -before i created the repo but didn't start on it
    - first started to intialize some variables and defined def __init__ for the FileManager class
    - finished the serialize and deserialize methods 
-12/08/2025: Session 2 7:00 am
    - worked on creating rest of the function to iplement the BTree file manager
    - created BTreeIndex class 
        - within the create_node function, we first check if the file specificed already exists and if so return a response and exit, otherwise create and open the file
        - created the create_node, insert_value, write header, read header, create header, etc. ( couldnt finish the inert half child, search methods, and insert non full notes but pushing now at 5:26 pm to save progress )
-12/09/2025: session 3 3:42 pm
    - started back up another session to finish insert_non_full_value(self, node, key, value) and the other insert methods
    - heard from fellow seatmate that i might need to have a recusrive method to split the nodes so will have to consider that 
    - started to add comment ins extract_node_data(self, output): to keep track of my development 
    - also fixed a earlier mistake where i put '>I' instead of '>Q' where is accepted 4 bytes instead of 8 bytes 
    -finished the FileManager.py and now testing it out on creating a index myindex.idx
-12/10/2025: Session 4 12:50 am
    - was able to run the tests and it seemed to work now just adding some instructions to run the program

How to execute: 
- To create a file in the program you must specify a not already existing file to create: 
    ex: python3 FileManager.py create test.idx (will create the test.idx file if it does exist )
    default structure example: python3 FileManager.py create <insert file name here>.idx 
- If you specify a file that already exist it will return: File aready exists
- If you want to insert values into the program:
    default structure example python3 FileManager.py insert <insert file name here>.idx <insert key> <insert value>
- If you want to search for values in the program:
    default structure example: python3 FileManager.py search <insert file name here>.idx <insert key>
- if you want to print the btree:
    default structure example: python3 FileManager.py print <insert file name here>.idx