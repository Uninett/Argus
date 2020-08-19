import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from string import ascii_lowercase, ascii_uppercase, digits
from typing import List, Tuple

import django
from django.core import serializers
from django.db.models import Model
from django.utils import timezone

FIXTURES_DIR = Path(__file__).resolve().parent
ROOT_DIR = FIXTURES_DIR.parent.parent.parent.parent
INCIDENT_FIXTURES_FILE = FIXTURES_DIR / "incident" / "mock_data.json"

# Must be called before any models are imported, to be able to use them
sys.path.append(ROOT_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "argus.site.settings.dev")
django.setup()

from argus.incident.models import *


# --- Generation configuration ---
START_PK = 1
MAX_ID = 999_999
WORD_LENGTH_RANGE = (2, 10)
MIN_TIMESTAMP = timezone.get_current_timezone().localize(datetime(2000, 1, 1))
# SourceSystem:
NUM_SOURCE_SYSTEMS_PER_TYPE = 3
# Object:
NUM_OBJECTS = 50
OBJECT_NAME_WORD_COUNT_RANGE = (2, 5)
COMPOSITE_WORD_CHANCE = 1 / 10
WORD_NUMBER_SUFFIX_CHANCE = 1 / 5
# ParentObject:
NUM_PARENT_OBJECTS = 10
PARENT_OBJECT_NAME_WORD_COUNT_RANGE = (1, 2)
# ProblemType:
NUM_PROBLEM_TYPES = 10
PROBLEM_TYPE_NAME_WORD_COUNT_RANGE = (2, 3)
# Incident:
NUM_INCIDENTS = 200
INCIDENT_START_TIME_NOW_CHANCE = 1 / 5
INCIDENT_DESCRIPTION_WORD_COUNT_RANGE = (2, 10)
INCIDENT_STATEFUL_CHANCE = 1 / 2
STATEFUL_INCIDENT_OPEN_CHANCE = 1 / 5
# Event:
EVENT_OTHER_CHANCE = 1 / 5


# --- Util functions ---
def random_int(range_: Tuple[int, int]) -> int:
    return random.randint(*range_)


past_ids = set()


def random_id() -> str:
    id_ = random.randint(1, MAX_ID)
    # Ensure unique IDs (note that this is across models; might want to change to check per model)
    while id_ in past_ids:
        id_ = random.randint(1, MAX_ID)

    past_ids.add(id_)
    return str(id_)


def random_word(word_length_range: Tuple[int, int] = WORD_LENGTH_RANGE) -> str:
    word_length = random_int(word_length_range)
    return "".join(random.choice(ascii_lowercase) for _ in range(word_length))


def random_word_list(word_count_range: Tuple[int, int]) -> List[str]:
    word_count = random_int(word_count_range)
    return [random_word() for _ in range(word_count)]


def random_words(word_count_range: Tuple[int, int]) -> str:
    return " ".join(random_word_list(word_count_range))


def random_description(word_count_range: Tuple[int, int]) -> str:
    description = random_words(word_count_range)
    # Make first letter upper case, and add a period
    return description[0].upper() + description[1:] + "."


def random_timestamp() -> datetime:
    random_time_delta = (timezone.now() - MIN_TIMESTAMP).total_seconds() * random.random()
    return MIN_TIMESTAMP + timedelta(seconds=random_time_delta)


def roll_dice(chance_threshold: float) -> bool:
    return random.random() < chance_threshold


def format_url(source_system: SourceSystem, name: str) -> str:
    return f"http://{source_system.name}.{source_system.type}.no/{name.replace(' ', '%20')}".lower()


def set_pks(model_objects: List[Model]) -> List[Model]:
    pk = START_PK
    for obj in model_objects:
        obj.pk = pk
        pk += 1
    return model_objects


# --- Generation functions ---
def generate_source_system_types() -> List[SourceSystemType]:
    return [SourceSystemType(name="nav"), SourceSystemType(name="zabbix")]


def generate_source_systems(source_system_types) -> Tuple[List[Model], List[Model]]:
    source_systems = []
    source_system_users = []
    for source_type in source_system_types:
        for _ in range(NUM_SOURCE_SYSTEMS_PER_TYPE):
            name = random.choice(ascii_uppercase) + random.choice(digits)
            user = User(username=f"{source_type}.{name}".lower())
            source_systems.append(SourceSystem(name=name, type=source_type, user=user))
            source_system_users.append(user)

    tuples = set_pks(source_systems), set_pks(source_system_users)
    # Reassign user after PKs have been set, to prevent `null` values in the JSON
    for source_system in source_systems:
        source_system.user = source_system.user
    return tuples


def generate_object_names() -> List[str]:
    def random_object_word() -> str:
        # Will most often be an empty string, sometimes a single digit, and rarely a double digit
        suffix = (
            f"{random.choice(digits)}{random.choice(digits) if roll_dice(WORD_NUMBER_SUFFIX_CHANCE) else ''}"
            if roll_dice(WORD_NUMBER_SUFFIX_CHANCE)
            else ""
        )
        return random_word() + suffix

    object_names = []
    for _ in range(NUM_OBJECTS):
        name_words = []
        for _ in range(random_int(OBJECT_NAME_WORD_COUNT_RANGE)):
            if roll_dice(COMPOSITE_WORD_CHANCE):
                # Will be a word-like-this
                word = "-".join(random_object_word() for _ in range(random_int(OBJECT_NAME_WORD_COUNT_RANGE)))
            else:
                word = random_object_word().title()
            name_words.append(word)
        object_names.append(" ".join(name_words))

    return object_names


def generate_parent_object_names() -> List[str]:
    return [random_words(PARENT_OBJECT_NAME_WORD_COUNT_RANGE).title() for _ in range(NUM_PARENT_OBJECTS)]


def generate_problem_type_names() -> List[str]:
    problem_type_names = []
    for _ in range(NUM_PROBLEM_TYPES):
        name = "".join(w.title() for w in random_word_list(PROBLEM_TYPE_NAME_WORD_COUNT_RANGE))
        # Make first letter lower case
        name = name[0].lower() + name[1:]
        problem_type_names.append(name)

    return problem_type_names


# FIXME: hacky solution that relies purely on the fact that
#  Django's `serializers.serialize()` calls `isoformat()` when serializing
class InfinityDatetime:
    def isoformat(self):
        return INFINITY_REPR


def generate_incidents(source_systems) -> List[Model]:
    second_delay = timedelta(seconds=1)

    incidents = []
    for i in range(NUM_INCIDENTS):
        start_time_now = roll_dice(INCIDENT_START_TIME_NOW_CHANCE)
        if start_time_now:
            # Ensures a small delay between each incident with a "now" timestamp
            start_time = timezone.now() - i * second_delay
        else:
            start_time = random_timestamp()

        source_system = random.choice(source_systems)
        source_incident_id = random_id()

        if roll_dice(INCIDENT_STATEFUL_CHANCE):
            if roll_dice(STATEFUL_INCIDENT_OPEN_CHANCE):
                end_time = InfinityDatetime()
            elif start_time_now:
                end_time = start_time + second_delay
            else:
                random_timedelta = abs(random_timestamp() - start_time)
                end_time = start_time + random_timedelta
        else:
            end_time = None

        incidents.append(
            Incident(
                start_time=start_time,
                end_time=end_time,
                source=source_system,
                source_incident_id=source_incident_id,
                details_url=format_url(source_system, source_incident_id),
                description=random_description(INCIDENT_DESCRIPTION_WORD_COUNT_RANGE),
            )
        )

    return set_pks(incidents)


def generate_tags_and_relations(
    incidents, object_names, parent_object_names, problem_type_names
) -> Tuple[List[Model], List[Model]]:
    def create_tag_relation_from_random_choice(collection, incident_):
        return IncidentTagRelation(
            tag=random.choice(collection),
            incident=incident_,
            added_by=incident_.source.user,
            added_time=incident_.start_time,
        )

    object_tags = [Tag(key="object", value=name) for name in object_names]
    parent_object_tags = [Tag(key="parent_object", value=name) for name in parent_object_names]
    problem_type_tags = [Tag(key="problem_type", value=name) for name in problem_type_names]
    tags = set_pks(object_tags + parent_object_tags + problem_type_tags)

    tag_relations = []
    for incident in incidents:
        tag_relations.append(create_tag_relation_from_random_choice(object_tags, incident))
        tag_relations.append(create_tag_relation_from_random_choice(parent_object_tags, incident))
        tag_relations.append(create_tag_relation_from_random_choice(problem_type_tags, incident))

    return tags, set_pks(tag_relations)


def generate_events(incidents) -> List[Model]:
    def end_time_is_in_the_future(incident_: Incident):
        if not incident_.stateful:
            return False
        return isinstance(incident_.end_time, InfinityDatetime) or incident_.open

    events = []
    for incident in incidents:
        events.append(
            Event(
                incident=incident,
                actor=incident.source.user,
                timestamp=incident.start_time,
                type=Event.Type.INCIDENT_START,
            )
        )
        if incident.stateful and not end_time_is_in_the_future(incident):
            events.append(
                Event(
                    incident=incident,
                    actor=incident.source.user,
                    timestamp=incident.end_time,
                    type=Event.Type.INCIDENT_END,
                )
            )
        if roll_dice(EVENT_OTHER_CHANCE):
            if not incident.stateful or end_time_is_in_the_future(incident):
                random_timedelta = (timezone.now() - incident.start_time) * random.random()
            else:
                random_timedelta = (incident.end_time - incident.start_time) * random.random()
            events.append(
                Event(
                    incident=incident,
                    actor=incident.source.user,
                    timestamp=incident.start_time + random_timedelta,
                    type=Event.Type.OTHER,
                    description=f"Info: {random_description(INCIDENT_DESCRIPTION_WORD_COUNT_RANGE)}",
                )
            )

    return set_pks(events)


def create_fixture_file(file_path=INCIDENT_FIXTURES_FILE):
    source_system_types = generate_source_system_types()
    source_systems, source_system_users = generate_source_systems(source_system_types)
    object_names = generate_object_names()
    parent_object_names = generate_parent_object_names()
    problem_type_names = generate_problem_type_names()
    incidents = generate_incidents(source_systems)
    tags, tag_relations = generate_tags_and_relations(incidents, object_names, parent_object_names, problem_type_names)
    events = generate_events(incidents)

    all_objects = (
        *source_system_types,
        *source_system_users,
        *source_systems,
        *incidents,
        *tags,
        *tag_relations,
        *events,
    )

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w") as f:
        serializers.serialize("json", all_objects, stream=f)


if __name__ == "__main__":
    create_fixture_file()
