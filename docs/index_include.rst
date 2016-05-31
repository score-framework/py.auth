.. module:: score.auth
.. role:: confkey
.. role:: confdefault

**********
score.auth
**********

This module provides authentication ("who are you?") and authorization ("are
you allowed to do this?") for your application. The former is implemented with
the use of so-called :class:`Authenticators <.Authenticator>`, the latter with
a clever workflow for defining and probing rules.

Quickstart
==========

Authentication
--------------

Add this module to your initialization list and configure it to make use of the
:mod:`score.session` module (assuming you have a ``User`` class in your
database):

.. code-block:: ini
    :emphasize-lines: 4,5,7-9

    [score.init]
    modules =
        score.db
        score.session
        score.auth

    [auth]
    authenticators =
        score.auth.authenticator.SessionAuthenticator(path.to.User)

You can now store assign a ``User`` to your :term:`context <context object>`
and the authenticator will store and retrieve that user from your session in
subsequent contexts:

>>> with score.ctx.Context() as ctx:
...     assert ctx.actor is None
...     ctx.actor = ctx.db.query(path.to.User).first()
... 
>>> with score.ctx.Context() as ctx:
...     assert ctx.actor is ctx.db.query(path.to.User).first()
... 

Authorization
-------------

Create a rule set for authorization queries and add some rules:

.. code-block:: python

    ruleset = score.auth.RuleSet()

    @ruleset.rule('confuse', Cat)
    def confuse(ctx, cat):
        # decide, whether this cat may be confused given this context
        return isinstance(ctx.actor, Vet)

The module configuration should point to the given rule set for authorization:

.. code-block:: ini
    :emphasize-lines: 4

    [auth]
    authenticators =
        score.auth.authenticator.SessionAuthenticator(path.to.User)
    ruleset = path.to.ruleset

You can now query your context for permissions:

>>> ctx.permits('confuse', cat)
False

Configuration
=============

.. autofunction:: init

Details
=======

Authenticators
--------------

When the configured module is requested to determine the currently active
user, it will need to forward the request to registered :class:`Authenticators
<.Authenticator>`. These Authenticators are organized as a :term:`chain
<authentication chain>`, each Authenticator asking the next one if it cannot
figure out the current user.

A typical chain of Authenticators could look like the following:

- A login authenticator: Tests, if a form was submitted, that
  would log the user in. If it was not, it asks the next Authenticator.
- :class:`.SessionAuthenticator`: Checks the session, if there is a previously
  stored user. Continues asking the next Authenticator if there is not.
- :class:`.NullAuthenticator`: Returns `None` to indicate that the chain has
  reached its end.

An example login authenticator could look like the following:

.. code-block:: python

    from score.auth import Authenticator

    class LoginAuthenticator(Authenticator):

        def retrieve(self, ctx):
            user = self._perform_login(ctx)
            if user:
                return user
            else:
                # the login was not successful, ask the next authenticator to
                # retrieve the current user.
                return self.next.retrieve(ctx)

        def _perform_login(self, ctx):
            if not hasattr(ctx, 'http'):
                return None
            if 'username' not in ctx.http.request.POST:
                return None
            if 'password' not in ctx.http.request.POST:
                return None
            username = ctx.http.request.POST['username']
            user = ctx.db.query(db.User).\
                filter(db.User.username == username)
                first()
            if not user:
                return None
            if not user.verify_password(ctx.http.request.POST['password']):
                return None
            # we have a logged in user, so pass it to all subsequent
            # authenticators to allow them storing the value.
            self.next.store(ctx, user)
            return user


RuleSets
--------

The :class:`.RuleSet` is a decorator for defining :term:`rules <rule>`. A rule
consists of an operation and any number of `type` objects, like the following:

.. code-block:: python

    ruleset = score.auth.RuleSet()

    @ruleset.rule('sing', Song)
    def sing(ctx, song):
        return song.performer == ctx.actor and \
            Permission.SING_A_SONG in actor.permissions

Whenever the context is queried whether it is possible to sing a specific Song,
this function will be invoked to provide the answer:

.. code-block:: python

    if ctx.permits('sing', Song.load('Galaxy Song')):
        # this must be Stephen Hawking!

It is also possible to omit the parameters to the decorator, if the rule does
not require any objects. The name of the rule will be the name of the function
in this case:

.. code-block:: python

    ruleset = score.auth.RuleSet()

    @ruleset.rule  # NOTE: no definitions here ..
    def sing(ctx):  # .. and no additional function parameters
        pass


API
===

.. autofunction:: init

.. autoclass:: ConfiguredAuthModule

    .. attribute:: ruleset

        A configured instance of :class:`.RuleSet`.

    .. automethod:: permits

.. autoclass:: RuleSet

    .. attribute:: rules

        A set of rules added by the :class:`rule` decorator.

    .. automethod:: permits

    .. autoclass:: score.auth::RuleSet.rule

.. autoclass:: score.auth.authenticator.Authenticator

.. autoclass:: score.auth.authenticator.NullAuthenticator

.. autoclass:: score.auth.authenticator.SessionAuthenticator
