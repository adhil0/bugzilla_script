import bugzilla
import time
import requests
import logging
import argparse
from tqdm import tqdm

def get_token(offline_token):

    # https://access.redhat.com/articles/3626371
    data = { 'grant_type' : 'refresh_token', 'client_id' : 'rhsm-api', 'refresh_token': offline_token }
    url = 'https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token'
    r = requests.post(url, data=data)
    # It returns 'application/x-www-form-urlencoded'
    token = r.json()['access_token']
    return(token)

def get_cases(offline_token):
    """Get relevant cases from Red Hat Portal
    Arguments:
        offline_token: token for Red Hat Portal API (https://access.redhat.com/articles/3626371)
    Returns:
        Dictionary of Relevant Cases
    """
    token = get_token(offline_token)
    query = "case_summary:*webscale* OR case_tags:*shift_telco5g* OR case_tags:*cnv*case"
    fields = ",".join(["case_number","case_status","case_bugzillaNumber"])
    query = "({})".format(query)
    num_cases = 5000
    payload = {"q": query, "partnerSearch": "false", "rows": num_cases, "fl": fields}
    headers = {"Accept": "application/json", "Authorization": "Bearer " + token}
    url = "https://access.redhat.com/hydra/rest/search/cases"

    logging.warning("searching the portal for cases")
    start = time.time()
    r = requests.get(url, headers=headers, params=payload)
    cases_json = r.json()['response']['docs']
    end = time.time()
    logging.warning("found {} cases in {} seconds".format(len(cases_json), (end-start)))
    cases = {}
    for case in cases_json:
        cases[case["case_number"]] = {
            "status": case["case_status"]
        }
        # Sometimes there is no BZ attached to the case
        if "case_bugzillaNumber" in case:
            cases[case["case_number"]]["bug"] = case["case_bugzillaNumber"]
    return cases

def get_bugzillas(cases, bz_api, offline_token):
    """Get Bugzillas that haven't been tagged w/ "Telco"
    Arguments:
        cases: dictionary of relevant cases
        bz_api: bugzilla connection object
        offline_token: token for Red Hat Portal API (https://access.redhat.com/articles/3626371)
    Returns:
        list of Bugzilla #'s that don't have "Telco" in their internal_whiteboard
    """

    bz_dict = {}

    # Get new token to avoid time out error
    token = get_token(offline_token)
    headers = {"Accept": "application/json", "Authorization": "Bearer " + token}

    logging.warning("getting all bugzillas")
    for case in tqdm(cases):
        if "bug" in cases[case] and cases[case]['status'] != "Closed":
            bz_endpoint = "https://access.redhat.com/hydra/rest/v1/cases/" + case
            r_bz = requests.get(bz_endpoint, headers=headers)
            bz_dict[case] = r_bz.json()['bugzillas']

    # See if Bugzilla tagged with Telco
    logging.warning("getting untagged bugs via bugzilla API")
    untagged_bugs = []
    for case in tqdm(bz_dict):
        for bug in bz_dict[case]:
                bugs = bz_api.getbug(bug['bugzillaNumber'])
                if "Telco " not in bugs.internal_whiteboard and "Telco" != bugs.internal_whiteboard[-5:] and "Telco, " not in bugs.internal_whiteboard:
                    untagged_bugs.append(bugs.id)
    return untagged_bugs

def tag_bugzillas(bz_api, untagged_bugs):
    """ Add Telco to bug's internal_whiteboard
    Arguments:
        bz_api: bugzilla connection object
        untagged_bugs: list of Bugzilla #'s that don't have "Telco" in their internal_whiteboard
    Returns:
        Nothing
    """
    logging.warning("adding 'Telco ' to internal whiteboard of untagged bugs")
    for bug in tqdm(untagged_bugs):
        bugs = bz_api.getbug(bug)
        update = bz_api.build_update(internal_whiteboard="Telco " + bugs.internal_whiteboard)
        bz_api.update_bugs([bugs.id], update)

def main():
    parser = argparse.ArgumentParser(description="Get untagged Bugzillas")
    parser.add_argument('-o', '--offline_token', type=str, required=True, help='API token for case portal: https://access.redhat.com/articles/3626371')
    parser.add_argument('-b', '--bz_key', type=str, required=True, help='API key for bugzilla.redhat.com: https://bugzilla.redhat.com/userprefs.cgi?tab=apikey')
    parser.add_argument('-y', '--modify', action='store_true', help = "Include if you want to add 'Telco ' to untagged BZ's")
    args=parser.parse_args()
    
    offline_token = args.offline_token
    bz_key = args.bz_key
    if args.modify:
        modify = True
    else:
        modify = False

    cases = get_cases(offline_token)
    bz_url = "bugzilla.redhat.com"
    bz_api = bugzilla.Bugzilla(bz_url, api_key=bz_key)
    untagged_bugs = get_bugzillas(cases, bz_api, offline_token)

    print("Untagged Bugzillas:", untagged_bugs)

    if modify:
        tag_bugzillas(bz_api, untagged_bugs)



if __name__ == "__main__":
    main()