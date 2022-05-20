#!/usr/bin/env bash

set -e      # Stop Script on Error

# For Debugging (print env. variables into a file)
printenv > /var/log/colony-vars-"$(basename "$BASH_SOURCE" .sh)".txt
# sleep 5600