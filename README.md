# bugzilla_script

Script that:

- Pulls all cases of interest

- Pulls all Bugzillas associated with these cases

- Adds "Telco " to each Bugzilla's internal whiteboard

More info on offline_token: https://access.redhat.com/articles/3626371

More info on Bugzilla API key: https://bugzilla.redhat.com/userprefs.cgi?tab=apikey

### Usage:

  

1. `git clone https://github.com/adhil0/bugzilla_script.git`
2. `cd bugzilla_script`
3. Install dependencies (either of the following)
  * `dnf install python3-bugzilla python3-tqdm`   (available in EPEL 8)
  * `pip install -r requirements.txt`
4. To generate list of untagged Bugzillas: `python3 bz_script.py -o <OFFLINE_TOKEN> -b <BZ_API_KEY>`
5. To generate list of untagged Bugzillas and add "Telco " to their internal whiteboard: `python3 bz_script.py -o <OFFLINE_TOKEN> -b <BZ_API_KEY> -y`
