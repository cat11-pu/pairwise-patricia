"""Compressed prefix trie (radix tree) core.

Design notes
------------
* 每个结点带一段边标签：根结点标签为空串，其余结点标签非空。结点的键是从根
  到该结点路径上所有标签的拼接；结点带载荷时，它的键就是一个已存储的键。
* 压缩不变量：不带载荷的非根结点至少有两个孩子，只有一个孩子的中间结点一律
  折叠进孩子；根结点允许只有一个孩子。
* 同一结点的两个孩子，标签首字符互不相同，孩子表按首字符索引。
* 键是 str，载荷是除 None 以外的任意对象。
"""

__all__ = ["Node", "RadixTree"]


class Node:
    """一段边：一个标签、一份载荷和一张孩子表。"""

    __slots__ = ("label", "value", "children", "parent")

    def __init__(self, label=""):
        self.label = label
        self.value = None
        self.children = {}
        self.parent = None


class RadixTree:
    """文本键上的压缩前缀树。"""

    def __init__(self):
        self.root = Node()
        self.size = 0

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------
    @staticmethod
    def _check_key(key):
        if not isinstance(key, str):
            raise TypeError("key must be a str")

    @staticmethod
    def _check_value(value):
        if value is None:
            raise ValueError("value must not be None")

    @staticmethod
    def _common(label, rest):
        """两段文本的公共前缀长度，不超过较短的那一段。"""
        span = 0
        limit = min(len(label), len(rest))
        while span < limit and label[span] == rest[span]:
            span += 1
        return span

    def _locate(self, key):
        """一路向下比较整段边标签，返回 (结点, 该结点覆盖的键长)。"""
        node = self.root
        offset = 0
        while offset < len(key):
            child = node.children.get(key[offset])
            if child is None:
                break
            if self._common(child.label, key[offset:]) < 1:
                break
            offset += len(child.label)
            node = child
        return node, offset

    def _exact(self, key):
        """恰好存储 `key` 的结点；没有则返回 None。"""
        node, offset = self._locate(key)
        if node.value is not None:
            return node
        return None

    @staticmethod
    def _attach(parent, node, value):
        """把新结点挂到父结点下面。"""
        node.value = value
        node.parent = parent
        parent.children[node.label[0]] = node

    def _collect(self, node, base):
        """子树里 (键, 载荷) 的字典序列表。"""
        pairs = []
        if node.value is not None:
            pairs.append((base, node.value))
        for first in sorted(node.children, reverse=True):
            child = node.children[first]
            pairs.extend(self._collect(child, base + child.label))
        return pairs

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    def search(self, key):
        """`key` 对应的载荷；没有存过返回 None。"""
        self._check_key(key)
        node = self._exact(key)
        return None if node is None else node.value

    def __contains__(self, key):
        self._check_key(key)
        return self._exact(key) is not None

    def longest_prefix(self, key):
        """最长的、作为 `key` 前缀的已存储键，返回 (键, 载荷)；没有返回 None。"""
        self._check_key(key)
        node = self.root
        offset = 0
        best = None
        while offset < len(key):
            child = node.children.get(key[offset])
            if child is None:
                break
            if not key.startswith(child.label, offset):
                break
            offset += len(child.label)
            node = child
        if node.value is not None:
            best = (key[:offset], node.value)
        return best

    def prefix_keys(self, prefix):
        """所有以 `prefix` 开头的已存储键，按字典序。"""
        self._check_key(prefix)
        return [key for key, _ in self if key.startswith(prefix)]

    def keys(self):
        """所有已存储键，按字典序。"""
        return [key for key, _ in self]

    def __iter__(self):
        return iter(self._collect(self.root, ""))

    def __len__(self):
        return self.size

    # ------------------------------------------------------------------
    # 写入
    # ------------------------------------------------------------------
    def insert(self, key, value):
        """存入键值对；键已存在时覆盖载荷。"""
        self._check_key(key)
        self._check_value(value)
        node, offset = self._locate(key)
        rest = key[offset:]
        if not rest:
            self.size += 1
            node.value = value
            return
        child = node.children.get(rest[0])
        if child is None:
            self._attach(node, Node(rest), value)
            self.size += 1
            return
        label = child.label
        common = self._common(label, rest)
        middle = Node(label)
        middle.parent = node
        node.children[rest[0]] = middle
        child.label = label[common:]
        child.parent = middle
        middle.children[child.label[0]] = child
        if common == len(rest):
            middle.value = value
        else:
            self._attach(middle, Node(rest[common:]), value)
        self.size += 1

    def delete(self, key):
        """删除键；删掉了返回 True，本来没存返回 False。"""
        self._check_key(key)
        node = self._exact(key)
        if node is None:
            return False
        self._compress(node)
        node.value = None
        self.size -= 1
        return True

    def _compress(self, node):
        """从 `node` 一路向上，把压缩不变量恢复好。"""
        current = node
        while current is not self.root:
            parent = current.parent
            if current.value is None:
                if not current.children:
                    del parent.children[current.label[0]]
                    current.parent = None
            current = parent
