.. module:: score.auth
.. role:: faint
.. role:: confkey

**********
score.auth
**********

Introduction
============

This module provides authentication ("who are you?") and authorization ("are
you allowed to do this?") for your application. The former is implemented with
the use of so-called :class:`Authenticators <.Authenticator>`, the latter with
a clever workflow for defining and probing rules.


ActorMixin
==========

This module supplies an :class:`.ActorMixin`, which you can use to build your
authorization system. Example:

.. code-block:: python

    class Actor(Base, ActorMixin):
        name = Column(String, nullable=False)

    class User(Actor):
        username = Column(String, nullable=False)
        password = Column(PasswordType(schemes=['pbkdf2_sha512']))


Authenticators
==============

When the configured module is requested to determine the currently active
user, it will need to forward the request to registered :class:`Authenticators
<.Authenticator>`. These Authenticators are organized as a :term:`chain
<authentication chain>`, each Authenticator asking the next one if it cannot
figure out the current user.

A typical chain of Authenticators could look like the following:

- :class:`.pyramid.LoginAuthenticator`: Tests, if a form was submitted, that
  would log the user in. If it was not, it asks the next Authenticator.
- :class:`.SessionAuthenticator`: Checks the session, if there is a previously
  stored user. Continues asking the next Authenticator if there is not.
- :class:`.NullAuthenticator`: Returns `None` to indicate that the chain has
  reached its end.


RuleSets
========

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
not require any objects:

.. code-block:: python

    ruleset = score.auth.RuleSet()

    @ruleset.rule  # NOTE: no definitions here ..
    def sing(ctx):  # .. and no additional function parameters
        pass


Complete Example
----------------

Let's have a look at a working example building a simple authorization system
to illustrate the features of this module. First, you have to define your
:term:`permissions <permission>`. The best way to achieve this is to implement
a :ref:`declarative Enumeration <db_enumerations>` of your choice.

The following example defines permissions by creating the class ``Permission``,
uses the provided Mixins, the created :ref:`Base Class <db_base>` and the
functions :func:`create_relationship_class
<score.db.create_relationship_class>` and :func:`create_collection_class
<score.db.create_collection_class>` to create the relationships and collections
for :term:`actors <actor>` and :term:`groups <group>`.

.. code-block:: python

    # http://galaxysongasteroids.montypython.com/

    from sqlalchemy import Column, String
    import score.db
    import score.auth

    class Permission(score.db.Enum):
        SING_A_SONG = 'sing_a_song'
        SHOOT_ASTEROIDS = 'shoot_asteroids'

    Base = score.db.create_base()

    class Actor(Base, score.auth.ActorMixin):
        name = Column(String, nullable=False)

    class Group(Base):
        name = Column(String, nullable=False)

    ActorGroup = score.db.create_relationship_class(
        Actor, Group, 'groups',
        sorted=False, duplicates=False
    )

    GroupPermission = score.db.create_collection_class(
        Group, 'permissions', Column(Permission.db_type(), nullable=False),
        sorted=False, duplicates=False
    )

    stephen = Actor(name='Stephen Hawking')
    owners = Group(name='Owners Of The Galaxy')
    owners.permissions.append(Permission.SING_A_SONG)
    owners.permissions.append(Permission.SHOOT_ASTEROIDS)
    stephen.groups.append(owners)

As a result, the actor *Stephen Hawking* is a member of the group *Owners Of
The Galaxy* and is allowed to *sing a song* as well as *shoot asteroids*. You
can check if *Stephen Hawking* is allowed to *shoot asteroids* using his
permissions list:

>>> Permission.SHOOT_ASTEROIDS in stephen.permissions
True

In most cases it is necessary to define :term:`operations <operation>` for
different classes to refine existing :term:`permissions <permission>`.
Therefore we use the decorator :class:`RuleSet.rule`. Let's extend our example
above.

.. code-block:: python

    from sqlalchemy import Integer, ForeignKey
    from sqlalchemy.orm import relationship, backref

    class Song(Base):
        name = Column(String, nullable=False)
        performer_id = Column(Integer, ForeignKey('_actor.id'), nullable=False)
        performer = relationship('Actor', backref='songs')

    galaxy_song = Song(name='Galaxy Song', performer=stephen)

    my_ruleset = score.auth.RuleSet()

    @my_ruleset.rule(Song, 'sing')
    def sing_song(a_song, actor):
        return a_song.performer == actor and \
            Permission.SING_A_SONG in actor.permissions

    # ... init score and load a context ...
    ctx.permits('sing', galaxy_song)  # True if ctx.actor is stephen

In this example the :term:`actor` *Stephen Hawking* is performer of the
*Galaxy Song*. We defined a :term:`rule` allowing an :term:`actor` that is
performer of a song and having the :term:`permission` *sing a song* to sing
it. The decorator ``my_rulset.rule`` adds the decorated function
``sing_song`` to the :attr:`RuleSet.rules` of the instanced :class:`RuleSet`
``my_ruleset``. We then ask if *Stephen Hawking* is allowed to sing the
*Galaxy Song*. According to our implementation the :term:`actor` is allowed to.


Mixins
======

.. autoclass:: ActorMixin

    .. attribute:: permissions

        A list of permissions generated from the attribute *permissions* of
        the associated :term:`groups <group>`. It assumes that the mixed
        class implements a *groups* attribute.


Configuration
=============

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
