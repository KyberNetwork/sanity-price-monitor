# Deployment Instructions
Deployment script uses [Ansible](https://www.ansible.com/).

## Install
Replace SERVER_ADDRESS and USERNAME with actual values.

    $ ansible-playbook -i inventories/hosts.yml playbook.yml --extra-vars "server_host=SERVER_ADDRESS server_user=USERNAME"
    
## Install only sources (faster)
Replace SERVER_ADDRESS and USERNAME with actual values.

    $ ansible-playbook -i inventories/hosts.yml playbook.yml --tags sources --extra-vars "server_host=SERVER_ADDRESS server_user=USERNAME"
    
## Install only sources with some extras (time, verbose, notification)
Replace SERVER_ADDRESS and USERNAME with actual values.

    $ time ansible-playbook -i inventories/hosts.yml playbook.yml --tags sources --extra-vars "server_host=SERVER_ADDRESS server_user=USERNAME" -vvv ; terminal-notifier -message 'Command finished!' -sound 'default'

## Install Specific Branch
Add the optional extra var branch=BRANCH_NAME. Default is 'master'.

e.g.:

    $ time ansible-playbook -i inventories/hosts.yml playbook.yml --tags sources --extra-vars "branch=SPECIFIC_BRANCH server_host=SERVER_ADDRESS server_user=USERNAME" -vvv ; terminal-notifier -message 'Command finished!' -sound 'default'
