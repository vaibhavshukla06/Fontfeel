import unittest
import os
import sys

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from font_validator import determine_font_style

class TestFontValidator(unittest.TestCase):
    """Test cases for the font validator module."""
    
    def test_determine_font_style_from_name(self):
        """Test that font style can be determined from the name."""
        # Mock a font object with a name table
        class MockFont:
            class MockNameTable:
                def getName(self, nameID, platformID, platEncID, langID):
                    class MockName:
                        def toStr(self):
                            return "Roboto Sans"
                    return MockName()
            
            def __init__(self):
                self['name'] = self.MockNameTable()
                
            def __getitem__(self, key):
                if key == 'name':
                    return self['name']
                return None
        
        mock_font = MockFont()
        self.assertEqual(determine_font_style(mock_font), "sans-serif")
    
    # Add more tests as needed

if __name__ == '__main__':
    unittest.main() 