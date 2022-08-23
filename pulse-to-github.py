from github import Github
from OTXv2 import OTXv2
from datetime import datetime
from re import search, compile
from numpy import array,unique
from numpy import ndarray as nd

# Service Parameters

otx_key = ('YOUR_OTX_KEY')
timestamp_file = r'TIMESTAMP'
file2push = r'RESULT-FILE'
github_key = ('YOUR_GIT_KEY')
github_repo = 'YOUR-REPO'
github_path = 'FOLDER1/'
github_filename = 'FILE'


# Regexp hostname to domain

web_rexp = compile('^w{3}\.(?P<domain>.+)')

# Commit timestamp of last pulse retrievement

def saveTimestamp(file_path):
    result_time = datetime.now().isoformat()
    with open(file_path, "w") as writer:
        writer.write(result_time)

# Read timestamp from previously generated file

def readTimestamp(file_path):
    with open(file_path, "r") as reader:
        start_time = reader.read()
    return start_time

# Retrieve Domains and Hostnames from pulses

def pulse2List(pulse,result_list):
    for ind in pulse['indicators']:
        ind_type = ind['type']
        ind_val = ind['indicator']
        if ind_type == 'domain':
            result_list.append(ind_val)
        # Hostnames may include WWW prefix, removing it using Regex
        elif ind_type == 'hostname':
            extract_domain_group = search(web_rexp,ind_val)
            if extract_domain_group:
                result_list.append(extract_domain_group.group('domain'))
            else:
                result_list.append(ind_val)
    return result_list

# Get unique values from list

def uniqList(list2check):
    list2array = array(list2check)
    uniq_array = unique(list2array)
    uniq_list = nd.tolist(uniq_array)
    with open(file2push,'w') as writer:
        for element in uniq_list:
            writer.write("0.0.0.0 {}\n".format(element))

# Push result file to GitHub

def push2GitHub(result_file):
    # Set Timeout to 350 in case of large commit file
    g = Github(github_key,timeout=350)
    repo = g.get_user().get_repo(github_repo)
    all_files = []
    contents = repo.get_contents("")
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            file = file_content
            all_files.append(
                    str(file).replace(
                    'ContentFile(path="', 
                    '').replace('")','')
                )

    with open(result_file, 'r') as reader:
        content = reader.read()

    # Upload to github

    git_file = (
        github_path + 
        github_filename + 
        datetime.now().strftime("%y%m%d%H%M")
            )
    if git_file in all_files:
        contents = repo.get_contents(git_file)
        repo.update_file(
            contents.path, 
            "committing files", 
            content, 
            contents.sha, 
            branch="main"
                )
    else:
        repo.create_file(git_file, "committing files", content, branch="main")

# Main

if __name__ == "__main__":
    # Load OTX key
    otx = OTXv2(otx_key)
    non_uniq_domain_list = list()

    try:
        time_last_run = readTimestamp(timestamp_file)
        pulses = otx.getsince(time_last_run)

        '''
        In case lack of timestamp_file all 
        the pulses for OTX key will be retrieved
        '''

    except FileNotFoundError as e:
        print(
            '<TimeStamp file not found. '
            'Retrieving all pulses for selected OTX key>'
            )
        pulses = otx.getall()
    
    # After retrieving pulses set timestamp

    saveTimestamp(timestamp_file)

    # Check if any pulses retrieved

    if pulses == []:
        print(
            '<No Pulse in given time range>'
            )
        exit()

    # Check each OTX pulse and append results to non_uniq_domain_list

    for otx_pulse in pulses:
        non_uniq_result = pulse2List(otx_pulse,non_uniq_domain_list)

    # Get unique list

    uniqList(non_uniq_result)

    # Push result file to GitHub

    push2GitHub(file2push)
