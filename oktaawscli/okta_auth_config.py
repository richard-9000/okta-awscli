""" Config helper """

import os

from configparser import RawConfigParser, ConfigParser
from getpass import getpass

try:
    input = raw_input
except NameError:
    pass


class OktaAuthConfig:
    """ Config helper class """

    def __init__(self, logger, file_handle=None):
        self.logger = logger
        self.file_handle = file_handle
        self.password = None
        if file_handle is not None:
            self._value = RawConfigParser()
            self._value.read_file(self.file_handle)
        else:
            self.config_path = os.path.join(os.path.expanduser('~'), '.okta-aws')
            if os.path.exists(self.config_path) and os.path.getsize(self.config_path) > 0:
                self._value = RawConfigParser()
                self._value.read(self.config_path)
            else:
                print("Config path: {} does not exist".format(self.config_path))
                new_cfg = ConfigParser()
                base_url = input("What is your organization's login url? ")

                new_cfg["default"] = {'base-url': base_url}
                with open(self.config_path, 'w') as cp:
                    new_cfg.write(cp)
                self._value = new_cfg

    def base_url_for(self, okta_profile):
        """ Gets base URL from config """
        if self._value.has_option(okta_profile, 'base-url'):
            base_url = self._value.get(okta_profile, 'base-url')
            self.logger.info("Authenticating to: %s" % base_url)
        else:
            base_url = self._value.get('default', 'base-url')
            self.logger.info(
                "Using base-url from default profile %s" % base_url
            )
        return base_url

    def app_link_for(self, okta_profile):
        """ Gets app_link from config """
        app_link = None
        if self._value.has_option(okta_profile, 'app-link'):
            app_link = self._value.get(okta_profile, 'app-link')
        elif self._value.has_option('default', 'app-link'):
            app_link = self._value.get('default', 'app-link')
        self.logger.info("App Link set as: %s" % app_link)
        return app_link

    def username_for(self, okta_profile):
        """ Gets username from config """
        if self._value.has_option(okta_profile, 'username'):
            username = self._value.get(okta_profile, 'username')
            self.logger.info("Authenticating as: %s" % username)
        else:
            username = input('Enter username: ')
        return username

    def password_for(self, okta_profile):
        """ Gets password from config """
        if self.password is not None:
            return self.password
        if self._value.has_option(okta_profile, 'password'):
            self.password = self._value.get(okta_profile, 'password')
        else:
            self.password = getpass('Enter password: ')
        return self.password

    def factor_for(self, okta_profile):
        """ Gets factor from config """
        if self._value.has_option(okta_profile, 'factor'):
            factor = self._value.get(okta_profile, 'factor')
            self.logger.debug("Setting MFA factor to %s" % factor)
            return factor
        return None

    def duration_for(self, okta_profile):
        """ Gets requested duration from config, ignore it on failure """
        if self._value.has_option(okta_profile, 'duration'):
            duration = self._value.get(okta_profile, 'duration')
            self.logger.debug("Requesting a duration of %s seconds" % duration)
            try:
                return int(duration)
            except ValueError as _:
                self.logger.warn("Duration could not be converted to a number, ignoring.")
        return None

    def save_chosen_role_for_profile(self, okta_profile, role_arn):
        """ Gets role from config """
        if not self._value.has_section(okta_profile):
            self._value.add_section(okta_profile)

        base_url = self.base_url_for(okta_profile)
        self._value.set(okta_profile, 'base-url', base_url)
        self._value.set(okta_profile, 'role', role_arn)

        with open(self.config_path, 'w+') as configfile:
            self._value.write(configfile)

    def save_chosen_app_link_for_profile(self, okta_profile, app_link):
        """ Gets role from config """
        if not self._value.has_section(okta_profile):
            self._value.add_section(okta_profile)

        base_url = self.base_url_for(okta_profile)
        self._value.set(okta_profile, 'base-url', base_url)
        self._value.set(okta_profile, 'app-link', app_link)

        with open(self.config_path, 'w+') as configfile:
            self._value.write(configfile)

    def save_selected_roles(self, okta_profile, profiles):
        if not self._value.has_section(okta_profile):
            self._value.add_section(okta_profile)
        self._value.set(okta_profile, 'selected-roles', ','.join(profiles))

        if self.file_handle is not None:
            self._value.write(self.file_handle)
        else:
            with open(self.config_path, 'w+') as cfg:
                self._value.write(cfg)

    def selected_roles_for(self, okta_profile):
        if self._value.has_option(okta_profile, 'selected-roles'):
            return self._value.get(okta_profile, 'selected-roles').split(',')
        if self._value.has_option('default', 'selected-roles'):
            return self._value.get('default', 'selected-roles').split(',')
        return []
