import unittest
from utils.parser import parse_template

class TestParser(unittest.TestCase):
    def test_basic_excel_template(self):
        text = """
        product name: Bone Straight 
        slug: bone-straight
        product code: BS-01
        original price: 200
        discount price: 150
        stock: available
        capsize: Medium, Large
        inches: 10, 12, 14
        bundles: 3
        color: Natural Black, Red
        parting: Middle Part, Free Part
        styling: Straight
        description: Great quality
        preorder: available
        """
        data = parse_template(text)
        self.assertEqual(data.get('name'), 'Bone Straight')
        self.assertEqual(data.get('slug'), 'bone-straight')
        self.assertEqual(data.get('product_code'), 'BS-01')
        self.assertEqual(data.get('original_price'), 200.0)
        self.assertEqual(data.get('price'), 150.0)
        self.assertEqual(data.get('stock'), 99)
        self.assertFalse(data.get('is_preorder', True))  # Should be False
        self.assertEqual(data.get('cap_sizes'), ['Medium', 'Large'])
        self.assertEqual(data.get('lengths'), ['10', '12', '14'])
        self.assertEqual(data.get('bundles'), ['3'])
        self.assertEqual(data.get('colors'), ['Natural Black', 'Red'])
        self.assertEqual(data.get('parting_options'), ['Middle Part', 'Free Part'])
        self.assertEqual(data.get('styling'), ['Straight'])
        self.assertEqual(data.get('description'), 'Great quality')
        
    def test_preorder_stock(self):
        text = """
        Product name: curls
        Stock: PRE ORDER
        """
        data = parse_template(text)
        self.assertEqual(data.get('stock'), 0)
        self.assertTrue(data.get('is_preorder'))

    def test_numeric_stock(self):
        text = """
        Product name: curls
        Stock: 15
        """
        data = parse_template(text)
        self.assertEqual(data.get('stock'), 15)
        self.assertNotIn('is_preorder', data)
        
    def test_ignore_no_colon(self):
        text = """
        Product name: curls
        Some text without colon
        Stock: 15
        """
        data = parse_template(text)
        self.assertEqual(data.get('stock'), 15)

    def test_length_prices(self):
        text = """
        product name: Bone Straight 
        slug: bone-straight
        stock: available
        inches: 10:$150, 12:$170, 14: 200
        """
        data = parse_template(text)
        self.assertEqual(data.get('lengths'), ['10', '12', '14'])
        self.assertEqual(data.get('length_prices'), [
            {'length': '10', 'price': 150.0},
            {'length': '12', 'price': 170.0},
            {'length': '14', 'price': 200.0}
        ])

if __name__ == '__main__':
    unittest.main()
