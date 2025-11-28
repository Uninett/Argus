Preferences are all now properly backed by forms, inheriting from
`SimplePreferenceForm` which is a perfect fit for preferences where you choose
one of several options. Using `PreferenceField` directly will still work, but
the form used now receives the request on `__init__`. It is therefore necessary
to upgrade the old forms by either mixing in the `ClassicPreferenceFormMixin`,
which will discard the passed-in `request`, or writing your own `__init__` that
will prevent passing in the `request` via `super().__init__(*args, **kwargs)`.
