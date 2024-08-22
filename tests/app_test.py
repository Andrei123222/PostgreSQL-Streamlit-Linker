import unittest
from app import updateItem,insertInfo,deleteItem


class testAppUpdate(unittest.TestCase):
    def test_errors(self):
        with self.assertRaises(TypeError, msg="First argument must be a string(table's name)"):
            updateItem(0,)
    
        with self.assertRaises(TypeError, msg="First argument must be a string(table's name)"):
            updateItem(0.5,)

        with self.assertRaises(TypeError, msg="First argument must be a string(table's name)"):
            updateItem(True,)

        self.assertRaises(TypeError, updateItem, "mama")
        self.assertRaises(TypeError, updateItem, "")
        self.assertRaises(TypeError, updateItem, "d")

        self.assertRaises(IndexError, updateItem,"types","foo","foo")
        self.assertRaises(IndexError, updateItem,"types","foo","foosp","foop","fofoo","foop")
        self.assertRaises(IndexError, updateItem,"pet","foo","foop")
        self.assertRaises(IndexError, updateItem,"pet","foo","foop","foofoo","floo")
        self.assertRaises(IndexError, updateItem,"person","foo","foopt")
        self.assertRaises(IndexError, updateItem,"person","foo","foop","foog","foohfoo","fogo","fop")
        
class testAppInsert(unittest.TestCase):
    def test_errors(self):
        self.assertRaises(TypeError, insertInfo, 1)
        self.assertRaises(TypeError, insertInfo, 0.5)
        self.assertRaises(TypeError, insertInfo, True)

        self.assertRaises(TypeError, insertInfo, "baba")
        self.assertRaises(TypeError, insertInfo, "True")
        self.assertRaises(TypeError, insertInfo, "no")

        self.assertRaises(IndexError, insertInfo, "types","boo","boooboo")
        self.assertRaises(IndexError, insertInfo, "types","boo","boook","boookooo","coockoo")

        self.assertRaises(IndexError, insertInfo, "pet","bookt", "bookooo")
        self.assertRaises(IndexError, insertInfo, "pet","boo","booknook","nookoo","nonoo","bob")

        self.assertRaises(IndexError, insertInfo, "person","boo","boooboo","bobo")
        self.assertRaises(IndexError, insertInfo, "person","boo","bobok","bobon","nobon","bonbon")

class testAppDelete(unittest.TestCase):
    def test_errors(self):
        self.assertRaises(TypeError, deleteItem, "Dd")
        self.assertRaises(TypeError, deleteItem, "")
        self.assertRaises(TypeError, deleteItem, "mama")