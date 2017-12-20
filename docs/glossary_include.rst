.. _auth_glossary:

.. glossary::

    actor
        An actor is a person, cronjob or worker that is able to perform an
        :term:`operation`. It can be a member of several :term:`groups <group>`.
        It inherits the :term:`permissions <permission>` from its groups.

    group
        A group is a container for several :term:`permissions <permission>`.
        It can be added to different :term:`actors <actor>`.

    permission
        An :class:`Enum <enum.Enum>` allowing :term:`actors <actor>` of a
        :term:`group` to perform an :term:`operation`. Its job is not to
        implement or execute this :term:`operation`, but to just explain it by
        its definition as concise as possible. A suitable definition for a
        permission could be *open the door* or *write a blog*.

    rule
        A function accepting an object and an :term:`actor` returning whether
        the actor is allowed to perform the :term:`operation` in context of
        the object.

    operation
        A string representing an activity, task or job, e.g. *comment*,
        *edit* or *delete*.

    authentication chain
        When the configured module is requested to determine the currently
        active user, it will need to forward the request to registered
        :class:`Authenticators <.Authenticator>`. Each Authenticator will try
        to figure out the current user in a certain way and ask the next
        Authenticator if it fails to do so, until either one of the
        Authenticators succeeds or there are no more Authenticators to invoke.
