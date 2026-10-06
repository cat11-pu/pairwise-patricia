"""patricia：压缩前缀树内核（公共前缀分裂、路径压缩、最长前缀匹配、字典序枚举）。

对外入口：
    Node        树里的一个结点：一段边标签 + 一份载荷 + 一张孩子表
    RadixTree   压缩前缀树：插入、查询、删除、前缀枚举与最长前缀匹配
"""

from .core import Node, RadixTree

__all__ = ["Node", "RadixTree"]
