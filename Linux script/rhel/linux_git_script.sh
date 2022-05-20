#!/bin/bash -x

###################################
# Env vars
####################################
repo_url=$GitHubURL
git_token=$GitToken
main_file=$MainFileName
git_branch=$GitBranch
# git_branch="master"
########################################
# Create out_location for git download
########################################
out_location=${out_out_location:="/QualiMainRepo"}
if [ -d "$out_out_location" ]; then
  rm -rf $out_out_location
fi
mkdir -p $out_location
mkdir -p /git
touch /git/logs.log
exec 5> /git/logs.log
BASH_XTRACEFD="5"

######################
# Download tarball
######################
# test public repo without token
# test sudo
(curl -L -k -u token:${git_token} "${repo_url}/tarball/${git_branch}" | tar -xz -C $out_location \
&& echo "Succsesfully download the Main repo from ${repo_url} to $out_location") \
|| (echo "Error downloading or extarcting Main repo." && exit 1)
chmod -R a+rwx $out_location

####################################
# Configure path for script startup
####################################
if [[ $main_file =~ "\.sh" ]]; then
  main_file="${main_file}.sh"
fi

####################################
# Test if full file path exists
####################################
file=$(find . -name "$main_file")
touch /git/file.log
echo $file >> /git/file.log 2>&1
echo $file
prefix="https://github.com/"
Check_path=${GitHubURL#"$prefix"}
Check_path=$(echo $Check_path | awk -F '/' '{print $1""}')
main_executer_path=$(find $out_location -mindepth 1 -maxdepth 1 -type d -name "$Check_path*")

##########################
# Check if folder exists
############################
cd "${main_executer_path}" || (echo "Cannot open Main repo." && exit 1)

###############################
# Test if full file path exists
###############################
# Linux_git_script/start.sh
if [ ! -f "$main_file" ]; then
  echo "File not found!" && main_file=$(find -name "$main_file" | awk "NR==1 {print; exit}")
#   Folder_files="$(dirname "${main_file}")"
# else
#   Folder_files=$(echo $main_file | awk -F '/' '{print $1""}')
fi

touch /git/test123.log
test=$(find ./ -name "start.sh" | awk "NR==1 {print; exit}")
echo "test $test" >> /git/test123.log
Folder_files="$(dirname "${main_file}")"
# Folder_files=$(echo $main_file | awk -F '/' '{print $1""}')
echo "Folder_files $Folder_files" >> /git/test123.log
${main_file} "${echo_input}" "${main_executer_path}/${Folder_files}" 

# Folder=/QualiMainRepo/oleksandr-r-q-ps_scr-f2e1dd4e68e87dd621ff429bf9e960a3e428e051/.