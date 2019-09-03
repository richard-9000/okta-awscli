""" AWS authentication """
# pylint: disable=C0325
import os
import base64
import xml.etree.ElementTree as ET
from collections import namedtuple
from configparser import RawConfigParser
import boto3
from botocore.exceptions import ClientError
import re
import requests

class AwsAuth():
    """ Methods to support AWS authentication using STS """

    def __init__(self, profile, okta_profile, verbose, logger):
        home_dir = os.path.expanduser('~')
        self.creds_dir = home_dir + "/.aws"
        self.creds_file = self.creds_dir + "/credentials"
        self.profile = profile
        self.verbose = verbose
        self.logger = logger
        self.role = ""

        okta_config = home_dir + '/.okta-aws'
        parser = RawConfigParser()
        parser.read(okta_config)

        if parser.has_option(okta_profile, 'role'):
            self.role = parser.get(okta_profile, 'role')
            self.logger.debug("Setting AWS role to %s" % self.role)


    def choose_aws_role(self, assertion):
        """ Choose AWS role from SAML assertion """

        roles = self.__extract_available_roles_from(assertion)
        if self.role:
            predefined_role = self.__find_predefiend_role_from(roles)
            if predefined_role:
                self.logger.info("Using predefined role: %s" % self.role)
                return predefined_role
            else:
                self.logger.info("""Predefined role, %s, not found in the list
of roles assigned to you.""" % self.role)
                self.logger.info("Please choose a role.")

        alias_map = self.__get_account_alias(assertion)
        role_options = self.__create_options_from(roles, alias_map)
        for option in role_options:
            print(option.option_text)

        role_choice = int(input('Please select the AWS role: ')) - 1
        return roles[role_choice], role_options[role_choice]

    @staticmethod
    def __get_account_alias(assertion):
        """ Find the alias for accounts """
        response = requests.post('https://signin.aws.amazon.com/saml', data={'SAMLResponse': assertion})
        accounts = re.findall(r'Account: ([^\s]+) \((\d{12})\)', response.text)
        return { tup[1] : tup[0] for tup in accounts }

    @staticmethod
    def get_sts_token(role_arn, principal_arn, assertion, duration=None, logger=None):
        """ Gets a token from AWS STS """

        # Connect to the GovCloud STS endpoint if a GovCloud ARN is found.
        arn_region = principal_arn.split(':')[1]
        if arn_region == 'aws-us-gov':
            sts = boto3.client('sts', region_name='us-gov-west-1')
        else:
            sts = boto3.client('sts')

        try:
            response = sts.assume_role_with_saml(RoleArn=role_arn,
                                                 PrincipalArn=principal_arn,
                                                 SAMLAssertion=assertion,
                                                 DurationSeconds=duration or 3600)
        except ClientError as ex:
            if logger:
                logger.error(
                    "Could not retrieve credentials: %s" % 
                    ex.response['Error']['Message']
                )
                exit(-1)
            else:
                raise

        credentials = response['Credentials']
        return credentials

    def check_sts_token(self, profile):
        """ Verifies that STS credentials are valid """
        # Don't check for creds if profile is blank
        if not profile:
            return False

        parser = RawConfigParser()
        parser.read(self.creds_file)

        if not os.path.exists(self.creds_dir):
            self.logger.info("AWS credentials path does not exist. Not checking.")
            return False

        elif not os.path.isfile(self.creds_file):
            self.logger.info("AWS credentials file does not exist. Not checking.")
            return False

        elif not parser.has_section(profile):
            self.logger.info("No existing credentials found. Requesting new credentials.")
            return False

        session = boto3.Session(profile_name=profile)
        sts = session.client('sts')
        try:
            sts.get_caller_identity()

        except ClientError as ex:
            if ex.response['Error']['Code'] == 'ExpiredToken':
                self.logger.info("Temporary credentials have expired. Requesting new credentials.")
                return False

        self.logger.info("STS credentials are valid. Nothing to do.")
        return True

    def write_sts_token(self, profile, access_key_id, secret_access_key, session_token):
        """ Writes STS auth information to credentials file """
        if not os.path.exists(self.creds_dir):
            os.makedirs(self.creds_dir)
        config = RawConfigParser()

        if os.path.isfile(self.creds_file):
            config.read(self.creds_file)

        if not config.has_section(profile):
            config.add_section(profile)

        config.set(profile, 'aws_access_key_id', access_key_id)
        config.set(profile, 'aws_secret_access_key', secret_access_key)
        config.set(profile, 'aws_session_token', session_token)

        with open(self.creds_file, 'w+') as configfile:
            config.write(configfile)
        self.logger.info("Temporary credentials written to profile: %s" % profile)
        self.logger.info("Invoke using: aws --profile %s <service> <command>" % profile)

    @staticmethod
    def __extract_available_roles_from(assertion):
        aws_attribute_role = 'https://aws.amazon.com/SAML/Attributes/Role'
        attribute_value_urn = '{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'
        roles = []
        root = ET.fromstring(base64.b64decode(assertion))
        role_tuple = namedtuple("RoleTuple", ["principal_arn", "role_arn"])
        for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
            if saml2attribute.get('Name') == aws_attribute_role:
                for attrvalue in saml2attribute.iter(attribute_value_urn):
                    # Role and Principal arns can be in any order and/or from separate accounts.
                    role_arn = re.findall(r'arn:aws:iam::\d{12}:role/[^,]*', attrvalue.text)[0]
                    principal_arn = re.findall(r'arn:aws:iam::\d{12}:saml-provider/[^,]*', attrvalue.text)[0]
                    roles.append(role_tuple(principal_arn, role_arn))
        return roles

    @staticmethod
    def __create_options_from(roles, alias_map):
        options = []
        option_tuple = namedtuple("OptionTuple", ["option_text", "alias_name", "role_name"])
        for index, role in enumerate(roles):
            (account_number, role_name) = re.findall(r'arn:aws:iam::(\d{12}):role.*/([^/]+)$', role.role_arn)[0]
            if account_number in alias_map:
                role_text = "%d: %s (%s)" % (index + 1, role.role_arn, alias_map[account_number])
                alias_name = alias_map[account_number]
            else: 
                role_text = "%d: %s" % (index + 1, role.role_arn)
                alias_name = account_number

            options.append(option_tuple(role_text, alias_name, role_name))
        return options

    def __find_predefiend_role_from(self, roles):
        found_roles = filter(lambda role_tuple: role_tuple.role_arn == self.role, roles)
        return next(iter(found_roles), None)
