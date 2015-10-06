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

"""
This package :ref:`integrates <framework_integration>` the module with
pyramid_.

.. _pyramid: http://docs.pylonsproject.org/projects/pyramid/en/latest/
"""
from .authenticator import Authenticator
from score.init import parse_dotted_path


class LoginAuthenticator(Authenticator):
    """
    An :class:`Authenticator <score.auth.authenticator.Authenticator>` that will
    automatically check if a *username* and *password* were submitted via POST
    and log the user in if the credentials match.

    The class is assuming that the password member is an
    :class:`sqlalchemy_utils.types.password.PasswordType` and will thus compare
    the POSTed *password* directly. It expects a submitted form with the
    following structure to trigger the automatic login on any URL:

    .. code-block:: jinja

        <form method="post">
            <input name="username" />
            <input name="password" type="password" />
            <input type="submit" />
        </form>
    """

    def __init__(self, conf, next, actor_cls):
        super().__init__(conf, next)
        if isinstance(actor_cls, str):
            actor_cls = parse_dotted_path(actor_cls)
        self.actor_cls = actor_cls

    def retrieve(self, ctx):
        user = self._login_attempt(ctx)
        if user is None:
            user = self.next.retrieve(ctx)
        return user

    def _login_attempt(self, ctx):
        if not hasattr(ctx, 'request'):
            return None
        if 'username' not in ctx.request.POST:
            return None
        if 'password' not in ctx.request.POST:
            return None
        user = ctx.db.query(self.actor_cls).\
            filter(self.actor_cls.username == ctx.request.POST['username']).\
            first()
        if not user:
            return None
        if user.password != ctx.request.POST['password']:
            return None
        self.next.store(ctx, user)
        return user
