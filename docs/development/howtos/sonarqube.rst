=======================
Howto: Handle sonarqube
=======================

We use `sonarqube`_ to scan new code for potential issues and security hotspots.
It posts comments on pull requests when it finds new issues in that code using rules
defined by the developer team at Sikt.

But we sometimes also disagree with how it handles parts of certain rules. We will
document that here and which comment to use when marking such an issue as accepted or
false positive.

python:S1192 - String literals should not be duplicated
-------------------------------------------------------

If it makes it more readable, for example if configuration is happening within the
Python code, then we accept it with "This is better for readability".

python:S2208 - Wildcard imports should not be used
--------------------------------------------------

This is okay in settings files. Mark as false positive with "Django standard
practice for settings files". Notice that `sonarqube`_ ignores all ``#noqa``
so "#noqa: `F401`_, `F403`_" won't help.

.. _sonarqube: https://www.sonarsource.com/products/sonarcloud/
.. _F401: https://www.flake8rules.com/rules/F401.html
.. _F403: https://www.flake8rules.com/rules/F403.html
