import unittest
from unittest.mock import patch
from nexus_notifications import read_notifications,manage_thread,rollback_subscription,AdapterError
class NotificationTests(unittest.TestCase):
    def test_live_read_contract(self):
        with patch('nexus_notifications.api',side_effect=[(200,{'login':'fixture'},''),(200,[{'id':'12','unread':True}],'')]):
            self.assertEqual(read_notifications('fixture')['unread_count'],1)
    def test_mark_read_and_duplicate(self):
        before={'id':'12','repository':{'full_name':'fixture/test'},'unread':True}
        after={**before,'unread':False}
        with patch('nexus_notifications.api',side_effect=[(200,{'login':'fixture'},''),(200,before,''),(205,None,''),(200,after,'')]):
            result=manage_thread('fixture','12','mark_read','fixture/test');self.assertTrue(result['verified']);self.assertFalse(result['rollback_supported'])
        with patch('nexus_notifications.api',side_effect=[(200,{'login':'fixture'},''),(200,after,'')]) as api:
            self.assertTrue(manage_thread('fixture','12','mark_read','fixture/test')['duplicate']);self.assertEqual(api.call_count,2)
    def test_subscription_write_and_restore(self):
        thread={'id':'12','repository':{'full_name':'fixture/test'}}
        prior={'subscribed':False,'ignored':False};target={'subscribed':True,'ignored':False}
        with patch('nexus_notifications.api',side_effect=[(200,{'login':'fixture'},''),(200,thread,''),(200,prior,''),(200,target,''),(200,target,'')]):
            receipt=manage_thread('fixture','12','subscribe','fixture/test')['rollback']
        with patch('nexus_notifications.api',side_effect=[(200,{'login':'fixture'},''),(200,thread,''),(200,prior,''),(200,prior,'')]):
            self.assertTrue(rollback_subscription('fixture',receipt)['restored'])
    def test_auth_permission_timeout_failure(self):
        for message in ('authentication_failed','permission_denied','remote_timeout_outcome_unknown'):
            with self.subTest(message=message),patch('nexus_notifications.api',side_effect=AdapterError(message)):
                with self.assertRaisesRegex(AdapterError,message): manage_thread('fixture','12','subscribe','fixture/test')
    def test_cross_repository_write_rejected(self):
        with patch('nexus_notifications.api',side_effect=[(200,{'login':'fixture'},''),(200,{'id':'12','repository':{'full_name':'other/repo'}},'')]) as api:
            with self.assertRaisesRegex(AdapterError,'thread_scope_mismatch'): manage_thread('fixture','12','mark_read','fixture/test')
            self.assertEqual(api.call_count,2)
    def test_false_readback_never_success(self):
        thread={'id':'12','repository':{'full_name':'fixture/test'},'unread':True}
        with patch('nexus_notifications.api',side_effect=[(200,{'login':'fixture'},''),(200,thread,''),(205,None,''),(200,thread,'')]):
            with self.assertRaisesRegex(AdapterError,'write_unconfirmed'): manage_thread('fixture','12','mark_read','fixture/test')
