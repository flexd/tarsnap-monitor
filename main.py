#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()
import csv
import StringIO
from collections import OrderedDict
from pushbullet import Pushbullet
import confit
import argparse
import sys

template = {
    'balance_limit': float,
    'credentials': {
        'pushbullet': str,
        'tarsnap_address': str,
        'tarsnap_password': str,
    }
}
config = confit.LazyConfig('TarsnapMonitor', __name__)
parser = argparse.ArgumentParser(description='Tarsnap monitor')
parser.add_argument('--address', '-addr', dest='tarsnap_address', metavar='TARSNAP_ADDRESS',
                    help='tarsnap username address')
parser.add_argument('--password', '-pass', dest='tarsnap_password',
                    metavar='TARSNAP_PASSWORD',
                    help='tarsnap password')
parser.add_argument('--pushbullet', '-push', dest='pushbullet',
                    metavar='PUSHBULLET',
                    help='pushbullet api key')
parser.add_argument('--limit', '-l', dest='balance_limit',
                    metavar='BALANCE_LIMIT',
                    help='Tarsnap balance limit')
parser.add_argument('--verbose', '-v', dest='verbose', action='store_true',
                    help='print debugging messages')
parser.add_argument('--debug', '-d', dest='debug', action='store_true',
                    help='debug mode')

args = parser.parse_args()
config.set_args(args)
valid = config.get(template)
if args.verbose:
    print 'configuration directory is %s' % config.config_dir()

pb = Pushbullet(valid.credentials.pushbullet)

phone = pb.devices[1]

r = requests.post('https://www.tarsnap.com/manage.cgi?action=verboseactivity&format=csv',
                  data={"address": valid.credentials.tarsnap_address,
                        "password": valid.credentials.tarsnap_password})

balances = OrderedDict()
last_balance = 0.0
usage_log = OrderedDict()
if r.status_code == 200:
    if "Password is incorrect" in r.text:
        print "Password is incorrect."
        sys.exit()
    raw_csv = StringIO.StringIO(r.text)
    for row in csv.DictReader(raw_csv):
        if row["RECTYPE"] == 'Balance':
            balances[row["DATE"]] = float(row["BALANCE"])
        else:
            usage_log[row["DATE"]] = row
    last_balance = balances.values()[-1]
    if last_balance < valid.balance_limit:
        if not args.debug:
            pb.push_note("Tarsnap", "Your Tarsnap balance is under %f. Current balance %f" % (valid.balance_limit, last_balance))
        else:
            print "balance is under limit, limit: %f, value: %f" % (valid.balance_limit, last_balance)
