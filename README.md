[![Galaxy](https://img.shields.io/badge/galaxy-samdoran.hiveos-blue)](https://galaxy.ansible.com/samdoran/hiveos)

# Aerohive HiveOS Collection #

**STILL VERY MUCH A WORK IN PROGRESS**

This Ansible collection contains modules and plugins for managing Aerohive HiveOS devices with Ansible.

This collection was tested against HiveOS 10.0r7a.

### cliconf plugins ###

| Name              | Description          |
|-------------------|----------------------|
| `samdoran.hiveos.hiveos` | Use HiveOS cliconf to run commands on HiveOS |


### Modules ###

| Name              | Default Value       | Description          |
|-------------------|---------------------|----------------------|
| `samdoran.hiveos.hiveos_facts` | Gather facts about a HiveOS device. |

## Installing this collection ##

    ansible-galaxy collection install samdoran.hiveos
