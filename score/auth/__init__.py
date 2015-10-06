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

import logging
from score.init import (
    ConfiguredModule, parse_dotted_path, parse_call, parse_list)
import warnings
from .authenticator import NullAuthenticator


log = logging.getLogger(__package__)


defaults = {
    'ctx.member': 'actor',
    'authenticators': [],
    'ruleset': None,
}


def init(confdict, ctx_conf):
    """
    Initializes this module acoording to :ref:`our module initialization
    guidelines <module_initialization>` with the following configuration keys:

    :confkey:`ruleset` :faint:`[default=RuleSet()]`
        A dotted path to an instance of :class:`RuleSet` in your project. This
        module will be initialized without any rules, if this configuration key
        is omitted, resulting in denial of every operation.

    :confkey:`authenticators` :faint:`[default=list()]`
        List of :class:`Authenticators` capable of determining the current
        actor.

    :confkey:`ctx.member` :faint:`[default=actor]`
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
    auth_conf = ConfiguredAuthModule(ruleset, conf['ctx.member'])
    authenticator = NullAuthenticator()
    for line in reversed(parse_list(conf['authenticators'])):
        authenticator = parse_call(line, (auth_conf, authenticator))
    auth_conf.authenticator = authenticator
    _register_ctx_actor(conf, ctx_conf, auth_conf)
    _register_ctx_permits(conf, ctx_conf, auth_conf)
    return auth_conf


def _register_ctx_actor(conf, ctx_conf, auth_conf):
    def constructor(ctx):
        return auth_conf.authenticator.retrieve(ctx)
    def destructor(ctx, old, exception):
        try:
            new = getattr(ctx, conf['ctx.member'])
        except AttributeError:
            new = None
        if new != old:
            auth_conf.authenticator.store(ctx, new)
    ctx_conf.register(conf['ctx.member'], constructor, destructor)
    def actor_persister(ctx):
        def persist():
            try:
                new = getattr(ctx, conf['ctx.member'])
            except AttributeError:
                new = None
            auth_conf.authenticator.store(ctx, new)
        return persist
    ctx_conf.register('persist_' + conf['ctx.member'], actor_persister)


def _register_ctx_permits(conf, ctx_conf, auth_conf):
    def constructor(ctx):
        def permits(operation, *args):
            actor = getattr(ctx, conf['ctx.member'])
            return ctx_conf.permits(actor, operation, *args)
        return permits
    ctx_conf.register('permits', constructor)


class ConfiguredAuthModule(ConfiguredModule):
    """
    This module's :class:`configuration class
    <score.init.ConfiguredModule>`.
    """

    def __init__(self, ruleset, ctx_member):
        super().__init__(__package__)
        self.ruleset = ruleset
        self.ctx_member = ctx_member

    def permits(self, actor, operation, obj):
        """
        A proxy for :meth:`RuleSet.permits` of the configured
        :attr:`ruleset` instance.
        """
        return self.ruleset.permits(actor, operation, obj)


class ActorMixin:

    @property
    def permissions(self):
        return list(set([permission for group in self.groups
                         for permission in group.permissions]))


class RuleSet:
    """
    Stores :term:`rules <rule>` and handles :term:`operations <operation>` for
    classes.
    """

    rules = {}

    class rule:
        """
        Decorator for adding a :term:`rule` to the :attr:`ruleset
        <.ConfiguredAuthModule.ruleset>`. If no *operation* is given, the
        decorator will use the name of the decorated function.
        """

        def __init__(self, cls, operation=None):
            self.cls = cls
            self.operation = operation

        def __call__(self, func):
            if not self.operation:
                self.operation = func.__name__
            if self.cls not in RuleSet.rules:
                RuleSet.rules[self.cls] = {}
            RuleSet.rules[self.cls][self.operation] = func
            return func

    def permits(self, actor, operation, obj):
        """
        Checks if an :term:`actor` is allowed to perform an :term:`operation`
        to an object by using the :term:`rules <rule>` added to the
        :attr:`ruleset <.ConfiguredAuthModule.ruleset>`.
        """
        log.debug({'actor': actor, 'operation': operation, 'object': obj})
        try:
            cls_rules = self.rules[obj.__class__]
        except KeyError:
            try:
                cls_rules = next(rules
                                 for cls, rules in self.rules.items()
                                 if isinstance(obj, cls))
            except StopIteration:
                warnings.warn('No rules defined for class "%s".' %
                              obj.__class__.__name__)
                return False
        try:
            rule = cls_rules[operation]
        except KeyError:
            warnings.warn('No rule defined for operation "%s".' %
                          operation)
            return False
        return rule(obj, actor)
