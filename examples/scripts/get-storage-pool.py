#!/usr/bin/env python3
###
# (C) Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
###

import sys
if sys.version_info < (3, 4):
    raise Exception('Must use Python 3.4 or later')

import hpOneView as hpov
from pprint import pprint


def acceptEULA(con):
    # See if we need to accept the EULA before we try to log in
    con.get_eula_status()
    try:
        if con.get_eula_status() is True:
            print('EULA display needed')
            con.set_eula('no')
    except Exception as e:
        print('EXCEPTION:')
        print(e)


def login(con, credential):
    # Login with givin credentials
    try:
        con.login(credential)
    except:
        print('Login failed')


def get_pool_by_name(sto, stosys_name, pool_name):
    systems = sto.get_storage_systems()
    for sys in systems:
        if sys['name'] == stosys_name:
            # search managed pools in matching storage system
            pools = sys['managedPools']
            for pool in pools:
                if pool['name'] == pool_name:
                    print('Getting Storage Pool: ', pool['name'], ' in',
                          stosys_name)
                    pprint(pool)
                    return
            print('Pool: ', pool_name, ' not found')
            return
    print('Storage System: ', stosys_name, ' not found')


def get_all_pools(sto):
    pools = sto.get_storage_pools()
    for pool in pools['members']:
        print('Getting Storage Pool: ', pool['name'])
        pprint(pool)
        print()


def main():
    parser = argparse.ArgumentParser(add_help=True,
                        formatter_class=argparse.RawTextHelpFormatter,
                                     description='''
    Display Storage Pools

    Usage: ''')
    parser.add_argument('-a', dest='host', required=True,
                        help='''
    HP OneView Appliance hostname or IP address''')
    parser.add_argument('-u', dest='user', required=False,
                        default='Administrator',
                        help='''
    HP OneView Username''')
    parser.add_argument('-p', dest='passwd', required=True,
                        help='''
    HP OneView Password''')
    parser.add_argument('-c', dest='cert', required=False,
                        help='''
    Trusted SSL Certificate Bundle in PEM (Base64 Encoded DER) Format''')
    parser.add_argument('-y', dest='proxy', required=False,
                        help='''
    Proxy (host:port format''')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-s', dest='sto_name',
                       help='''
    Name of storage system. This option requires the pool name option "-n"
    to be specified''')
    group.add_argument('-g', dest='get_all',
                       action='store_true',
                       help='''
    Display ALL storage pools and exit''')
    parser.add_argument('-n', dest='pool_name', required=False,
                        help='''
    Storage pool name''')

    args = parser.parse_args()
    credential = {'userName': args.user, 'password': args.passwd}

    con = hpov.connection(args.host)
    sto = hpov.storage(con)

    if args.proxy:
        con.set_proxy(args.proxy.split(':')[0], args.proxy.split(':')[1])
    if args.cert:
        con.set_trusted_ssl_bundle(args.cert)

    login(con, credential)
    acceptEULA(con)

    if args.sto_name:
        if args.pool_name:
            get_pool_by_name(sto, args.sto_name, args.pool_name)
        else:
            print ('Storage system MUST be accompanied by storage pool name')
        sys.exit()

    if args.get_all:
        get_all_pools(sto)

if __name__ == '__main__':
    import sys
    import argparse
    sys.exit(main())

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
