import io
import logging
import unittest
from collections import namedtuple
from unittest.mock import patch

from oktaawscli.okta_auth_config import OktaAuthConfig
from oktaawscli.aws_auth import AwsAuth


class OktaRoleTests(unittest.TestCase):

    @classmethod
    def setUp(cls) -> None:
        cls.logger = logging.getLogger('okta-awscli')
        cls.handle = io.StringIO()
        cls.okta_auth_config = OktaAuthConfig(cls.logger, cls.handle)
        cls.aws_auth = AwsAuth('profile', 'profile', True, cls.logger)
        option_tuple = namedtuple("OptionTuple", ["option_text", "alias_name", "role_name"])
        cls.options = []
        cls.options.append(option_tuple("Hi I'm text", "role-name", "role-name2"))
        cls.options.append(option_tuple("Hi I'm text2", "role-name2", "role-name3"))
        cls.options.append(option_tuple("Hi I'm text3", "role-name3", "role-name4"))

    def read_handle(self) -> str:
        self.handle.seek(0)
        return self.handle.read()

    def test_role_writes(self):
        profiles = ['arn:aws:iam::000000000000:role/sso/def/test', 'arn:aws:iam::000000000001:role/sso/def/test', 'arn:aws:iam::000000000002:role/sso/def/test']
        self.okta_auth_config.save_selected_roles('profile', profiles)
        back = self.okta_auth_config.selected_roles_for('profile')
        self.assertEqual(profiles, back)

    @patch('builtins.input', return_value="1,2,3")
    def test_input_multi(self, _):
        roles = self.aws_auth.choose_roles(self.options, "1,2,3", [1, 2, 3])
        self.assertEqual(roles, "1,2,3")

    @patch('builtins.input', return_value="")
    def test_input_default(self, _):
        roles = self.aws_auth.choose_roles(self.options, "1,2,3", [1, 2, 3])
        self.assertEqual(roles, "1,2,3")

    @patch('builtins.input', side_effect=["", "1,2,3"])
    def test_input_no_default(self, _):
        roles = self.aws_auth.choose_roles(self.options, "", [])
        self.assertEqual(roles, "1,2,3")


if __name__ == '__main__':
    unittest.main()
