============================
How to: Add more preferences
============================

The model ``Preferences`` found in ``argus.auth.models`` stores user
preferences in a namespaced way.

In order to add more preferences:

1. Create a Django app to host the preferences
2. Figure out a unique name for the set of preferences you are making. This is
   the ``namespace``. It must function as a python variable, so must start with
   either an underline (_) or an alphabetic character. If there is only one set
   of preferences for the app you could use the app name.
3. Adapt the below boilerplate::

        from argus.auth.models import preferences, PreferencesBase, PreferenceField

        class MagicNumberForm(forms.Form):
            magic_number = forms.IntegerField()


        @preferences(namespace="mypref")
        class MyPreferences:  # Optionally you can inherit from PreferencesBase
                              # here to get method completion
            FIELDS = {
                "magic_number": PreferenceField(form=MagicNumberForm, default=42),
            }

            # Optional Meta for testing, not needed unless only used for tests
            class Meta:
                app_label = "auth"

   The name of the actual preference (in the example this is "magic_number")
   should also be a valid python variable name.

   There should be one form per preference.

   The app-label line is needed for preference models that only exist for
   tests. Either remove it entirely or make sure the "app_label" is identical
   to the app label of your app when making a "real" preference namespace.
4. The preferences are stored in the database table row in a JSON blob named
   "preferences". The entire blob is copied to the context of all views via the
   context processor ``argus.auth.context_processors.preferences``.

   You can override what is put in context per namespace via overriding the
   method ``update_context()``. By default the former looks like the below
   code::

       def update_context(self, context):
           "Override this to change what is put in context"
            return {}

The preferences are currently not available via the API.
