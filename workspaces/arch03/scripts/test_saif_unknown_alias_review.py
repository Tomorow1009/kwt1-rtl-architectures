import unittest
import saif_unknown_alias_review as review


class WireAliasTests(unittest.TestCase):
    def test_escaped_and_vector_aliases(self):
        self.assertEqual(review.wire(r'\ML_int[8][63] '), 'ML_int[8][63]')
        self.assertEqual(review.wire('B [63]'), 'B[63]')
        graph = review.graph(r'assign B[63] = \ML_int[8][63] ; assign temp = B[63];')
        self.assertEqual(review.aliases('B[63]', graph), {'B[63]', 'ML_int[8][63]', 'temp'})

    def test_logic_and_constants_are_not_wire_equivalences(self):
        for expr in ("1'bx", "1'b0", '~A', 'A & B', '{A, B}', 'A[7:0]'):
            self.assertIsNone(review.wire(expr))
        self.assertEqual(dict(review.graph("assign A = 1'b0; assign B = ~A;")), {})

    def test_cycles_terminate_without_crossing_scopes(self):
        graph = review.graph('assign A=B; assign B=C; assign C=A; assign other=X;')
        self.assertEqual(review.aliases('A', graph), {'A', 'B', 'C'})
        self.assertEqual(review.aliases('absent', graph), {'absent'})


if __name__ == '__main__':
    unittest.main()
