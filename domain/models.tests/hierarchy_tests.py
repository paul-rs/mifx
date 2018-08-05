import unittest
from models.hierarchy import Hierarchy
from models.project import Project


class HierarchyTests(unittest.TestCase):

    def test_root(self):
        hierarchy = Hierarchy(1, 'Project root', None)
        invalid_values = [
            Project(1, None, None, 0, 0),
            'None',
            123
        ]

        for val in invalid_values:
            with self.assertRaises(TypeError):
                hierarchy.root = val
