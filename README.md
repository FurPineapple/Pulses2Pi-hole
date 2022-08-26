# Pulses to Pi-hole

Automate your Pi-Hole DNS sinkhole and restrict access to unreliable – potentially malicious domains without manual monitoring and every day participation. Automated collection of unreliable domain information from OTX AlienVault pulses using PythonSDK. Lists of domains are automatically collected, pushed to your GitHub repository and mapped to the Gravity database.

* Dependencies:

  * Running Pi-Hole
  
  * OTX Alienvault Active Account
  
    * Login to your account and navigate to https://otx.alienvault.com/api , where you will be able to generate the API key.
  
  * GitHub Active Account
  
    * Login to your account and navigate to https://github.com/settings/tokens , where you will be able to generate the API key.
    
  * Non-standard Python3 modules are required:

    * PyGithub module
      ```
      pip3 install PyGithub
      ```
    * OTXv2 module
      ```
      pip3 install OTXv2
      ```
    * NumPy module
      ```
      pip3 install NumPy
      ```
      
# Integration:

## 0. Once all dependencies match the required

* Select the directory to store the code:

  * For example using: `/usr/local/usr-pihole-scripts/`

  * Where the code is going to be stored: `/usr/local/usr-pihole-scripts/pulse-to-gravity.py`

**_You need to be root, or have evaluated permissions to make chenges in `/usr/local/*`_**

## 1. Once script is placed

* Change the `# Service Parameters` part of the code.

Navigate to: 
```
# Service Parameters

otx_key = ('YOUR_OTX_KEY') #-------------------------------> Get API Key from OTX AvienVault;

timestamp_file = ('/FULL-PATH/TO/STORED/TIMESTAMP') #------> Select path to store last pulse pull attempt timestamp;

file2push = ('FULL-PATH/TO/STORING/RESULT-LIST') #---------> Select path to store list of domains into the file;

github_key = ('YOUR_GITHUB_KEY') #-------------------------> Get API Key from GitHub / You will also need to set
                                 #                           up the scopes or permissions, further info right 
                                 #                           after this block;
                                 
github_repo = 'REPOSITORY' #-------------------------------> Select your GitHub repository in which You would like
                           #                                 to store lists;
                           
github_filename = 'FULL-PATH/FILENAME' #-------------------> Select full path to place you want to store lists 
                                       #                     including filename pattern. If you do not want to
                                       #                     create any new folder leave filename pattern only
                                       #                     => the lists will be stored right into the selected
                                       #                     branch (by default - main) not into separated folders;
                                       
raw_url = 'https://raw.githubusercontent.com/{0}/{1}/main/{2}' #--> Hard-coded raw file URL. In case branch has been
                                                               #    changed, change `main` branch to one You use;
                                                               
gravity_database_path = 'FULL-PATH/TO/GRAVITY.DB'              #--> Path to your local Pi-Hole Gravity database.
                                                               #    By default path == '/etc/pihole/gravity.db'.
                                                               
```
Get more info on GitHub App permissions:

```
https://docs.github.com/en/rest/overview/permissions-required-for-github-apps
```

**The parameters are hard-coded, in case you change GitHub API key, new key must be stored, for the code to connect successfully to GitHub, same applies for OTX API key.**

# 2. Once `service parameters` in the code are changed

Create `systemd` service and timers to automatically run the script:

As root perform following:
```
nano /etc/systemd/system/pulse-update.service
```

---------------------

Create `.service` dependant on timer:

```
[Unit]
Description=Stores pulse to Gravity.db
Wants=pulse-update.timer

[Service]
Type=simple
ExecStart=/usr/bin/python3.9 /usr/local/usr-pihole-scripts/pulse-to-gravity.py

[Install]
WantedBy=multi-user.target
```

---------------------

Then create `.timer` to execute the `.service`. 
* The `OnCalendar` field will match time You want `.service` to run. For more info can visit for example:

```
https://silentlad.com/systemd-timers-oncalendar-(cron)-format-explained
```

Example below:

```
nano /etc/systemd/system/pulse-update.timer
```

Example of content:

```
[Unit]
Description=Stores pulse to Gravity.db
Requires=pulse-update.service

[Timer]
Unit=pulse-update.service
OnCalendar=*-*-* 04:00:00

[Install]
WantedBy=timers.target
```
**_Please carefully check whether original pi-hole `cronjob` is not running same time `systemd` timers are set! To check use: `cat /etc/cron.d/pihole` and extract time fields of the cronjob containing `pihole updateGravity` command. Check your set time is not interfering._**

Installing Pi-Hole crontab job is set randomly between 3 and 5 am every Sunday. You can check forum thread: 

```
https://discourse.pi-hole.net/t/change-gravity-update-frequency-from-gui/23598
```

---------------------

To update Gravity independently after `pulse-update.service` create other systemd `.service`:

```
nano /etc/systemd/system/db-update.service
```

Example of content:

```
[Unit]
Description=Update Gravity
After=pulse-update.service
Wants=db-update.timer

[Service]
Type=simple
ExecStart=/usr/local/bin/pihole updateGravity

[Install]
WantedBy=multi-user.target
```

---------------------

Then add timer to invoke Gravity update:

```
nano /etc/systemd/system/db-update.timer
```

Example:

```
[Unit]
Description=Update Gravity
Requires=db-update.service

[Timer]
Unit=db-update.service
OnCalendar=*-*-* 04:56:30

[Install]
WantedBy=timers.target
```

# 3. Reload `systemctl daemon` and enable `.timers`

* `systemctl daemon-reload`

* `systemctl enable pulse-update.timer`

* `systemctl enable db-update.timer`

Then you can check the state of .timers by using:

  `systemctl status YOUR-TIMER-NAME.timer`
  
To activate timers just use:

  `systemctl start YOUR-TIMER-NAME.timer`

Then the timer will trigger `.service` on the time selected in `.timer` unit.

That is pretty much it, now in your selected time the code will run, pull OTX pulses, filter duplicates and put list of domains to your GitHub, then Pi-Hole gravity database will get raw file's URL and next timer will update database.

# Important Info:

***Please note, in case `timestamp` file is empty, does not exist or the path is given incorrectly (only filename is issued) script will trigger `otx.getall()`. In that case script will pull all existing pulses for the selected OTX key. It may take decent amount of time.***

 * After `otx.getall()` successfully finishes all the data is stored in the local file system, be sure you gave the path to partition which has some free space. Every day generated lists consume less than 1MB storage, when the `.getall()` function is called it may take around 10MB, according to the count of pulses You have subscribed;
 
 * Locally stored `result-lists` are overwritten every time service awakes.
 
 * In case filename is given without path, whether it is `timestamp` or `result-list`, file will appear in current user's directory';
 
 * In case path to the `timestamp` or for the `result-list` is not given, programe will be interrupted.
  
***In order to prevent run of `.getall()` function, create timestamp file first, giving it's full path to `Service Parameters`***
