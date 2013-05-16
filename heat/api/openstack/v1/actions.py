# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from webob import exc

from heat.api.openstack.v1 import util
from heat.common import wsgi
from heat.rpc import api as engine_api
from heat.common import identifier
from heat.rpc import client as rpc_client
import heat.openstack.common.rpc.common as rpc_common


class ActionController(object):
    """
    WSGI controller for Actions in Heat v1 API
    Implements the API for stack actions
    """

    _action_keymap = {engine_api.STACK_ACTION_SUSPEND: 'suspend'}

    def __init__(self, options):
        self.options = options
        self.engine = rpc_client.EngineClient()

    @util.identified_stack
    def index(self, req, identity):
        """
        Lists summary information for all actions available for this stack
        """

        try:
            act_list = self.engine.list_stack_actions(req.context, identity)
        except rpc_common.RemoteError as ex:
            return util.remote_error(ex)

        try:
            for a in act_list:
                a['action'] = self._action_keymap[a['action']]
        except KeyError:
            raise exc.HTTPInternalServerError(_("Unexpected engine action"))

        return {'actions': act_list}

    @util.identified_stack
    def action(self, req, identity, body={}):
        """
        Performs a specified action on a stack, the body is expecting to
        contain exactly one item whose key specifies the action
        """

        if len(body) < 1:
            raise exc.HTTPBadRequest(_("No action specified"))

        if len(body) >1:
            raise exc.HTTPBadRequest(_("Multiple actions specified"))

        ac = body.keys()[0]
        if ac not in self._action_keymap.values():
            raise exc.HTTPBadRequest(_("Invalid action %s specified" % ac))

        if ac == 'suspend':
            try:
                res = self.engine.stack_suspend(req.context, identity)
            except rpc_common.RemoteError as ex:
                return util.remote_error(ex)
        else:
            raise exc.HTTPInternalServerError(_("Unexpected engine action %s"))


def create_resource(options):
    """
    Actions action factory method.
    """
    # TODO(zaneb) handle XML based on Content-type/Accepts
    deserializer = wsgi.JSONRequestDeserializer()
    serializer = wsgi.JSONResponseSerializer()
    return wsgi.Resource(ActionController(options), deserializer, serializer)
