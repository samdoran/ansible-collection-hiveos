#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import json

from itertools import chain
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list
from ansible.module_utils._text import to_text
from ansible.plugins.cliconf import CliconfBase


class Cliconf(CliconfBase):

    def get_config(self, source='running', flags=None, format=None):
        if source not in ('running', 'backup', 'bootstrap', 'current', 'default', 'failed', 'version',):
            raise ValueError("fetching configuration from %s is not supported" % source)

        if format:
            raise ValueError("'format' value %s is not supported for get_config" % format)

        cmd = 'show config %s' % source
        return self.send_command(cmd)

    def get(self, command, prompt=None, answer=None, sendonly=False, newline=True, check_all=False):
        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, newline=newline, check_all=check_all)

    def get_device_info(self):
        device_info = {}

        device_info['network_os'] = 'hiveos'

        reply = self.get('show version')
        data = to_text(reply, errors='surrogate_or_strict').strip()

        match = re.search(r'Version:\s+\w+\s(\S+)\s', data)
        if match:
            device_info['network_os_version'] = match.group(1)

        match = re.search(r'Platform:\s*(\S+)', data)
        if match:
            device_info['network_os_model'] = match.group(1)

        reply = self.get('show config running | include hostname')
        reply = to_text(reply, errors='surrogate_or_strict').strip()
        device_info['network_os_hostname'] = reply.split(' ')[-1]

        return device_info

    def get_capabilities(self):
        result = super(Cliconf, self).get_capabilities()
        # result['device_info'] = self.get_device_info()
        return json.dumps(result)

    def edit_config(self, candidate=None, commit=True, replace=False, comment=None):
        for cmd in chain(['configure'], to_list(candidate)):
            self.send_command(cmd)
