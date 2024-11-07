from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
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
        ss = SourceSystemFactory(user=user)
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

        incident = StatelessIncidentFactory(source=source)
        self.assertTrue(user.is_used())

    def test_is_not_dormant_if_actor_of_event(self):
        source_user = SourceUserFactory()
        source = SourceSystemFactory(user=source_user)
        incident = StatelessIncidentFactory(source=source)

        user = PersonUserFactory()
        incident.create_ack(user)
        self.assertTrue(user.is_used())


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

    def test_vanilla_get_context_dumps_preferences_field(self):
        user = PersonUserFactory()

        Preferences.ensure_for_user(user)
        pref_set = user.get_preferences(namespace=MyPreferences._namespace)
        preferences = {"a": 1}
        pref_set.preferences = preferences
        pref_set.save()
        self.assertEqual(pref_set.get_context(), pref_set.preferences)

    def test_overriden_get_context_dumps_preferences_field_and_more(self):
        user = PersonUserFactory()

        Preferences.ensure_for_user(user)
        pref_set = user.get_preferences(namespace=MyOtherPreferences._namespace)
        preferences = {"a": 1}
        pref_set.preferences = preferences
        pref_set.save()
        result = pref_set.get_context()
        self.assertEqual(pref_set.preferences["a"], result["a"])
        # hardcoded in class
        self.assertEqual(result["jazzpunk"], "For Great Justice!")

    def test_update_context_overrides_preference(self):
        user = PersonUserFactory()

        Preferences.ensure_for_user(user)
        pref_set = user.get_preferences(namespace=MyOtherPreferences._namespace)
        preferences = {"foobar": "gurba"}
        pref_set.preferences = preferences
        pref_set.save()
        result = pref_set.get_context()
        # hardcoded in class
        self.assertNotEqual(result["foobar"], "gurba")
        self.assertEqual(result["foobar"], "xux")

    def test_save_preference_saves_named_preference(self):
        user = PersonUserFactory()

        Preferences.ensure_for_user(user)
        pref_set = user.get_preferences(namespace=MyPreferences._namespace)

        self.assertFalse(pref_set.preferences)  # no prefs set
        pref_set.save_preference("filifjonka", "gubbelur")
        self.assertEqual(pref_set.preferences["filifjonka"], "gubbelur")

    def test_define_specific_preferences_via_forms_to_validate(self):
        user = PersonUserFactory()
        Preferences.ensure_for_user(user)

        pref_set1 = user.get_preferences(namespace=MyPreferences._namespace)
        Form1 = pref_set1.FORMS["magic_number"]
        pref_dict1 = {"foo": "bar", "magic_number": 2}
        query_dict1 = QueryDict("", mutable=True)
        query_dict1.update(pref_dict1)
        form1 = Form1(query_dict1)
        self.assertTrue(form1.is_valid())
        self.assertNotIn("foo", form1.cleaned_data)
        self.assertEqual(form1.cleaned_data["magic_number"], pref_dict1["magic_number"])

        pref_set2 = user.get_preferences(namespace=MyOtherPreferences._namespace)
        Form2 = pref_set2.FORMS["magic_number"]
        pref_dict2 = {"foo": "bar", "magic_number": 3}
        query_dict2 = QueryDict("", mutable=True)
        query_dict2.update(pref_dict2)
        form2 = Form2(query_dict2)
        self.assertTrue(form2.is_valid())
        self.assertNotIn("foo", form2.cleaned_data)
        self.assertEqual(form2.cleaned_data["magic_number"], pref_dict2["magic_number"])

        self.assertNotEqual(form1.cleaned_data, form2.cleaned_data)


class PreferencesManagerTests(TestCase):
    def test_get_by_natural_key_fetches_preference_of_correct_namespace(self):
        user = PersonUserFactory()

        Preferences.ensure_for_user(user)
        prefs = user.get_preferences(MyPreferences._namespace)
        result = Preferences.objects.get_by_natural_key(user, MyPreferences._namespace)
        self.assertEqual(prefs, result)

    def test_create_missing_preferences_creates_all_namespaces_for_all_users(self):
        user1 = PersonUserFactory()
        user2 = PersonUserFactory()

        # no preferences yet
        self.assertFalse(Preferences.objects.filter(user=user1).exists())
        self.assertFalse(Preferences.objects.filter(user=user2).exists())

        Preferences.objects.create_missing_preferences()
        # two each
        self.assertEqual(Preferences.objects.filter(user=user1).count(), 2)
        self.assertEqual(Preferences.objects.filter(user=user2).count(), 2)
