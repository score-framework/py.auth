# Copyright © 2015-2018 STRG.AT GmbH, Vienna, Austria
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

import logging
from score.init import (
    ConfiguredModule, parse_dotted_path, parse_call, parse_list)
from .authenticator import NullAuthenticator
from ._ruleset import RuleSet


log = logging.getLogger(__package__)


defaults = {
    'ctx.member': 'actor',
    'authenticators': [],
    'ruleset': None,
}


def init(confdict, ctx):
    """
    Initializes this module acoording to :ref:`our module initialization
    guidelines <module_initialization>` with the following configuration keys:

    :confkey:`ruleset` :confdefault:`RuleSet()`
        A dotted path to an instance of :class:`RuleSet` in your project. This
        module will be initialized without any rules, if this configuration key
        is omitted, resulting in denial of every operation.

    :confkey:`authenticators` :confdefault:`list()`
        List of :class:`Authenticators` capable of determining the current
        actor.

    :confkey:`ctx.member` :confdefault:`actor`
        The :term:`context member` under which the current actor should be made
        available. Leaving this at its default will allow you to access the
        current actor as the following:

        >>> ctx.actor
    """
    conf = defaults.copy()
    conf.update(confdict)
    if conf['ruleset'] in (None, 'None'):
        ruleset = RuleSet()
    else:
        ruleset = parse_dotted_path(conf['ruleset'])
    if 'authenticator' in conf:
        assert not conf['authenticators']
        conf['authenticators'] = [conf['authenticator']]
        del conf['authenticator']
    auth = ConfiguredAuthModule(ruleset, conf['ctx.member'])
    authenticator = NullAuthenticator()
    for line in reversed(parse_list(conf['authenticators'])):
        authenticator = parse_call(line, (auth, authenticator))
    auth.authenticator = authenticator
    _register_ctx_actor(conf, ctx, auth)
    _register_ctx_permits(conf, ctx, auth)
    return auth


def _register_ctx_actor(conf, ctx, auth):

    def constructor(ctx):
        return auth.authenticator.retrieve(ctx)

    def destructor(ctx, old, exception):
        new = getattr(ctx, conf['ctx.member'], None)
        auth.authenticator.store(ctx, new)

    def actor_persister(ctx):
        def persist():
            new = getattr(ctx, conf['ctx.member'], None)
            auth.authenticator.store(ctx, new)
        return persist

    ctx.register(conf['ctx.member'], constructor, destructor)
    ctx.register('persist_' + conf['ctx.member'], actor_persister)


def _register_ctx_permits(conf, ctx, auth):
    def constructor(ctx):
        def permits(operation, *args, raise_=False):
            return auth.permits(ctx, operation, *args, raise_=raise_)
        return permits
    ctx.register('permits', constructor)


class ConfiguredAuthModule(ConfiguredModule):
    """
    This module's :class:`configuration class
    <score.init.ConfiguredModule>`.
    """

    def __init__(self, ruleset, ctx_member):
        super().__init__(__package__)
        self.ruleset = ruleset
        self.ctx_member = ctx_member

    def permits(self, ctx, operation, *args, raise_=False):
        """
        A proxy for :meth:`RuleSet.permits` of the configured
        :attr:`ruleset` instance.
        """
        return self.ruleset.permits(ctx, operation, *args, raise_=raise_)
