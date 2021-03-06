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


def output_progress(progress):
    for status in progress:
        if 'statusUpdate' in status:
            print('    ', status['statusUpdate'])


def del_all_profiles(srv, force):
    srvrs = srv.get_servers()
    for server in srvrs:
        if server['powerState'] == 'On':
            print(('Powering Off Server:  %s' % server['name']))
            ret = srv.set_server_powerstate(server, 'Off', force=True)
            pprint(ret)

    profiles = srv.get_server_profiles()
    for profile in profiles:
        print(('Removing Profile %s' % profile['name']))
        ret = srv.remove_server_profile(profile, force)
        output_progress(ret['progressUpdates'])


def del_profile_by_name(con, srv, name, force):

    profiles = srv.get_server_profiles()
    for profile in profiles:
        if profile['name'] == name:
            server = con.get(profile['serverHardwareUri'])
            if server['powerState'] == 'On':
                print(('Powering Off Server:  %s' % server['name']))
                ret = srv.set_server_powerstate(server, 'Off', force=True)
                pprint(ret)
            print(('Removing Profile %s' % profile['name']))
            ret = srv.remove_server_profile(profile, force)
            output_progress(ret['progressUpdates'])
            return
    print('Profile: ', name, ' not found')


def main():
    parser = argparse.ArgumentParser(add_help=True,
                        formatter_class=argparse.RawTextHelpFormatter,
                                     description='''
    Delete server profile

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
    parser.add_argument('-f', dest='force', required=False,
                        action='store_true',
                        help='''
    Force the removal of the server profile''')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-n', dest='name',
                       help='''
    Name of the server profile to delete''')
    group.add_argument('-d', dest='delete_all',
                       action='store_true',
                       help='''
    Remove ALL server profiles and exit''')

    args = parser.parse_args()
    credential = {'userName': args.user, 'password': args.passwd}

    con = hpov.connection(args.host)
    srv = hpov.servers(con)

    if args.proxy:
        con.set_proxy(args.proxy.split(':')[0], args.proxy.split(':')[1])
    if args.cert:
        con.set_trusted_ssl_bundle(args.cert)

    login(con, credential)
    acceptEULA(con)

    if args.delete_all:
        del_all_profiles(srv, args.force)
        sys.exit()

    del_profile_by_name(con, srv, args.name, args.force)

if __name__ == '__main__':
    import sys
    import argparse
    sys.exit(main())

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
