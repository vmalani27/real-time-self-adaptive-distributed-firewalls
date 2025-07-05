import unittest
from central_engine.trie_engine import Trie

class TestTrie(unittest.TestCase):
    def setUp(self):
        self.trie = Trie()

    def test_insert_and_search(self):
        self.trie.insert('192.168.1.1', 'A')
        self.assertEqual(self.trie.search('192.168.1.1'), 'A')
        self.assertIsNone(self.trie.search('10.0.0.1'))

    def test_prefix_and_delete(self):
        self.trie.insert('192.168.1.1', 'A')
        self.trie.insert('192.168.1.2', 'B')
        matches = self.trie.prefix_match('192.168.1')
        self.assertIn(('192.168.1.1', 'A'), matches)
        self.assertIn(('192.168.1.2', 'B'), matches)
        self.trie.delete('192.168.1.1')
        self.assertIsNone(self.trie.search('192.168.1.1'))

if __name__ == "__main__":
    unittest.main() 