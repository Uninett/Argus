===============
Troubleshooting
===============

Exception complaining about unregistered namespace
==================================================

Check that you are using the correct root urls!

When developing you can run ``python manage.py show_urls`` and grep after the
missing namespace. If it's not there, you're using the wrong root urls.

If you get this problem in tests, remember you can override what root urls the
tests see by
``@override_settings(ROOT_URLCONF="i.want.to.test.these.urls.py")``, replacing
"i.want.to.test.these.urls.py" with whatever urls.py defines the namespace in
question.

Docker file won't build, can't install packages
===============================================

Are you running a VPN? Try turning it off.
