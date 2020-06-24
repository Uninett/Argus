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
ALERT_FIXTURES_FILE = FIXTURES_DIR / "alert" / "mock_data.json"

# Must be called before any models are imported, to be able to use them
sys.path.append(ROOT_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "argus.site.settings.dev")
django.setup()

from argus.alert.models import *


# --- Generation configuration ---
START_PK = 1
MAX_ID = 999_999
WORD_LENGTH_RANGE = (2, 10)
MIN_TIMESTAMP = timezone.get_current_timezone().localize(datetime(2000, 1, 1))
# AlertSource:
NUM_ALERT_SOURCES_PER_TYPE = 3
# ObjectType:
NUM_OBJECT_TYPES = 10
OBJECT_TYPE_NAME_LENGTH_RANGE = (3, 7)
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
PROBLEM_TYPE_DESCRIPTION_WORD_COUNT_RANGE = (5, 20)
# Alert:
NUM_ALERTS = 200
ALERT_TIMESTAMP_NOW_CHANCE = 1 / 3
ALERT_DESCRIPTION_WORD_COUNT_RANGE = (2, 10)
# ActiveAlert
ALERT_ACTIVE_CHANCE = 1 / 20


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
    random_time_delta = (
        timezone.now() - MIN_TIMESTAMP
    ).total_seconds() * random.random()
    return MIN_TIMESTAMP + timedelta(seconds=random_time_delta)


def roll_dice(chance_threshold: float) -> bool:
    return random.random() < chance_threshold


def format_url(alert_source: AlertSource, name: str) -> str:
    return f"http://{alert_source.name}.{alert_source.type}.no/{name.replace(' ', '%20')}".lower()


def set_pks(model_objects: List[Model]) -> List[Model]:
    pk = START_PK
    for obj in model_objects:
        obj.pk = pk
        pk += 1
    return model_objects


# --- Generation functions ---
def generate_alert_source_types() -> List[AlertSourceType]:
    return [AlertSourceType(name="NAV"), AlertSourceType(name="Zabbix")]


def generate_alert_sources(alert_source_types) -> List[Model]:
    alert_sources = []
    for source_type in alert_source_types:
        for _ in range(NUM_ALERT_SOURCES_PER_TYPE):
            alert_sources.append(
                AlertSource(
                    name=random.choice(ascii_uppercase) + random.choice(digits),
                    type=source_type,
                )
            )

    return set_pks(alert_sources)


def generate_object_types() -> List[Model]:
    object_types = []
    for _ in range(NUM_OBJECT_TYPES):
        object_types.append(
            ObjectType(name=random_word(OBJECT_TYPE_NAME_LENGTH_RANGE).title())
        )

    return set_pks(object_types)


def generate_objects(object_types, alert_sources) -> List[Model]:
    def random_object_word() -> str:
        # Will most often be an empty string, sometimes a single digit, and rarely a double digit
        suffix = (
            (
                random.choice(digits)
                + (
                    random.choice(digits)
                    if roll_dice(WORD_NUMBER_SUFFIX_CHANCE)
                    else ""
                )
            )
            if roll_dice(WORD_NUMBER_SUFFIX_CHANCE)
            else ""
        )
        return random_word() + suffix

    objects = []
    for _ in range(NUM_OBJECTS):

        # Generate name
        name_words = []
        for _ in range(random_int(OBJECT_NAME_WORD_COUNT_RANGE)):
            if roll_dice(COMPOSITE_WORD_CHANCE):
                # Will be a word-like-this
                word = "-".join(
                    random_object_word()
                    for _ in range(random_int(OBJECT_NAME_WORD_COUNT_RANGE))
                )
            else:
                word = random_object_word().title()
            name_words.append(word)
        name = " ".join(name_words)

        alert_source = random.choice(alert_sources)

        objects.append(
            Object(
                name=name,
                object_id=random_id(),
                url=format_url(alert_source, name),
                type=random.choice(object_types),
                alert_source=alert_source,
            )
        )

    return set_pks(objects)


def generate_parent_objects(alert_sources) -> List[Model]:
    parent_objects = []
    for _ in range(NUM_PARENT_OBJECTS):
        alert_source = random.choice(alert_sources)
        name = random_words(PARENT_OBJECT_NAME_WORD_COUNT_RANGE).title()

        parent_objects.append(
            ParentObject(
                name=name,
                parentobject_id=random_id(),
                url=format_url(alert_source, name),
            )
        )

    return set_pks(parent_objects)


def generate_problem_types() -> List[Model]:
    problem_types = []
    for _ in range(NUM_PROBLEM_TYPES):
        name = "".join(
            w.title() for w in random_word_list(PROBLEM_TYPE_NAME_WORD_COUNT_RANGE)
        )
        # Make first letter lower case
        name = name[0].lower() + name[1:]

        description = random_description(PROBLEM_TYPE_DESCRIPTION_WORD_COUNT_RANGE)

        problem_types.append(ProblemType(name=name, description=description))

    return set_pks(problem_types)


def generate_alerts(
    alert_sources, objects, parent_objects, problem_types
) -> List[Model]:
    second_delay = timedelta(seconds=1)

    alerts = []
    for i in range(NUM_ALERTS):
        if roll_dice(ALERT_TIMESTAMP_NOW_CHANCE):
            # Adds a small delay between each alert with a "now" timestamp
            timestamp = timezone.now() + i * second_delay
        else:
            timestamp = random_timestamp()

        alert_source = random.choice(alert_sources)
        alert_id = random_id()

        alerts.append(
            Alert(
                timestamp=timestamp,
                source=alert_source,
                alert_id=alert_id,
                object=random.choice(objects),
                parent_object=random.choice(parent_objects),
                details_url=format_url(alert_source, alert_id),
                problem_type=random.choice(problem_types),
                description=random_description(ALERT_DESCRIPTION_WORD_COUNT_RANGE),
            )
        )

    return set_pks(alerts)


def generate_active_alerts(alerts) -> List[Model]:
    return set_pks(
        [ActiveAlert(alert=alert) for alert in alerts if roll_dice(ALERT_ACTIVE_CHANCE)]
    )


def create_fixture_file():
    alert_source_types = generate_alert_source_types()
    alert_sources = generate_alert_sources(alert_source_types)
    object_types = generate_object_types()
    objects = generate_objects(object_types, alert_sources)
    parent_objects = generate_parent_objects(alert_sources)
    problem_types = generate_problem_types()
    alerts = generate_alerts(alert_sources, objects, parent_objects, problem_types)
    active_alerts = generate_active_alerts(alerts)

    all_objects = (
        *alert_source_types,
        *alert_sources,
        *object_types,
        *objects,
        *parent_objects,
        *problem_types,
        *alerts,
        *active_alerts,
    )

    ALERT_FIXTURES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with ALERT_FIXTURES_FILE.open("w") as f:
        serializers.serialize("json", all_objects, stream=f)


if __name__ == "__main__":
    create_fixture_file()
