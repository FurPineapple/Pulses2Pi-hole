# Pulses to Pi-hole
Small project to retrieve OTX Alienvault pulses to Pi-hole database

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
      
## Integration:

# 0. Once all dependencies match the required, select the directory to store the code.

> For example using: `/usr/local/usr-pihole-scripts/`

> Where the code is going to be stored: `/usr/local/usr-pihole-scripts/pulse-to-gravity.py`

**_You need to be root, or have evaluated permissions to make chenges in `/usr/local/*`_**

**You may want to change the `# Service Parameters` part of the code.**

>Navigate to: 
```
# Service Parameters

otx_key = ('YOUR_OTX_KEY')
timestamp_file = ('/FULL-PATH/TO/STORED/TIMESTAMP')
file2push = ('FULL-PATH/TO/STORING/RESULT-LIST')
github_key = ('YOUR_GITHUB_KEY')
github_repo = 'REPOSITORY'
github_filename = 'FULL-PATH/FILENAME'
raw_url = 'https://raw.githubusercontent.com/{0}/{1}/main/{2}'
gravity_database_path = 'FULL-PATH/TO/GRAVITY.DB'
```

**The parameters are hard-coded, in case you change GitHub API key, new key must be stored, for the code to connect successfully to GitHub, same applies for OTX API key.**

# 1. As long as previous step is done, let's create `systemd` services to automatically run the script:

> As root perform following:
```
nano /etc/systemd/system/pulse-update.service
```

---------------------

> Create `.service` dependant on timer:

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

> Then create `.timer` to execute the `.service`

```
nano /etc/systemd/system/pulse-update.timer
```
> Example below:

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

> Installing Pi-Hole crontab job is set randomly between 3 and 5 am every Sunday. You can check forum thread: https://discourse.pi-hole.net/t/change-gravity-update-frequency-from-gui/23598

---------------------

> To update Gravity independently after `pulse-update.service` create other systemd `.service`:

```
nano /etc/systemd/system/db-update.service
```

> Example of content:

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

> Then add timer to invoke Gravity update:

```
nano /etc/systemd/system/db-update.timer
```

> Example:

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

# 2. Reload `systemctl daemon` and enable `.timers`

* `systemctl daemon-reload`

* `systemctl enable pulse-update.timer`

* `systemctl enable db-update.timer`

> Then you can check the state of .timers by using:

  `systemctl status YOUR-TIMER-NAME.timer`
  
> To activate timers just use:

  `systemctl start YOUR-TIMER-NAME.timer`

> Then the timer will trigger `.service` on the time selected in `.timer` unit.

*That is pretty much it, now in your selected time the code will run, pull OTX pulses, filter dublicates and put list of domains to your GitHub, then Pi-Hole gravity database will get raw file's url and next timer will update database.*

***Please note that running first time may trigger `otx.getall()` which will pull all existing pulses for selected OTX key, in order to prevent this, create timestamp file first, giving it's full path to `Service Parameters`. Othervice file will be created in given path and used as timestamp for retrieved pulses. `otx.getall()` may take decent amount of time.***
