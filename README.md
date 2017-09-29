# Gunbot config updater

This script loads a Gunbot configuration file from an URL and uses it to create a new configuration adding the specified API keys. Optionally it can also also generate Gunthy GUI configuration file and restart both Gunbot and Gunthy GUI so that they are in sync.

## What does it do?

The script does the following:

* It loads the Gunbot configuration file from the specified URL, default is Dante's configuration file on Pastebin
* It updates the API keys
* It generates the Gunthy GUI configuration file with trade pairs
* It restarts both Gunbot and Gunthy GUI so that they are in sync
* It optionally can create backups of the configuration files
* It can rollback to the previous version of the configuration files if somthing goes wrong
* It can monitor if the web page of the specified URL has been modified

## Configuration files

The following configuration files must be set:

* secrets.json: contains the API keys for the exchanges Gunbot is trading on
* gunbot_config_updater.json: contains the rest of the configuration required by the script

An example secrets.json file is included (secrets_examples.json). 

## Command line arguments

The following command line arguments are supported:

```
   usage: gunbot_config_updater.py [-h] [-r] [-c] [-t] [-v | -q] [--version]
                                   [url]<code>

  download a Gunbot configuration from the specified url
 
  positional arguments:
    url             url to retrieve Gunbot configuration from
 
  optional arguments:
    -h, --help       show this help message and exit
    -r, --rollback   rollback to the previous configuration
    -c, --changed    only update if web page changed
    -o, --onlycheck  only check if web page changed
    -t, --testmode   create test configuration files only
    -v, --verbose    increase output verbosity
    -q, --quiet      no output
    --version        show program's version number and exit
```

# Done

The has been implemented:

# To do

The following still needs to be implemted:

* Make the script self running so it can monitor for changes at set intervals
* Clean up response handling so that json objects can be deserialized to python objects and vice versa
* Handle Tradeview integration
* Add Telegram integration to inform when the config has been updated
* Log to file
* Clean up code to meet DRY principle
* Add display to consol instead off showing logfile
* Automatically install dependencies
* Add risk indicator to trade pairs and make configurable untill which risk level to include
