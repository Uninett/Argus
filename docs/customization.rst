.. _customization:

=================
Customizing Argus
=================

Beyond :ref:`integrations with sources, ticket systems and notification
systems <integrations>` Argus can be customized further.

The entries here are for customizations that take much more effort than
installing some libraries and changing some settings.

Authentication with OAuth2
==========================

You can add your own OAuth2 providers, and more than one if necessary. While
there are many providers already included with the OAuth2 library we are using,
we had to write our own.

See :ref:`authentication-reference` for reference.

Filtering system
================

The filtering subsystem is replaceable.

See :ref:`howto-customize-filtering`

HTMx frontend
=============

The HTMx frontend is designed to be very customizable.

See :ref:`customize-htmx-frontend`

.. toctree::
   :glob:

   customization/*
