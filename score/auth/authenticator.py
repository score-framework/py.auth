# Copyright © 2015 STRG.AT GmbH, Vienna, Austria
#
# This file is part of the The SCORE Framework.
#
# The SCORE Framework and all its parts are free software: you can redistribute
# them and/or modify them under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation which is in the
# file named COPYING.LESSER.txt.
#
# The SCORE Framework and all its parts are distributed without any WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. For more details see the GNU Lesser General Public
# License.
#
# If you have not received a copy of the GNU Lesser General Public License see
# http://www.gnu.org/licenses/.
#
# The License-Agreement realised between you as Licensee and STRG.AT GmbH as
# Licenser including the issue of its valid conclusion and its pre- and
# post-contractual effects is governed by the laws of Austria. Any disputes
# concerning this License-Agreement including the issue of its valid conclusion
# and its pre- and post-contractual effects are exclusively decided by the
# competent court, in whose district STRG.AT GmbH has its registered seat, at
# the discretion of STRG.AT GmbH also the competent court, in whose district the
# Licensee has his registered seat, an establishment or assets.

import pickle
from score.init import parse_dotted_path


class Authenticator:
    """
    An object that can query (and possibly remember) the currently acting user.
    """

    def __init__(self, conf, next):
        self.conf = conf
        self.next = next

    def retrieve(self, ctx):
        return self.next.retrieve(ctx)

    def store(self, ctx, actor):
        self.next.store(ctx, actor)


class NullAuthenticator(Authenticator):
    """
    Always returns `None` as the current user. This class is used as the last
    :class:`Authenticator` in an :term:`authentication chain`.
    """

    def __init__(self):
        pass

    def retrieve(self, ctx):
        return None

    def store(self, ctx, actor):
        pass


class SessionAuthenticator(Authenticator):
    """
    Makes a lookup in the current session :term:`context member`.
    """
    # TODO: document actor_class

    def __init__(self, conf, next, actor_class=None, session_key='actor'):
        super().__init__(conf, next)
        self.session_key = session_key
        if isinstance(actor_class, str):
            actor_class = parse_dotted_path(actor_class)
        self.dbcls = actor_class

    def retrieve(self, ctx):
        if self.session_key in ctx.session:
            return self._load(ctx, ctx.session[self.session_key])
        return self.next.retrieve(ctx)

    def store(self, ctx, actor):
        if actor is None:
            del ctx.session[self.session_key]
        else:
            ctx.session[self.session_key] = self._dump(actor)
        self.next.store(ctx, actor)

    def _dump(self, actor):
        if self.dbcls is None:
            return pickle.dumps(actor)
        return actor.id

    def _load(self, ctx, data):
        if self.dbcls is None:
            return pickle.loads(data)
        return ctx.db.query(self.dbcls).get(data)
