import unittest
def over_viditelnost(viditelnost,prihlaseny = False,username = ""):
    if viditelnost == None: return False
    if("*" in viditelnost): return True
    if("+" in viditelnost and prihlaseny):return True
    if(prihlaseny and username in viditelnost):
        return True
    return False

class Views_py(unittest.TestCase):
    def test_viditelnost(self):
        self.assertEqual(over_viditelnost(["*","čokolvek_ine"]), True)
        self.assertEqual(over_viditelnost(None), False)
        self.assertEqual(over_viditelnost([]), False)
        self.assertEqual(over_viditelnost([],True,"username"), False)
        self.assertEqual(over_viditelnost(["username"], True, "username"), True)
        self.assertEqual(over_viditelnost(["username"], False, "username"), False)
        self.assertEqual(over_viditelnost(["username2","+"], True, "username"), True)
        self.assertEqual(over_viditelnost(["username2", "+"], False, "username"), False)
        self.assertEqual(over_viditelnost(["username2"], True, "username"), False)
        self.assertEqual(over_viditelnost(["*username"], True, "username"), False)

if __name__ == '__main__':
    unittest.main()