import ipaddress

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.value = None

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, pattern, value=None):
        node = self.root
        for part in pattern.split('.'):
            if part not in node.children:
                node.children[part] = TrieNode()
            node = node.children[part]
        node.is_end = True
        node.value = value

    def search(self, pattern):
        node = self.root
        for part in pattern.split('.'):
            if part not in node.children:
                return None
            node = node.children[part]
        return node.value if node.is_end else None

    def prefix_match(self, prefix):
        node = self.root
        for part in prefix.split('.'):
            if part not in node.children:
                return []
            node = node.children[part]
        results = []
        self._collect(node, prefix, results)
        return results

    def _collect(self, node, prefix, results):
        if node.is_end:
            results.append((prefix, node.value))
        for part, child in node.children.items():
            self._collect(child, f"{prefix}.{part}", results)

    def delete(self, pattern):
        def _delete(node, parts, depth):
            if depth == len(parts):
                if not node.is_end:
                    return False
                node.is_end = False
                node.value = None
                return len(node.children) == 0
            part = parts[depth]
            if part not in node.children:
                return False
            should_delete = _delete(node.children[part], parts, depth+1)
            if should_delete:
                del node.children[part]
                return not node.is_end and len(node.children) == 0
            return False
        _delete(self.root, pattern.split('.'), 0) 