import unittest
import jotihunt_api
import telegramhandler

__author__ = 'Mattijn'



class FlattenTest(unittest.TestCase):
    def test_flatten(self):
        self.assertEqual(jotihunt_api.flatten([[1, 2, 3], [4, [5, 6]]]), [1, 2, 3, 4, 5, 6])

    def test_flatten_empty(self):
        self.assertEqual(jotihunt_api.flatten([]), [])

    def test_flatten_nonlist(self):
        self.assertEqual(jotihunt_api.flatten(3), [])


class StatusTest(unittest.TestCase):
    def test_getattr_a(self):
        status = jotihunt_api.Status()
        for name in jotihunt_api.Alpha:
            self.assertEqual(getattr(status, name), status['a'])

    def test_getattr_b(self):
        status = jotihunt_api.Status()
        for name in jotihunt_api.Bravo:
            self.assertEqual(getattr(status, name), status['b'])

    def test_getattr_c(self):
        status = jotihunt_api.Status()
        for name in jotihunt_api.Charlie:
            self.assertEqual(getattr(status, name), status['c'])

    def test_getattr_d(self):
        status = jotihunt_api.Status()
        for name in jotihunt_api.Delta:
            self.assertEqual(getattr(status, name), status['d'])

    def test_getattr_e(self):
        status = jotihunt_api.Status()
        for name in jotihunt_api.Echo:
            self.assertEqual(getattr(status, name), status['e'])

    def test_getattr_f(self):
        status = jotihunt_api.Status()
        for name in jotihunt_api.Foxtrot:
            self.assertEqual(getattr(status, name), status['f'])

    def test_update_and_get_updated(self):
        status = jotihunt_api.Status()
        status.set_deelgebied('a', 'groen')
        self.assertEqual(status.get_updated(), ['a'])

    def test_get_updated_is_same(self):
        status = jotihunt_api.Status()
        status.get_updated()
        for k, v in status._last_update.items():
            self.assertEqual(status[k], v)


class JotihuntBotTest(unittest.TestCase):
    def test_add_update(self):
        chat_id = 9
        new_updatelist =[(chat_id,telegramhandler.get_deelgebied(d)) for d in ['A','B','C','D','E','F','HB']]
        b = telegramhandler.JotihuntBot()
        b.add_update(['/update', 'aan', 'Alpha'],chat_id)
        b.add_update(['/update', 'aan', 'All'],chat_id)
        self.assertEqual(sorted([(u.chat_id, u.deelgebied) for u in telegramhandler.update_list]), sorted(new_updatelist))

if __name__ == '__main__':
    import sys
    unittest.main(sys.argv)
