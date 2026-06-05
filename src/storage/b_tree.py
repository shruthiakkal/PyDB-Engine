import threading
from typing import Any, TypeAlias

Value: TypeAlias = Any
Row: TypeAlias = dict[str, Value]


class BTreeNode:
    def __init__(self, leaf: bool = True):
        self.leaf = leaf
        #  store tuples of (column_value, [row_id_1, row_id_2, ...])
        # Example: [ ("alice@email.com",), ("bob@email.com",) ]
        self.keys: list[tuple[Any, list[int]]] = []

        # Pointers to child BTreeNodes
        self.children: list["BTreeNode"] = []


class BTree:
    def __init__(self, min_degree: int = 3):
        self.root = BTreeNode(leaf=True)
        self.t = min_degree  # t=3 means max 5 keys per node

        # ... inside the BTree class

    def exists(self, key: Any) -> bool:
        """Public method to check if a key exists."""
        return self._search(self.root, key) is not None

    def _search(self, node: BTreeNode, key: Any) -> BTreeNode | None:
        """Internal recursive search method."""
        i = 0

        # 1. Find the first key greater than or equal to the search key
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        # 2. If we found the exact key, return this node!
        if i < len(node.keys) and key == node.keys[i]:
            return node

        # 3. If we hit a leaf and didn't find it, the key does not exist.
        if node.leaf:
            return None

        # 4. Otherwise, dive down into the appropriate child node.
        return self._search(node.children[i], key)

    # ... inside the BTree class

    def insert(self, key: Any, row_id: int) -> None:
        """Public method to insert a key and row_id."""
        root = self.root

        # 1. Is the root entirely full?
        if len(root.keys) == (2 * self.t) - 1:
            # The root is full. We must create a new empty root.
            new_root = BTreeNode(leaf=False)
            self.root = new_root
            new_root.children.append(root)

            # Split the old root and move one key up to the new root
            self._split_child(new_root, 0)

            # Now insert into the non-full tree
            self._insert_non_full(new_root, key, row_id)
        else:
            # Root is not full, proceed normally
            self._insert_non_full(root, key, row_id)

    def _insert_non_full(self, node: BTreeNode, key: Any, row_id: int) -> None:
        """Inserts a key into a node that is guaranteed NOT to be full."""
        i = len(node.keys) - 1

        if node.leaf:
            # 1. If it's a leaf, find where the key goes

            # Check if key already exists in this node to append row_id
            for idx, (k, row_ids) in enumerate(node.keys):
                if k == key:
                    row_ids.append(row_id)
                    return

            # Otherwise, make room and insert the new key tuple in sorted order
            node.keys.append((None, []))  # Dummy space
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = (key, [row_id])

        else:
            # 2. If it's an internal node, find the correct child to dive into
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1

            # Check if the child we want to dive into is full
            if len(node.children[i].keys) == (2 * self.t) - 1:
                # Split the child before diving into it
                self._split_child(node, i)

                # After splitting, the middle key of the child moved up.
                # We need to check if we should dive into the left or right newly split child.
                if key > node.keys[i]:
                    i += 1

            # Recursively insert into the guaranteed non-full child
            self._insert_non_full(node.children[i], key, row_id)

    def _split_child(self, parent: BTreeNode, i: int) -> None:
        """Splits the i-th child of the parent node."""
        t = self.t
        full_child = parent.children[i]

        # Create a new node to hold the right half of the full_child
        new_child = BTreeNode(leaf=full_child.leaf)

        # Move the rightmost (t-1) keys from the full child to the new child
        new_child.keys = full_child.keys[t : (2 * t - 1)]

        # If not a leaf, also move the rightmost t children pointers
        if not full_child.leaf:
            new_child.children = full_child.children[t : 2 * t]

        # Truncate the old full child so it only holds the left half
        # (Save the median key to push up to the parent)
        median_key_tuple = full_child.keys[t - 1]
        full_child.keys = full_child.keys[0 : t - 1]
        if not full_child.leaf:
            full_child.children = full_child.children[0:t]

        # Make room in the parent's children array for the new child
        parent.children.insert(i + 1, new_child)

        # Pull the median key up into the parent's keys array
        parent.keys.insert(i, median_key_tuple)


class BTreeTable:
    def __init__(
        self, name: str, columns: list[str], primary_key: str | None = None
    ) -> None:
        self.name = name
        self.columns = columns
        self.primary_key = primary_key

        self.lock = threading.Lock()

        # HEAP
        # Central storage mapping row_id -> Row
        self.storage: dict[int, Row] = {}
        # self.next_row_id acts as the physical address for where the row lives in memory (your Heap). In almost all major databases, internal pointers are tightly
        # packed integers. For example, PostgreSQL uses a 6-byte integer system (Block Number + Line Pointer) to track row locations.
        self.next_row_id: int = 1

        # indexes: mapping index name to BTree iinstance
        # A BTree will internally store { column_value: [row_id_1, row_id_2] }
        self.indexes: dict[str, BTree] = {}

        if primary_key:
            self.indexes[primary_key] = BTree()

    def insert(self, columns: list[str], values: list[Any]) -> Row:
        if len(columns) != len(values):
            raise ValueError("Column count does not match value count")

        row: Row = dict(zip(columns, values))

        with self.lock:
            # --- PHASE 1: Pre-computation ---
            current_row_id = self.next_row_id

            # --- PHASE 2: Validation ---
            if self.primary_key and self.primary_key in row:
                pk_value = row[self.primary_key]
                pk_btree: BTree = self.indexes[self.primary_key]

                # BTree search: O(log N)
                if pk_btree.exists(pk_value):
                    raise ValueError(
                        f"Unique constraint violation: {self.primary_key} '{pk_value}' already exists."
                    )

            # --- PHASE 3: Storage Write ---
            # O(1) Hash Map insert
            self.storage[current_row_id] = row
            self.next_row_id += 1

            # --- PHASE 4: Index Write ---
            # O(log N) B-Tree inserts
            for col_name, btree_index in self.indexes.items():
                if col_name in row:
                    col_value = row[col_name]
                    # You might need to handle duplicate values in non-unique indexes
                    # by storing a list of row_ids inside the BTree leaf node.
                    btree_index.insert(col_value, current_row_id)

            return row
