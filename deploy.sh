#!/bin/bash
export ANSIBLE_HOST_KEY_CHECKING=False
ansible-playbook -vvvv -i ansible_deploy/inventory.yml ansible_deploy/deploy.yml --ask-sudo-pass
unset ANSIBLE_HOST_KEY_CHECKING