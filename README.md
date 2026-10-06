# patricia

一个纯标准库、可确定复现的压缩前缀树（radix tree / Patricia trie）内核：按公共前缀
分裂边、按字典序枚举键、支持最长前缀匹配，删除键之后把只剩一段边的路径重新压紧。
内核不读时钟、不起线程、不做 I/O，也不使用随机数。

## 目录

- `patricia/core.py`：内核实现（`Node`、`RadixTree`）
- `tests/test_core.py`：行为与结构不变量测试

## 语义约定

- 键是 `str`，空串是合法键；载荷是除 `None` 以外的任意对象。键不是 `str` 抛
  `TypeError`，载荷是 `None` 抛 `ValueError`。
- 每个结点带一段边标签：根结点的标签为空串，其余结点的标签非空。结点的键等于从根
  到它路径上所有标签的拼接；结点带载荷时，它的键就是一个已存储的键。
- 压缩不变量：不带载荷的非根结点至少有两个孩子，只有一个孩子的中间结点会被折叠进
  它的孩子；根结点允许只有一个孩子。同一个结点的两个孩子，标签首字符互不相同。
- 对外接口：

      tree = RadixTree()
      tree.insert("car", "v-car")     # 存入键值对，键已存在时覆盖载荷
      tree.search("car")              # 载荷；没存过返回 None
      "car" in tree                   # 是否存过这个键
      tree.delete("car")              # 删掉了返回 True，本来没存返回 False
      tree.longest_prefix("carpet")   # 最长的、作为查询前缀的已存储键 -> ("car", "v-car")
      tree.prefix_keys("car")         # 以该前缀开头的键，按字典序
      tree.keys()                     # 所有已存储键，按字典序
      list(tree)                      # [(键, 载荷)]，按字典序
      len(tree)                       # 存了多少个键

## 怎么跑测试

在项目根目录执行：

    python3 -m unittest discover -s tests -v

Windows 上把 `python3` 换成你的解释器路径，例如：

    C:/Users/<你>/AppData/Local/Programs/Python/Python313/python.exe -m unittest discover -s tests -v

只依赖 Python 3 标准库，不需要装任何包，也不需要联网。
