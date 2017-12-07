#!/bin/bash
ansible-playbook -vvvv -i ansible_deploy/inventory.yml ansible_deploy/deploy.yml --ask-sudo-pass