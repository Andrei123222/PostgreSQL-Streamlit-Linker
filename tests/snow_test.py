import unittest
from pages.snow import updateData,insertData,deleteData

class TestAppUpdate(unittest.TestCase):
    def test_errors(self):
        self.assertRaises(TypeError,updateData,0)
        self.assertRaises(TypeError,updateData,0.5)
        self.assertRaises(TypeError,updateData,True)

        self.assertRaises(TypeError,updateData,"")
        self.assertRaises(TypeError,updateData,"mama")
        self.assertRaises(TypeError,updateData,"dd")

        self.assertRaises(IndexError,updateData,"brand","bb","bbn","bbnb")
        self.assertRaises(IndexError,updateData,"brand","bbd","bbh","bbk","bbl","bbv")

        self.assertRaises(IndexError,updateData,"device","dd","ddv","ddc","dds")
        self.assertRaises(IndexError,updateData,"device","dda","dde","ddq","ddt","ddy","ddz")

        self.assertRaises(IndexError,updateData,"stocks","cca","ccz","cc","ccc")
        self.assertRaises(IndexError,updateData,"stocks","ccg","cck","cci","ccr","cco","ccp")

class TestAppInsert(unittest.TestCase):
    def test_errors(self):
        self.assertRaises(TypeError,insertData,0)
        self.assertRaises(TypeError,insertData,0.5)
        self.assertRaises(TypeError,insertData,True)

        self.assertRaises(TypeError,insertData,"")
        self.assertRaises(TypeError,insertData,"mama")
        self.assertRaises(TypeError,insertData,"dd")

        self.assertRaises(IndexError,insertData,"brand","bb","bbnb")
        self.assertRaises(IndexError,insertData,"brand","bbd","bbh","bbk","bbv")

        self.assertRaises(IndexError,insertData,"device","dd","ddv","ddc","dds")
        self.assertRaises(IndexError,insertData,"device","dda","dde","ddq","ddt","ddy","ddz")

        self.assertRaises(IndexError,insertData,"stocks","cca","ccc")
        self.assertRaises(IndexError,insertData,"stocks","ccg","cck","cci","ccr")