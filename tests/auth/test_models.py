from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import QueryDict

from argus.auth.factories import PersonUserFactory, SourceUserFactory
from argus.auth.models import Preferences
from argus.incident.factories import SourceSystemFactory, StatelessIncidentFactory

from .models import MyPreferences, MyOtherPreferences


User = get_user_model()


class UserTypeTests(TestCase):
    def test_is_end_user(self):
        user = PersonUserFactory()
        self.assertTrue(user.is_end_user)

    def test_is_source_system(self):
        user = SourceUserFactory()
        SourceSystemFactory(user=user)
        self.assertTrue(user.is_source_system)


class UserIsMemberOfGroupTests(TestCase):
    def test_is_member_of_group_when_no_groups_returns_none(self):
        user = PersonUserFactory()
        self.assertEqual(user.is_member_of_group("blbl"), None)

    def test_is_member_of_group_when_group_is_str_succeeds(self):
        user = PersonUserFactory()
        group = Group.objects.create(name="fjoon")
        user.groups.add(group)
        self.assertTrue(user.is_member_of_group(group.name))

    def test_is_member_of_group_when_group_is_group_succeeds(self):
        user = PersonUserFactory()
        group = Group.objects.create(name="brrrr")
        user.groups.add(group)
        self.assertTrue(user.is_member_of_group(group))

    def test_is_member_of_group_when_not_member_of_group_fails(self):
        user = PersonUserFactory()
        group = Group.objects.create(name="foobar")
        self.assertFalse(user.is_member_of_group(group))


class UserIsUsedTests(TestCase):
    def test_is_dormant_if_no_actions_taken(self):
        user = PersonUserFactory()
        self.assertFalse(user.is_used())

    def test_is_not_dormant_if_source_of_incident(self):
        user = SourceUserFactory()
        source = SourceSystemFactory(user=user)

        StatelessIncidentFactory(source=source)
        self.assertTrue(user.is_used())

    def test_is_not_dormant_if_actor_of_event(self):
        source_user = SourceUserFactory()
        source = SourceSystemFactory(user=source_user)
        incident = StatelessIncidentFactory(source=source)

        user = PersonUserFactory()
        incident.create_ack(user)
        self.assertTrue(user.is_used())


class UserMiscMethodTests(TestCase):
    def test_get_preferences_context_returns_dict_of_all_properly_registered_preferences(self):
        user = PersonUserFactory()

        results = user.get_preferences_context()
        self.assertIsInstance(results, dict)
        self.assertEqual(len(results), len(Preferences.NAMESPACES))
        self.assertEqual(results[MyPreferences._namespace]["magic_number"], 42)
        self.assertEqual(results[MyOtherPreferences._namespace]["magic_number"], 5)

    def test_get_preferences_context_does_not_return_unregistered_preferences(self):
        user = PersonUserFactory()

        unregistered_preference = Preferences(
            namespace="foo",
            user=user,
            preferences={
                "evil": "hackerman",
                "waxes": "poetically",
            },
        )
        unregistered_preference.save()
        results = user.get_preferences_context()
        self.assertNotIn("foo", results)


class PreferencesTests(TestCase):
    def test_natural_key_should_return_username_and_namespace(self):
        user = PersonUserFactory()

        Preferences.ensure_for_user(user)
        mypref = MyPreferences.objects.get()
        natural_key = mypref.natural_key()
        self.assertEqual(natural_key, (user, mypref.namespace))

    def test_str_should_return_username_and_namespace(self):
        user = PersonUserFactory()

        Preferences.ensure_for_user(user)
        mypref = MyPreferences.objects.get()
        string = str(mypref)
        self.assertIn(user.username, string)
        self.assertIn(mypref.namespace, string)

    def test_imported_models_autoregister_in_Preferences_NAMESPACES(self):
        namespace1 = MyPreferences._namespace
        self.assertIn(namespace1, Preferences.NAMESPACES)
        self.assertEqual(Preferences.NAMESPACES[namespace1], MyPreferences)

        namespace2 = MyOtherPreferences._namespace
        self.assertIn(namespace2, Preferences.NAMESPACES)
        self.assertEqual(Preferences.NAMESPACES[namespace2], MyOtherPreferences)

    def test_ensure_for_user_creates_all_installed_namespaces_for_user(self):
        user = PersonUserFactory()

        Preferences.ensure_for_user(user)
        self.assertTrue(Preferences.objects.filter(namespace=MyPreferences._namespace))
        self.assertTrue(Preferences.objects.filter(namespace=MyOtherPreferences._namespace))

    def test_get_instance_converts_to_subclass(self):
        user = PersonUserFactory()

        Preferences.ensure_for_user(user)
        instances = Preferences.objects.filter(user=user, namespace=MyPreferences._namespace)
        self.assertEqual(instances.count(), 1)
        instance = instances[0]
        self.assertIsInstance(instance, MyPreferences)

    def test_get_namespaced_preferences_creates_preferences_with_defaults(self):
        user = PersonUserFactory()
        pref_set = user.get_namespaced_preferences(namespace=MyPreferences._namespace)
        self.assertIsInstance(pref_set, MyPreferences)
        self.assertEqual(pref_set.preferences, {"magic_number": 42})

    def test_vanilla_get_context_dumps_preferences_field_including_defaults(self):
        user = PersonUserFactory()

        pref_set = user.get_namespaced_preferences(namespace=MyPreferences._namespace)
        preferences = {"a": 1}
        pref_set.preferences = preferences
        pref_set.save()
        prefs_and_defaults = MyPreferences.get_defaults()
        prefs_and_defaults.update(pref_set.preferences)
        self.assertEqual(pref_set.get_context(), prefs_and_defaults)

    def test_overriden_get_context_dumps_preferences_field_and_more(self):
        user = PersonUserFactory()

        pref_set = user.get_namespaced_preferences(namespace=MyOtherPreferences._namespace)
        preferences = {"a": 1}
        pref_set.preferences = preferences
        pref_set.save()
        result = pref_set.get_context()
        self.assertEqual(pref_set.preferences["a"], result["a"])
        # added via get_context
        self.assertEqual(result["jazzpunk"], "For Great Justice!")

    def test_update_context_overrides_preference(self):
        user = PersonUserFactory()

        pref_set = user.get_namespaced_preferences(namespace=MyOtherPreferences._namespace)
        preferences = {"foobar": "gurba"}
        pref_set.preferences = preferences
        pref_set.save()
        result = pref_set.get_context()
        self.assertNotEqual(result["foobar"], "gurba")
        # overridden via update_context
        self.assertEqual(result["foobar"], "xux")

    def test_get_preference_always_succeeds(self):
        user = PersonUserFactory()

        pref_set = user.get_namespaced_preferences(namespace=MyPreferences._namespace)
        self.assertEqual(pref_set.get_preference("magic_number"), 42)
        self.assertEqual(pref_set.get_preference("unknown_preference"), None)

    def test_save_preference_saves_named_preference(self):
        user = PersonUserFactory()

        pref_set = user.get_namespaced_preferences(namespace=MyPreferences._namespace)

        self.assertTrue(pref_set.preferences)  # default prefs set
        pref_set.save_preference("filifjonka", "gubbelur")
        self.assertEqual(pref_set.preferences["filifjonka"], "gubbelur")

    def test_define_specific_preferences_via_forms_to_validate(self):
        user = PersonUserFactory()

        pref_set1 = user.get_namespaced_preferences(namespace=MyPreferences._namespace)
        Form1 = pref_set1.get_forms()["magic_number"]
        pref_dict1 = {"foo": "bar", "magic_number": 2}
        query_dict1 = QueryDict("", mutable=True)
        query_dict1.update(pref_dict1)
        form1 = Form1(query_dict1)
        self.assertTrue(form1.is_valid())
        self.assertNotIn("foo", form1.cleaned_data)
        self.assertEqual(form1.cleaned_data["magic_number"], pref_dict1["magic_number"])

        pref_set2 = user.get_namespaced_preferences(namespace=MyOtherPreferences._namespace)
        Form2 = pref_set2.get_forms()["magic_number"]
        pref_dict2 = {"foo": "bar", "magic_number": 3}
        query_dict2 = QueryDict("", mutable=True)
        query_dict2.update(pref_dict2)
        form2 = Form2(query_dict2)
        self.assertTrue(form2.is_valid())
        self.assertNotIn("foo", form2.cleaned_data)
        self.assertEqual(form2.cleaned_data["magic_number"], pref_dict2["magic_number"])

        self.assertNotEqual(form1.cleaned_data, form2.cleaned_data)


class PreferencesManagerTests(TestCase):
    def test_all_should_only_return_registered_preferences(self):
        user = PersonUserFactory()
        unregistered_preference = Preferences.objects.create(
            namespace="foo",
            user=user,
            preferences={
                "evil": "hackerman",
                "waxes": "poetically",
            },
        )
        results = Preferences.objects.all()
        self.assertNotIn(unregistered_preference, results)

    def test_get_by_natural_key_fetches_preference_of_correct_namespace(self):
        user = PersonUserFactory()

        prefs = user.get_namespaced_preferences(MyPreferences._namespace)
        result = Preferences.objects.get_by_natural_key(user, MyPreferences._namespace)
        self.assertEqual(prefs, result)

    def test_get_all_defaults_returns_all_prefs_defaults(self):
        defaults = Preferences.objects.get_all_defaults()
        self.assertIsInstance(defaults, dict)
        self.assertEqual(len(defaults), len(Preferences.NAMESPACES))
        self.assertEqual(defaults[MyPreferences._namespace]["magic_number"], 42)
        self.assertEqual(defaults[MyOtherPreferences._namespace]["magic_number"], 5)


class SubclassPreferencesManagerTests(TestCase):
    def test_create_adds_instance_with_correct_namespace(self):
        user = PersonUserFactory()

        obj = MyPreferences.objects.create(user=user)
        self.assertEqual(obj.namespace, MyPreferences._namespace)

    def test_default_queryset_only_includes_own_instances(self):
        user = PersonUserFactory()

        obj1 = MyPreferences.objects.create(user=user)
        obj2 = MyOtherPreferences.objects.create(user=user)

        self.assertIn(obj1, MyPreferences.objects.all())
        self.assertNotIn(obj2, MyPreferences.objects.all())


class UnregisteredPreferencesManagerTests(TestCase):
    def setUp(self):
        user = PersonUserFactory()
        self.unregistered_preference = Preferences.objects.create(
            namespace="foo",
            user=user,
            preferences={
                "evil": "hackerman",
                "waxes": "poetically",
            },
        )

    def test_all_does_not_find_registered_preferences(self):
        results = Preferences.unregistered.all()
        self.assertNotIn(MyPreferences, results)

    def test_all_finds_all_unregistered_preferences(self):
        results = Preferences.unregistered.all()
        self.assertIn(self.unregistered_preference, results)
