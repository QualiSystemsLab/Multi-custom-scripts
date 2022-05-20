#!/bin/bash -xe
exec 5> /git/logs1.log
BASH_XTRACEFD="5"
echo_input=$1
Folder=$2
echo "$echo_input" >> /git/logs.log 2>&1
ls -la >> /git/logs.log 2>&1
pwd >> /git/logs.log 2>&1
source ${Folder}/second.sh
func1 "love" "horror" >> /git/logs.log 2>&1
func2 "ball" "mystery" >> /git/logs.log 2>&1
func3_echo "$echo_input" "$echo_input" >> /git/logs.log 2>&1
# sudo yum install -y git
# touch /git/htop.html
sudo yum install -y epel-release
sudo yum install -y aha
sudo yum install -y htop
# sudo yum install -y aha
# sudo yum install -y htop
touch /git/htop.html
echo q | htop | aha --black --line-fix > /git/htop.html