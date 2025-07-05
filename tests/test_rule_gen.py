import unittest
from central_engine.rule_generator import generate_nft_rule

class TestRuleGen(unittest.TestCase):
    def test_valid_rule(self):
        d = {'source_ip': '192.168.1.100', 'dest_port': 80, 'attack_type': 'syn_flood'}
        out = generate_nft_rule(d)
        self.assertIn('rule_str', out)
        self.assertIn('metadata', out)
        self.assertEqual(out['metadata']['source_ip'], '192.168.1.100')
        self.assertEqual(out['metadata']['dest_port'], 80)

    def test_invalid_ip(self):
        d = {'source_ip': 'bad_ip', 'dest_port': 80, 'attack_type': 'syn_flood'}
        with self.assertRaises(ValueError):
            generate_nft_rule(d)

if __name__ == "__main__":
    unittest.main() 