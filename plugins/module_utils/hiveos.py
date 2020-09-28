#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
module: hiveos_facts
version_added: "2.0"
author: ""
short_description: Collect facts from remote devices running Aerohive HiveOS
description:
  - Collects a base set of device facts from a remote device that
    is running HiveOS. This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
extends_documentation_fragment: HiveOS
notes:
  - Tested against HiveOS 15.6
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        all, hardware, config, and interfaces.  Can specify a list of
        values to include a larger subset.  Values can also be used
        with an initial C(M(!)) to specify that a specific subset should
        not be collected.
    required: false
    default: '!config'
"""

EXAMPLES = """
# Collect all facts from the device
- hiveos_facts:
    gather_subset: all

# Collect only the config and default facts
- hiveos_facts:
    gather_subset:
      - config

# Do not collect hardware facts
- hiveos_facts:
    gather_subset:
      - "!hardware"
"""

RETURN = """
ansible_net_gather_subset:
  description: The list of fact subsets collected from the device
  returned: always
  type: list

# default
ansible_net_model:
  description: The model name returned from the device
  returned: always
  type: string
ansible_net_serialnum:
  description: The serial number of the remote device
  returned: always
  type: string
ansible_net_version:
  description: The operating system version running on the remote device
  returned: always
  type: string
ansible_net_hostname:
  description: The configured hostname of the device
  returned: always
  type: string
ansible_net_image:
  description: The image file the device is running
  returned: always
  type: string

# hardware
ansible_net_filesystems:
  description: All file system names available on the device
  returned: when hardware is configured
  type: list
ansible_net_filesystems_info:
  description: A hash of all file systems containing info about each file system (e.g. free and total space)
  returned: when hardware is configured
  type: dict
ansible_net_memfree_mb:
  description: The available free memory on the remote device in Mb
  returned: when hardware is configured
  type: int
ansible_net_memtotal_mb:
  description: The total memory on the remote device in Mb
  returned: when hardware is configured
  type: int

# config
ansible_net_config:
  description: The current active config from the device
  returned: when config is configured
  type: string

# interfaces
ansible_net_all_ipv4_addresses:
  description: All IPv4 addresses configured on the device
  returned: when interfaces is configured
  type: list
ansible_net_all_ipv6_addresses:
  description: All IPv6 addresses configured on the device
  returned: when interfaces is configured
  type: list
ansible_net_interfaces:
  description: A hash of all interfaces running on the system
  returned: when interfaces is configured
  type: dict
ansible_net_neighbors:
  description: The list of LLDP neighbors from the remote device
  returned: when interfaces is configured
  type: dict
"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.hiveos.hiveos import run_commands
from ansible.module_utils.six import iteritems


class FactsBase(object):

    COMMANDS = frozenset()

    def __init__(self, module):
        self.module = module
        self.facts = {}
        self.responses = None

    def populate(self):
        self.responses = run_commands(self.module, commands=self.COMMANDS, check_rc=False)

    def run(self, cmd):
        return run_commands(self.module, commands=cmd, check_rc=False)


class Default(FactsBase):

    COMMANDS = [
        'show version',
        'show hw-info',
        'show run | include hostname'
    ]

    def populate(self):
        super(Default, self).populate()
        # output from the first list index show version
        data_0 = self.responses[0]
        # output from the second list index show hw-info
        data_1 = self.responses[1]
        # output from the third list index show run | include hostname
        data_2 = self.responses[2]

        if data_0:
            self.facts['version'] = self.parse_version(data_0)
            self.facts['model'] = self.parse_model(data_0)

        if data_1:
            self.facts['serialnum'] = self.parse_serialnum(data_1)

        if data_2:
            self.facts['hostname'] = self.parse_hostname(data_2)

    def parse_version(self, data):
        match = re.search(r'Version:\s+\w+\s(\S+)\s', data)
        if match:
            return match.group(1)

    def parse_model(self, data):
        match = re.search(r'Platform:\s*(\S+)', data)
        if match:
            return match.group(1)

    def parse_serialnum(self, data):
        match = re.search(r'Serial number:\s+(\w+)', data)
        if match:
            return match.group(1)

    def parse_hostname(self, data):
        match = re.search(r'^hostname\s+(\S+)$', data)
        if match:
            return match.group(1)


class Hardware(FactsBase):

    COMMANDS = [
        'show system disk-info',
        'show cpu',
        'show memory',
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.facts['filesystems'] = self.parse_filesystems(data)

        data = self.responses[1]
        if data:
            self.facts['processor_total'] = re.search(r'^CPU total \w+:\s+(\S+)', data).group(1)
            self.facts['processor_user'] = re.search(r'CPU user \w+:\s+(\S+)', data).group(1)
            self.facts['processor_sys'] = re.search(r'CPU system \w+:\s+(\S+)', data).group(1)

        data = self.responses[2]
        if data:
            self.facts['memtotal_kb'] = re.search(r'Total Memory: \s+(\d+)', data).groups(1)
            self.facts['memfree_kb'] = re.search(r'Free Memory: \s+(\d+)', data).groups(1)
            self.facts['memused_kb'] = re.search(r'Used Memory: \s+(\d+)', data).groups(1)

    def parse_filesystems(self, data):
        return re.findall(r'^/dev|tmpfs', data, re.M)


class Config(FactsBase):

    COMMANDS = ['show config running']

    def populate(self):
        super(Config, self).populate()
        data = self.responses[0]
        if data:
            self.facts['config'] = data


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    config=Config,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())

global warnings
warnings = []


def main():
    """main entry point for module execution
    """
    argument_spec = {
        'gather_subset': {'default': ['!config'], 'type': 'list'},
    }

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    gather_subset = module.params['gather_subset']

    runable_subsets = set()
    exclude_subsets = set()

    for subset in gather_subset:
        if subset == 'all':
            runable_subsets.update(VALID_SUBSETS)
            continue

        if subset.startswith('!'):
            subset = subset[1:]
            if subset == 'all':
                exclude_subsets.update(VALID_SUBSETS)
                continue
            exclude = True
        else:
            exclude = False

        if subset not in VALID_SUBSETS:
            module.fail_json(msg='Bad subset')

        if exclude:
            exclude_subsets.add(subset)
        else:
            runable_subsets.add(subset)

    if not runable_subsets:
        runable_subsets.update(VALID_SUBSETS)

    runable_subsets.difference_update(exclude_subsets)
    runable_subsets.add('default')

    facts = {}
    facts['gather_subset'] = list(runable_subsets)

    instances = []
    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module))

    for inst in instances:
        inst.populate()
        facts.update(inst.facts)

    ansible_facts = {}
    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
