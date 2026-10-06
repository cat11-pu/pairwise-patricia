"""Unit tests for patricia.core."""

import random
import unittest

from patricia.core import RadixTree


class RadixTreeTest(unittest.TestCase):
    """压缩前缀树的对外行为与结构不变量。"""

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def build(self, keys):
        tree = RadixTree()
        for key in keys:
            tree.insert(key, "v:" + key)
        return tree

    def upward_key(self, node):
        """顺着父指针把标签拼回键。"""
        parts = []
        current = node
        while current.parent is not None:
            parts.append(current.label)
            current = current.parent
        parts.reverse()
        return "".join(parts)

    def check_structure(self, tree, expected):
        """整棵树走一遍：压缩不变量、父子指针、前缀拼接、键集合与枚举序。"""
        expected = set(expected)
        stored = set()
        stack = [(tree.root, "")]
        while stack:
            node, base = stack.pop()
            self.assertEqual(self.upward_key(node), base, "从根向下拼的键要和父指针拼回的键一致")
            if node is tree.root:
                self.assertEqual(node.label, "", "根结点的标签必须是空串")
            else:
                self.assertNotEqual(node.label, "", "非根结点的标签不能是空串")
                self.assertIsNotNone(node.parent, "非根结点必须挂在父结点下面")
                self.assertIs(node.parent.children.get(node.label[0]), node,
                              "父结点的孩子表要按标签首字符挂住这个结点")
            children = list(node.children.values())
            firsts = [child.label[0] for child in children]
            self.assertEqual(len(firsts), len(set(firsts)), "同一个结点的孩子首字符不能重复")
            for child in children:
                self.assertIs(child.parent, node, "孩子的父指针必须指回父结点")
                stack.append((child, base + child.label))
            if node.value is None:
                self.assertTrue(children or node is tree.root, "不带载荷的空结点必须从树上摘掉")
                if node is not tree.root:
                    self.assertGreaterEqual(len(children), 2, "不带载荷的结点至少要两个孩子")
            else:
                stored.add(base)
        self.assertEqual(stored, expected, "树里存的键集合必须与预期一致")
        self.assertEqual(len(tree), len(stored), "len(tree) 必须等于存键数")
        self.assertEqual(tree.keys(), sorted(stored), "枚举结果必须是字典序")

    # ------------------------------------------------------------------
    # cases
    # ------------------------------------------------------------------
    def test_01_empty_tree_and_arguments(self):
        tree = RadixTree()
        self.assertEqual(len(tree), 0)
        self.assertIsNone(tree.search(""))
        self.assertIsNone(tree.search("a"))
        self.assertEqual(tree.keys(), [])
        self.assertEqual(list(tree), [])
        self.assertEqual(tree.prefix_keys(""), [])
        self.assertEqual(tree.prefix_keys("a"), [])
        self.assertIsNone(tree.longest_prefix(""))
        self.assertIsNone(tree.longest_prefix("a"))
        self.assertFalse(tree.delete("a"))
        self.assertFalse(tree.delete(""))
        self.assertNotIn("", tree)
        self.assertNotIn("a", tree)
        for bad in (b"a", 7, None, 1.5, ["a"], ("a",)):
            with self.assertRaises(TypeError):
                tree.insert(bad, "x")
            with self.assertRaises(TypeError):
                tree.search(bad)
            with self.assertRaises(TypeError):
                tree.delete(bad)
            with self.assertRaises(TypeError):
                tree.longest_prefix(bad)
            with self.assertRaises(TypeError):
                tree.prefix_keys(bad)
            with self.assertRaises(TypeError):
                self.assertIn(bad, tree)
        with self.assertRaises(ValueError):
            tree.insert("a", None)
        self.assertEqual(len(tree), 0)
        self.assertEqual(tree.keys(), [])
        # 只有一个键时的插入、查询与删除
        tree.insert("a", "va")
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree.search("a"), "va")
        self.assertIn("a", tree)
        self.assertEqual(tree.keys(), ["a"])
        self.assertEqual(tree.prefix_keys("a"), ["a"])
        self.assertEqual(tree.longest_prefix("a"), ("a", "va"))
        self.assertEqual(tree.longest_prefix("abc"), ("a", "va"))
        self.assertTrue(tree.delete("a"))
        self.assertEqual(len(tree), 0)
        self.assertIsNone(tree.search("a"))
        self.assertNotIn("a", tree)
        self.assertEqual(tree.keys(), [])
        self.assertFalse(tree.delete("a"))

    def test_02_split_and_exact_lookup(self):
        tree = self.build(["cart", "car", "cat", "carbon", "dog"])
        self.assertEqual(len(tree), 5)
        for key in ("cart", "car", "cat", "carbon", "dog"):
            self.assertEqual(tree.search(key), "v:" + key)
            self.assertIn(key, tree)
        for missing in ("", "c", "ca", "caret", "cot", "carts", "carbonx", "do", "doggy"):
            self.assertIsNone(tree.search(missing), "不该命中 %r" % missing)
            self.assertNotIn(missing, tree)
        self.assertEqual(tree.keys(), ["car", "carbon", "cart", "cat", "dog"])
        self.assertEqual(tree.prefix_keys("car"), ["car", "carbon", "cart"])
        self.assertEqual(tree.prefix_keys("ca"), ["car", "carbon", "cart", "cat"])
        self.assertEqual(tree.prefix_keys("cart"), ["cart"])
        self.assertEqual(tree.prefix_keys("cx"), [])

    def test_03_iteration_is_lexicographic(self):
        keys = ["", "a", "ap", "apple", "app", "apricot", "az", "b",
                "ban", "band", "bandana", "banana", "z", "zebra"]
        order = ["banana", "z", "apple", "", "ap", "zebra", "b", "apricot",
                 "band", "a", "bandana", "app", "az", "ban"]
        self.assertEqual(sorted(order), sorted(keys))
        tree = RadixTree()
        for key in order:
            tree.insert(key, "v:" + key)
        expected = sorted(keys)
        self.assertEqual(len(tree), len(expected))
        self.assertEqual(tree.keys(), expected)
        self.assertEqual([key for key, _ in tree], expected)
        self.assertEqual([value for _, value in tree], ["v:" + key for key in expected])
        for prefix in ("", "a", "ap", "app", "b", "ban", "band", "banan", "banax", "z", "zz"):
            self.assertEqual(tree.prefix_keys(prefix),
                             [key for key in expected if key.startswith(prefix)])

    def test_04_structure_after_inserts(self):
        keys = ["", "a", "ab", "abc", "abcd", "abd", "ac", "b", "ba", "bac",
                "bb", "c", "cab", "cabbage", "cabby"]
        order = ["cab", "a", "bb", "abc", "cabbage", "", "ba", "abcd", "c",
                 "ab", "cabby", "ac", "b", "abd", "bac"]
        self.assertEqual(sorted(order), sorted(keys))
        tree = RadixTree()
        for key in order:
            tree.insert(key, "v:" + key)
        for key in keys:
            self.assertEqual(tree.search(key), "v:" + key)
        self.check_structure(tree, keys)

    def test_05_longest_prefix_is_the_longest(self):
        stored = ["", "car", "cart", "cartoon", "dog"]
        tree = self.build(stored)
        queries = ["", "c", "car", "carpet", "carts", "cartoon", "cartoonist",
                   "carto", "dog", "doggy", "dodge", "do", "zebra"]
        for query in queries:
            want = max((key for key in stored if query.startswith(key)), key=len, default=None)
            if want is None:
                self.assertIsNone(tree.longest_prefix(query))
            else:
                self.assertEqual(tree.longest_prefix(query), (want, "v:" + want),
                                 "longest_prefix(%r) 要落在最长的那个前缀上" % query)
        # 查询停在没载荷的分支结点上，也要拿到更短的那个前缀
        bare = self.build(["a", "abx", "aby", "b"])
        cases = [("abz", "a"), ("ab", "a"), ("abyy", "aby"), ("b", "b"),
                 ("bx", "b"), ("c", None), ("", None)]
        for query, want in cases:
            if want is None:
                self.assertIsNone(bare.longest_prefix(query))
            else:
                self.assertEqual(bare.longest_prefix(query), (want, "v:" + want),
                                 "longest_prefix(%r) 丢掉了更短的前缀" % query)

    def test_06_delete_keeps_the_key_set(self):
        keys = ["", "a", "ab", "abc", "b", "ba", "car", "carbon", "cart",
                "cat", "dog", "doge", "z"]
        order = list(keys)
        random.Random(20260116).shuffle(order)
        tree = RadixTree()
        model = {}
        for step, key in enumerate(order):
            tree.insert(key, "v%d" % step)
            model[key] = "v%d" % step
        self.check_structure(tree, model)
        victims = ["cart", "carbon", "abc", "doge", "z", "", "cat", "zzz",
                   "car", "ab", "ba", "a", "b", "dog"]
        for key in victims:
            expect = key in model
            self.assertEqual(tree.delete(key), expect, "delete(%r) 的返回值不对" % key)
            if expect:
                del model[key]
            self.assertEqual(tree.keys(), sorted(model), "删掉 %r 之后键集合不对" % key)
            self.assertEqual(len(tree), len(model), "删掉 %r 之后条数不对" % key)
            for alive in model:
                self.assertEqual(tree.search(alive), model[alive])
            self.assertIsNone(tree.search(key + "x"))
            self.check_structure(tree, model)
        self.assertEqual(model, {})

    def test_07_empty_and_single_character_keys(self):
        tree = self.build(["", "a", "aa", "aab", "ab", "b", "ba"])
        self.assertEqual(len(tree), 7)
        self.assertEqual(tree.search(""), "v:")
        self.assertEqual(tree.keys(), ["", "a", "aa", "aab", "ab", "b", "ba"])
        self.assertEqual(tree.prefix_keys(""), ["", "a", "aa", "aab", "ab", "b", "ba"])
        self.assertEqual(tree.prefix_keys("a"), ["a", "aa", "aab", "ab"])
        self.assertEqual(tree.prefix_keys("aa"), ["aa", "aab"])
        self.assertEqual(tree.prefix_keys("b"), ["b", "ba"])
        self.assertEqual(tree.longest_prefix(""), ("", "v:"))
        self.assertEqual(tree.longest_prefix("a"), ("a", "v:a"))
        self.assertEqual(tree.longest_prefix("aac"), ("aa", "v:aa"))
        self.assertEqual(tree.longest_prefix("b"), ("b", "v:b"))
        self.assertEqual(tree.longest_prefix("bz"), ("b", "v:b"))
        self.assertTrue(tree.delete(""))
        self.assertIsNone(tree.search(""))
        self.assertEqual(tree.keys(), ["a", "aa", "aab", "ab", "b", "ba"])
        self.assertTrue(tree.delete("ba"))
        self.assertIsNone(tree.search("ba"))
        self.assertEqual(tree.keys(), ["a", "aa", "aab", "ab", "b"])
        self.assertEqual(tree.longest_prefix("ba"), ("b", "v:b"))
        self.assertEqual(tree.longest_prefix("abz"), ("ab", "v:ab"))
        self.check_structure(tree, ["a", "aa", "aab", "ab", "b"])
        tree.insert("ba", "again")
        self.assertEqual(tree.search("ba"), "again")
        self.assertEqual(tree.keys(), ["a", "aa", "aab", "ab", "b", "ba"])
        self.check_structure(tree, ["a", "aa", "aab", "ab", "b", "ba"])

    def test_08_model_agreement_on_a_long_run(self):
        rng = random.Random(20260206)
        words = []
        for _ in range(40):
            length = rng.randrange(0, 7)
            words.append("".join(rng.choice("abc") for _ in range(length)))
        tree = RadixTree()
        model = {}
        for step, key in enumerate(words):
            tree.insert(key, "v%d" % step)
            model[key] = "v%d" % step
        self.assertEqual(len(tree), len(model))
        self.assertEqual(tree.keys(), sorted(model))
        for key in model:
            self.assertEqual(tree.search(key), model[key])
        self.check_structure(tree, model)
        victims = sorted(model)
        rng.shuffle(victims)
        removed = victims[:len(victims) // 2]
        for key in removed:
            self.assertTrue(tree.delete(key))
            del model[key]
        self.assertEqual(len(tree), len(model))
        self.assertEqual(tree.keys(), sorted(model))
        for key in model:
            self.assertEqual(tree.search(key), model[key])
        for key in removed:
            self.assertIsNone(tree.search(key))
        self.check_structure(tree, model)
        for prefix in ("", "a", "ab", "b", "ba", "c", "abc"):
            self.assertEqual(tree.prefix_keys(prefix),
                             [key for key in sorted(model) if key.startswith(prefix)])

    def test_09_compress_around_deletes(self):
        tree = self.build(["car", "cart", "cat", "carbon"])
        self.assertEqual(tree.keys(), ["car", "carbon", "cart", "cat"])
        self.assertTrue(tree.delete("car"))
        self.assertEqual(tree.keys(), ["carbon", "cart", "cat"])
        for key in ("carbon", "cart", "cat"):
            self.assertEqual(tree.search(key), "v:" + key)
        self.check_structure(tree, ["carbon", "cart", "cat"])
        self.assertTrue(tree.delete("carbon"))
        self.assertTrue(tree.delete("cart"))
        self.assertEqual(tree.keys(), ["cat"])
        self.assertEqual(tree.search("cat"), "v:cat")
        self.check_structure(tree, ["cat"])
        self.assertTrue(tree.delete("cat"))
        self.assertEqual(len(tree), 0)
        self.assertEqual(tree.keys(), [])
        self.check_structure(tree, [])
        tree.insert("cat", "again")
        self.assertEqual(tree.keys(), ["cat"])
        self.assertEqual(tree.search("cat"), "again")
        self.check_structure(tree, ["cat"])


if __name__ == "__main__":
    unittest.main()
