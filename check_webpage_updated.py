"""
This script checks if a web page has changed since the last check. If the web page does not support the header
Last-Modified then it uses an MD5 hash to track changes.
"""
import hashlib
import logging
from datetime import datetime

import requests

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class WebPageMonitor(object):
    MONITOR_FILE = '.webPageMonitor'
    LAST_MODIFIED_HEADER = 'Last-Modified'

    def __init__(self, url, monitor_file=None, force_use_hash=False, auto_switch_hash=False):
        if monitor_file is None:
            self.monitor_file = self.MONITOR_FILE
        else:
            self.monitor_file = monitor_file
        self.url = url
        self.force_use_hash = force_use_hash
        self.auto_switch_hash = auto_switch_hash
        self.url_changed = False

    def __write_monitor_file(self, data):
        try:
            with open(self.monitor_file, 'w') as fh:
                fh.write(data)
                fh.close()
        except IOError as e:
            logging.error("Error writing to file ({}): {}".format(self.monitor_file, e.strerror))

    def __read_monitor_file(self):
        # Load previous data from file
        data = None
        try:
            with open(self.monitor_file, 'r') as fh:
                data = fh.read()
                fh.close()
        except IOError as e:
            logging.warn("Could not read file ({}): {}".format(self.monitor_file, e.strerror))
        except EOFError:
            logging.warn("File loaded, but empty")
        return data

    def __check_header(self):
        prev_timestamp = self.__read_monitor_file()

        try:
            if prev_timestamp is not None:
                prev_timestamp = datetime.strptime(prev_timestamp, '%Y-%m-%d %H:%M:%S')

                logging.debug("Previous timestamp: {}".format(prev_timestamp))
        except ValueError:
            logging.warn("Value cannot be converted to a timestamp: {}".format(prev_timestamp))

        # We only want the headers, so stream is set to true
        response = requests.get(self.url, stream=True)

        if self.LAST_MODIFIED_HEADER in response.headers:
            last_modified = response.headers[self.LAST_MODIFIED_HEADER]

            # Convert to a datetime object
            timestamp = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')

            logging.debug("Header last-modified found. Returned headers: {}".format(response.headers))
            logging.debug("Timestamp: {}".format(timestamp))

            if prev_timestamp is None or prev_timestamp != timestamp:
                self.url_changed = True
                logging.info("{} header changed: previous={}, new={}".format(
                    self.LAST_MODIFIED_HEADER, prev_timestamp, timestamp))
                self.__write_monitor_file(str(timestamp))
            else:
                logging.info("{} header is the same: {}".format(self.LAST_MODIFIED_HEADER, timestamp))
        else:
            headers = '\n\t'.join('{}: {}'.format(k, v) for k, v in response.headers.items())
            msg = "Error: header {} NOT found. Returned headers:\n\t{}".format(
                self.LAST_MODIFIED_HEADER, headers)
            logging.warn(msg)
            if self.auto_switch_hash:
                logging.warn("Switching to hash")
                self.__check_hash()
            else:
                raise KeyError(msg)

    def __check_hash(self):
        prev_web_page_hash = self.__read_monitor_file()

        if prev_web_page_hash is not None:
            logging.debug("Previous hash: {}".format(prev_web_page_hash))

        response = requests.get(self.url)
        web_page_hash = hashlib.md5(response.text).hexdigest()

        if prev_web_page_hash is None or prev_web_page_hash != web_page_hash:
            self.url_changed = True
            logging.info("Hash changed: previous={}, new={}".format(prev_web_page_hash, web_page_hash))
            self.__write_monitor_file(web_page_hash)
        else:
            logging.info("Hash is the same: {}".format(web_page_hash))

    def check(self):
        self.url_changed = False

        if self.force_use_hash:
            self.__check_hash()
        else:
            self.__check_header()

        return self.url_changed
