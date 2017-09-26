#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script takes a Gunbot configuration file from the specified URL, updates the keys, creates a Gunthy GUI config
file and then stops and starts Gunthy GUI.

@author Stephen Oostenbrink (nidkil) <stephen at oostenbrink dot com>
"""

import os
import json
import requests
import logging
import subprocess
import shutil
import argparse

from check_webpage_updated import WebPageMonitor


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

DEFAULT_URL = 'https://pastebin.com/raw/SYTkqVDQ'


class GunbotConfigHandler(object):

    __TEST_MODE = 'test-'

    def __init__(self, config_dir=None, test_mode=None):
        self.test_mode_overrule = test_mode
        if config_dir is None:
            self.config_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.config_dir = config_dir
        self.config_path = os.path.join(self.config_dir, 'gunbot_config_updater.json')
        if not os.path.isfile(self.config_path):
            logging.error("Configuration file missing {}".format(self.config_path))
            exit(-3)
        logging.info("Loading config file from {}".format(self.config_path))
        with open(self.config_path) as config_file:
            self.configuration = json.load(config_file)
            config_file.close()
        logging.debug(self)

    @property
    def test_mode(self):
        if self.test_mode_overrule is None:
            return self.configuration['testMode']
        else:
            return self.test_mode_overrule

    @property
    def gunbot_location(self):
        if len(self.configuration['gunbot']['location']) == 0:
            return self.config_dir
        else:
            return self.configuration['gunbot']['location']

    @property
    def gunbot_config(self):
        if self.test_mode:
            return self.__TEST_MODE + self.configuration['gunbot']['config']
        else:
            return self.configuration['gunbot']['config']

    @property
    def gunbot_start(self):
        return self.configuration['gunbot']['start']

    @property
    def gunbot_stop(self):
        return self.configuration['gunbot']['stop']

    @property
    def gunthy_gui_config(self):
        if self.test_mode:
            return self.__TEST_MODE + self.configuration['gui']['config']
        else:
            return self.configuration['gui']['config']

    @property
    def gunthy_gui_gunbot_enabled(self):
        return self.configuration['gui']['enabled']

    @property
    def gunthy_gui_gunbot_version(self):
        return self.configuration['gui']['gunbotVersion']

    @property
    def gunthy_gui_start(self):
        return self.configuration['gui']['start']

    @property
    def gunthy_gui_stop(self):
        return self.configuration['gui']['stop']

    @property
    def backup(self):
        return self.configuration['backup']

    def __repr__(self):
        return "<%s instance at %s>" % (self.__class__.__name__, id(self))

    def __str__(self):
        return "%s (\n\ttest_mode_overrule=%s\n\ttest_mode=%s\n\tgunbot_location=%s\n\tgunbot_config=%s" \
            "\n\tgunthy_gui_config=%s\n\tgunthy_gui_gunbot_version=%s\n\tgunthy_gui_start=%s\n\tgunthy_gui_stop=%s" \
            "\n\tbackup=%s\n)" % (
            self.__class__.__name__,
            self.test_mode_overrule,
            self.test_mode,
            self.gunbot_location,
            self.gunbot_config,
            self.gunthy_gui_config,
            self.gunthy_gui_gunbot_version,
            self.gunthy_gui_start,
            self.gunthy_gui_stop,
            self.backup
            )


class GunbotConfigUpdater(object):

    __SECRETS_FILE = 'secrets.json'
    __BACKUP_EXT = '.backup'

    config = None

    def __init__(self, config_dir=None, test_mode=None):
        self.config_handler = GunbotConfigHandler(config_dir=config_dir, test_mode=test_mode)
        self.secrets_file_path = os.path.join(self.config_handler.gunbot_location, self.__SECRETS_FILE)
        if not os.path.isfile(self.secrets_file_path):
            logging.error("Secrets file missing: {}".format(self.secrets_file_path))
            exit(-4)
        logging.info("Loading API keys from {}".format(self.secrets_file_path))
        with open(self.secrets_file_path) as secrets_file:
            self.secrets = json.load(secrets_file)
            secrets_file.close()

    def __update_keys(self):
        for secret in self.secrets['exchanges']:
            exchange = secret['exchange']
            logging.info("Updating API keys for {}".format(exchange))
            self.config['exchanges'][exchange]['key'] = secret['api_key']
            self.config['exchanges'][exchange]['secret'] = secret['api_secret']

    def __update_gunthy_gui(self):
        exchanges = ['poloniex', 'kraken', 'bittrex', 'cryptopia']
        gui_config = []
        for exchange in exchanges:
            if exchange in self.config['pairs']:
                logging.info("Updating Gunthy GUI config for {}".format(exchange))
                pairs = self.config['pairs'][exchange]
                pair_config = {}
                for pair in pairs:
                    loaded_pair_config = self.config['pairs'][exchange][pair]
                    pair_config['gunbotVersion'] = self.config_handler.gunthy_gui_gunbot_version
                    pair_config['exchange'] = exchange
                    pair_config['pair'] = pair
                    pair_config['config'] = {}
                    pair_config['config']['strategy'] = loaded_pair_config['strategy']
                    pair_config['config']['override'] = {}
                    for key in loaded_pair_config['override']:
                        pair_config['config']['override'][key] = loaded_pair_config['override'][key]
                    gui_config.append(pair_config.copy())
        self.__write_json_to_file(self.config_handler.gunthy_gui_config, gui_config, True)

    def __update_gunbot_config(self):
        self.__write_json_to_file(self.config_handler.gunbot_config, self.config, True)

    def __write_json_to_file(self, dest_file, json_data, backup=False):
        dest_path = os.path.join(self.config_handler.gunbot_location, dest_file)
        backup_path = dest_path + self.__BACKUP_EXT
        if backup and os.path.isfile(backup_path):
            logging.info("Deleting old backup file {}".format(backup_path))
            os.remove(backup_path)
        if backup and os.path.isfile(dest_path):
            logging.info("Backing up config file from '{}' to '{}'".format(dest_path, backup_path))
            shutil.copy2(dest_path, backup_path)
        with open(dest_path, 'w') as f:
            json.dump(json_data, f, sort_keys=False, indent=4, ensure_ascii=False)
            f.close

    def __rollback_config(self, dest_file):
        dest_path = os.path.join(self.config_handler.gunbot_location, dest_file)
        backup_path = dest_path + self.__BACKUP_EXT
        if not os.path.isfile(backup_path):
            logging.info("Backup file '{}' does not exist, skipping".format(backup_path))
        elif os.path.isfile(dest_path):
            logging.info("Deleting configuration file '{}'".format(dest_path))
            os.remove(dest_path)
            logging.info("Restoring previous configuration file from '{}' to '{}'".format(dest_path, backup_path))
            shutil.copy2(backup_path, dest_path)
            logging.info("Deleting backup configuration file '{}'".format(backup_path))
            os.remove(backup_path)

    def __restart_gunthy_gui(self):
        cmd_stop = self.config_handler.gunbot_stop
        cmd_start = self.config_handler.gunbot_start
        cmd_gui_stop = self.config_handler.gunthy_gui_stop
        cmd_gui_start = self.config_handler.gunthy_gui_start
        if self.config_handler.test_mode:
            logging.info("Gunbot stop = {}".format(cmd_stop))
            logging.info("Gunthy GUI stop = {}".format(cmd_gui_stop))
            logging.info("Gunthy GUI start = {}".format(cmd_gui_start))
            logging.info("Gunbot start = {}".format(cmd_start))
        else:
            subprocess.check_output(cmd_stop.split(' '))
            subprocess.check_output(cmd_gui_stop.split(' '))
            subprocess.check_output(cmd_gui_start.split(' '))
            subprocess.check_output(cmd_start.split(' '))

    def execute(self, config_url):
        logging.info("Loading Gunbot configuration from {}".format(config_url))
        response = requests.get(config_url)
        self.config = json.loads(response.text)
        self.__update_keys()
        self.__update_gunbot_config()
        if self.config_handler.gunthy_gui_gunbot_enabled:
            self.__update_gunthy_gui()
            self.__restart_gunthy_gui()

    def rollback(self):
        logging.info("Rollback configuration files to previous version")
        self.__rollback_config(self.config_handler.gunbot_config)
        if self.config_handler.gunthy_gui_gunbot_enabled:
            self.__rollback_config(self.config_handler.gunthy_gui_config)


# TODO send Telegram message when updated or on error
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='download a Gunbot configuration from the specified url')
    parser.add_argument('-r', '--rollback', help='rollback to the previous configuration', action='store_true')
    parser.add_argument('url', nargs='?', help='url to retrieve Gunbot configuration from')
    parser.add_argument('-c', '--changed', help='only update if web page changed', action='store_true')
    parser.add_argument('-t', '--testmode', help='create test configuration files only', action='store_true')
    verbose_group = parser.add_mutually_exclusive_group()
    verbose_group.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    verbose_group.add_argument('-q', '--quiet', help="no output", action='store_true')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = parser.parse_args()
    name = os.path.basename(os.path.abspath(__file__))

    if args.url is None and not args.rollback:
        # Use Dante's default pastbin url
        args.url = DEFAULT_URL
    if args.url is not None and args.rollback:
        print '{}: url and rollback cannot be specified at the same time'.format(args.prog)
        print 'try \'{} --help\' for more information.'.format(args.prog)
        exit(-2)
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    if args.changed:
        monitor = WebPageMonitor(args.url, force_use_hash=True)
        if not monitor.check():
            exit(0)
    if args.testmode:
        updater = GunbotConfigUpdater(test_mode=args.testmode)
    else:
        updater = GunbotConfigUpdater()
    if args.rollback:
        updater.rollback()
    else:
        updater.execute(args.url)
