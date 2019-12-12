# Copyright © 2015-2018 STRG.AT GmbH, Vienna, Austria
# Copyright © 2019 Necdet Can Ateşman, Vienna, Austria
#
# This file is part of the The SCORE Framework.
#
# The SCORE Framework and all its parts are free software: you can redistribute
# them and/or modify them under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation which is in
# the file named COPYING.LESSER.txt.
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
# the discretion of STRG.AT GmbH also the competent court, in whose district
# the Licensee has his registered seat, an establishment or assets.

from collections import OrderedDict
import logging
import warnings

log = logging.getLogger('score.auth')


class RuleSet:
    """
    Stores :term:`rules <rule>` and handles :term:`operations <operation>` for
    classes.
    """

    def __init__(self):
        self.rules = {}

    def rule(self, operation, *args):
        """
        Decorator for adding a :term:`rule` to this RuleSet.

        The function can be used in two different ways: Either it directly
        annotates a function …

        .. code-block:: python

            @ruleset.rule
            def sing(ctx):
                return ctx.actor.name == 'Stephen Hawking'

        … or it defines an operation and a list of argument types, which must
        match the types of the arguments of the call to
        :meth:`.RuleSet.permits`:

        .. code-block:: python

            @ruleset.rule('rewrite', Song)
            def rewrite_song(ctx, song):
                return True  # songs may be rewritten at any time
        """
        if callable(operation):
            if operation.__name__ not in self.rules:
                self.rules[operation.__name__] = OrderedDict()
            self.rules[operation.__name__][tuple()] = operation
            return operation

        def capturer(func):
            if operation not in self.rules:
                self.rules[operation] = OrderedDict()
            self.rules[operation][args] = func
            return func

        return capturer

    def permits(self, ctx, operation, *args, raise_=False):
        """
        Checks if given *operation* is allowed on given *args* in given
        *context*.
        """
        for rule_args, rule_test in self.rules.get(operation, {}).items():
            if len(args) != len(rule_args):
                continue
            for i, arg in enumerate(args):
                if not isinstance(args[i], rule_args[i]):
                    break
            else:
                result = rule_test(ctx, *args)
                if not result and raise_:
                    raise NotAuthorized(operation, args)
                log.debug({'operation': operation,
                           'args': args,
                           'result': result})
                return result
        warnings.warn('No rules defined for operation "%s(%s)"' %
                      (operation, ','.join(map(str, map(type, args)))))
        if raise_:
            raise NotAuthorized(operation, args)
        return False


class NotAuthorized(Exception):
    """
    Thrown when the authorization for an operation failed.
    """

    def __init__(self, operation, args):
        super().__init__('Context does not permit %s(%s)' %
                         (operation, ','.join(map(str, map(type, args)))))
