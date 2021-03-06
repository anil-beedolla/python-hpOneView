# -*- coding: utf-8 -*-

"""
networking.py
~~~~~~~~~~~~

This module implements Settings HP OneView REST API
"""

__title__ = 'networking'
__version__ = '0.0.1'
__copyright__ = '(C) Copyright 2012-2014 Hewlett-Packard Development ' \
                ' Company, L.P.'
__license__ = 'MIT'
__status__ = 'Development'

###
# (C) Copyright 2014 Hewlett-Packard Development Company, L.P.
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

from hpOneView.common import *
from hpOneView.connection import *
from hpOneView.activity import *
from hpOneView.exceptions import *


class networking(object):

    def __init__(self, con):
        self._con = con
        self._activity = activity(con)

    ###########################################################################
    # Logical Interconnect Group
    ###########################################################################
    def update_settings_from_default(self, settings={}):
        if not settings:
            settings = make_enet_settings('__NoName__')
        default = self._con.get('%s/defaultSettings')
        return default

        for key in list(settings.keys()):
            if key != 'name':
                settings[key] = default[key]
        return settings

    def create_lig(self, lig, blocking=True, verbose=False):
        task, body = self._con.post(uri['lig'], lig)
        task, entity = self._activity.make_task_entity_tuple(task)
        if blocking is True:
            task = self._activity.wait4task(task, verbose=verbose)
        return entity

    def update_lig(self, lig, blocking=True, verbose=False):
        task, body = self._con.put(lig['uri'], lig)
        if blocking is True:
            task = self._activity.wait4task(task, verbose=verbose)
        return task

    def delete_lig(self, lig, blocking=True, verbose=False):
        task, body = self._con.delete(lig['uri'])
        if blocking is True:
            task = self._activity.wait4task(task, verbose=verbose)
        return task

    def get_ligs(self):
        return get_members(self._con.get(uri['lig']))

    def get_lig_by_name(self, ligname):
        return self._con.get_entity_byfield(uri['lig'], 'name', ligname)

    def get_interconnect_types(self):
        # get all the supported interconnect types
        resp = get_members(self._con.get(uri['ictype']))
        return resp

    def get_lis(self):
        return get_members(self._con.get(uri['li']))

    ###########################################################################
    # Connection Templates
    ###########################################################################
    def get_connection_templates(self):
        return get_members(self._con.get(uri['ct']))

    def update_net_ctvalues(self, xnet, bw={}):
        if not bw:
            return
        if not xnet:
            raise HPOneViewInvalidResource('Missing Network')
        defaultCT = self._con.get(xnet['connectionTemplateUri'])
        defaultCT['bandwidth']['maximumBandwidth'] = bw['maximumBandwidth']
        defaultCT['bandwidth']['typicalBandwidth'] = bw['typicalBandwidth']
        task, body = self._con.put(defaultCT['uri'], defaultCT)
        return self._activity.make_task_entity_tuple(task)

    ###########################################################################
    # NetworkSets
    ###########################################################################
    def create_networkset(self, name, nets=[], bw={},
                          blocking=True, verbose=False):
        nset = make_netset_dict(name, nets)
        body = self._con.conditional_post(uri['nset'], nset)
        task, entity = self._activity.make_task_entity_tuple(body)
        if not task and not entity:
            # contitional_post returned an already existing resource
            return body
        else:
            # assume we can update CT even if network create task is not cmpelt
            self.update_net_ctvalues(entity, bw)
            if blocking is True:
                task = self._activity.wait4task(task, tout=60, verbose=verbose)
            return entity

    def delete_networkset(self, networkset, blocking=True, verbose=False):
        task, body = self._con.delete(networkset['uri'])
        if blocking is True:
            task = self._activity.wait4task(task, verbose=verbose)
        return task

    def get_networksets(self):
        return get_members(self._con.get(uri['nset']))

    ###########################################################################
    # Networks
    ###########################################################################
    def create_enet_networks(self, prefix, vid_start, vid_count, bw={}):
        enet_list = []
        try:
            for vid in range(vid_start, vid_start + vid_count):
                enet_name = '%s%s' % (prefix, vid)
                enet_list.append(self.create_enet_network(enet_name,
                                                          vid,
                                                          bw=bw
                                                          ))
        except http.client.HTTPException:
            # All or nothing
            for enet in enet_list:
                try:
                    self._con.delete(enet['uri'])
                except http.client.HTTPException:
                    pass
            raise HPOneViewException('Could not create one or more networks')
        return enet_list

    def create_enet_network(self, name, vid,
                            purpose='General',
                            smartLink=True,
                            privateNetwork=False,
                            ethernetNetworkType='Tagged',
                            bw={},
                            blocking=True,
                            verbose=False):
        xnet = make_enet_dict(name, vid, smartLink=smartLink,
                              privateNetwork=privateNetwork, purpose=purpose,
                              ethernetNetworkType=ethernetNetworkType)
        task, entity = self.create_network(uri['enet'], xnet, bw, verbose)
        if blocking is True:
            task = self._activity.wait4task(task, tout=60, verbose=verbose)
        return entity

    def create_fc_network(self, name, attach='FabricAttach',
                          autodist=True, linktime=30, bw={},
                          managedSanUri=None, blocking=True, verbose=False):
        xnet = make_fc_dict(name, attach, autodist, linktime, managedSanUri)
        task, entity = self.create_network(uri['fcnet'], xnet, bw, verbose)
        if blocking is True:
            task = self._activity.wait4task(task, tout=60, verbose=verbose)
        return entity

    def create_network(self, uri, xnet, bw={}, verbose=False):
        # throws an exception if there is an error
        body = self._con.conditional_post(uri, xnet)
        task, entity = self._activity.make_task_entity_tuple(body)
        if not task and not entity:
            # contitional_post returned an already existing resource
            return None, body
        else:
            # assume we can update CT even if network create task is not cmpelt
            self.update_net_ctvalues(entity, bw)
            return task, entity

    def update_network(self, xnet):
        task, body = self._con.put(xnet['uri'], xnet)
        return self._activity.make_task_entity_tuple(task)

    def delete_network(self, xnet, blocking=True, verbose=False):
        task, body = self._con.delete(xnet['uri'])
        if blocking is True:
            task = self._activity.wait4task(task, verbose=verbose)
        return task

    def get_enet_networks(self):
        return get_members(self._con.get(uri['enet']))

    def get_fc_networks(self):
        return get_members(self._con.get(uri['fcnet']))

    ###########################################################################
    # Uplink Sets
    ###########################################################################
    def get_uplink_sets(self):
        return get_members(self._con.get(uri['uplink-sets']))

    def delete_uplink_set(self, uplink_set, blocking=True, verbose=False):
        task, body = self._con.delete(uplink_set['uri'])
        if blocking is True:
            task = self._activity.wait4task(task, verbose=verbose)
        return task

    ###########################################################################
    # Interconnects
    ###########################################################################
    def get_interconnects(self):
        return get_members(self._con.get(uri['ic']))

    def get_enet_network_by_name(self, nwname):
        return self._con.get_entity_byfield(uri['enet'], 'name', nwname)

    def get_fc_network_by_name(self, nwname):
        return self._con.get_entity_byfield(uri['fcnet'], 'name', nwname)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
