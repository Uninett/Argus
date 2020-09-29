# Argus
[![build badge](https://github.com/Uninett/Argus/workflows/build/badge.svg)](https://github.com/Uninett/Argus/actions)
[![codecov badge](https://codecov.io/gh/Uninett/Argus/branch/master/graph/badge.svg)](https://codecov.io/gh/Uninett/Argus)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Argus is a platform for aggregating incidents across network management systems, and sending notifications to users. Users build notification profiles that define which incidents they subscribe to.

This repository hosts the backend built with Django, while the frontend is hosted here: https://github.com/Uninett/Argus-frontend.


## Setup

### Prerequisites
* Python 3.6+
* pip

### Dataporten setup
* Register a new application with the following redirect URL: `{server_url}/oidc/complete/dataporten_feide/`
  * `{server_url}` must be replaced with the URL to the server running this project, like `http://localhost:8000`
* Add the following permission scopes:
  * `profile`
  * `userid`
  * `userid-feide`

### Project setup
* Create a Python 3.6+ virtual environment
* `pip install -r requirements.txt`
* `python manage.py migrate`

Start the server with `python manage.py runserver`.

### Site- and deployment-specific settings

Site-specific settings are set as per 12 factor, with environment variables. For more details, see the relevant section in the docs: [Setting site-specific settings](https://argus.readthedocs.io/en/latest/site-specific-settings.html).

A recap of the environment variables that can be set by default follows.

#### Environment variables

* ARGUS_DATAPORTEN_KEY, which holds the id/key for using dataporten for
  authentication.
* ARGUS_DATAPORTEN_SECRET, which holds the password for using dataporten for
  authentication.
* ARGUS_COOKIE_DOMAIN, the domain the cookie is set for
* ARGUS_FRONTEND_URL, for redirecting back to frontend after logging in through
  Feide, and also CORS. Must either be a subdomain of or the same as
  ARGUS_COOKIE_DOMAIN
* ARGUS_SEND_NOTIFICATIONS, True in production and False by default, to allow supressing notifications
* DEBUG, 1 for True, 0 for False
* TEMPLATE_DEBUG. By default set to the same as DEBUG.
* DEFAULT_FROM_EMAIL, the email From-address used for notifications sent via email
* EMAIL_HOST, smarthost (domain name) to send email through
* EMAIL_HOST_USER, (optional) if the host in EMAIL_HOST needs authentication
* EMAIL_HOST_PASSWORD, (optional) password if the smarthost needs that
* EMAIL_PORT, in production by default set to 587
* SECRET_KEY, used internally by django, should be about 50 chars of ascii
  noise (but avoid backspaces!)

There are also settings (not env-variables) for which notification plugins to use:

DEFAULT_SMS_MEDIA, which by default is unset, since there is no standardized
way of sending SMSes. See **Notifications and notification plugins**.

DEFAULT_EMAIL_MEDIA, which is included and uses Django's email backend. It is
better to switch out the email backend than replcaing this plugin.

*A Gmail account with "Allow less secure apps" turned on, was used in the development of this project.*

### Production gotchas

The frontend and backend currently needs to be on either the same domain or be
subdomains of the same domain (ARGUS_COOKIE_DOMAIN).

When running on localhost for dev and test, ARGUS_COOKIE_DOMAIN may be empty.

### Running tests
* `python manage.py test src`


### Mock data
##### Generating
```sh
PYTHONPATH=src python src/argus/incident/fixtures/generate_fixtures.py
```
This creates the file `src/argus/incident/fixtures/incident/mock_data.json`.

##### Loading
```sh
python manage.py loaddata incident/mock_data
```

### Running in development

The fastest is to use virtualenv or virtaulenvwrapper or similar to create
a safe place to stash all the dependencies.

1. Create the virtualenv
2. Fill the activated virtualenv with dependencies:

```
$ pip install -r requirements/prod.txt
$ pip install -r requirements/dev.txt
```

Copy the `cmd.sh-template` to a new name ending with ".sh", make it executable
and set the environment variables within. This file must not be checked in to
version control, since it contains passwords. You *must* set DATABASE_URL,
DJANGO_SETTINGS_MODULE and SECRET_KEY. If you want to test the frontend you
must also set all the DATAPORTEN-settings. Get the values from
https://dashboard.dataporten.no/ or create a new application there.

For the database we recommend postgres as we use a postgres-specific feature in
the Incident-model.

DJANGO_SETTINGS_MODULE can be set to "argus.site.settings.dev" but we recommend
having a `localsettings.py` in the same directory as `manage.py` with any
overrides. This file also does not belong in version control since it reflects
a specific developer's preferences. Smart things first tested in
a localsettings can be moved to the other settings-files later on. If you copy
the entire logging-setup from "argus.site.settings.dev" to "localsettings.py"
remember to set "disable_existing_loggers" to True or logentries will occur
twice.

### Debugging tips

To test/debug notifications as a whole, use the email subsystem (Media: Email in a NotificationProfile).
Set EMAIL_HOST to "localhost", EMAIL_PORT to "1025", and run a dummy mailserver:

```
$ python3 -m smtpd -n -c DebuggingServer localhost:1025
```

Notifications sent will then be dumped to the console where the dummy server runs.

## Endpoints
*`/admin/` to access the project's admin pages.*

All endpoints require requests to contain a header with key `Authorization` and value `Token {token}`, where `{token}` is replaced by a registered auth token; these are generated per user by logging in through Feide, and can be found at `/admin/authtoken/token/`.

<details>
<summary>Auth endpoints</summary>

* `GET` to `/api/v1/auth/user/`: returns the logged in user
* `GET` to `/api/v1/auth/users/<int:pk>/`: returns a user by PK
* `POST` to `/oidc/api-token-auth/`: returns an auth token for the posted user
  * Note that this token will expire after 14 days, and can be replaced by posting to the same endpoint.
  * Example request body: `{ username: <username>, password: <password> }`
* `/oidc/login/dataporten_feide/`: redirects to Feide login
* `/api/v1/auth/phone-number/`:
  * `GET`: returns the phone numbers of the logged in user
    <details>
    <summary>Example response body:</summary>

    ```json
    [
      {
        "pk": 2,
        "user": 1,
        "phone_number": "+4767676767"
      },
      {
        "pk": 1,
        "user": 1,
        "phone_number": "+4790909090"
      }
    ]
    ```
    </details>
  * `POST`: creates and returns the phone numbers of the logged in user
    <details>
    <summary>Example request body:</summary>

    ```json
    {
      "pk": 2,
      "phone_number": "+4767676767"
    }
    ```
    </details>
* `/api/v1/auth/phone-number/<int:pk>/`:
  * `GET`: returns the specific phone number of the logged in user
    <details>
    <summary>Example response body:</summary>

    ```json
    {
      "pk": 2,
      "user": 1,
      "phone_number": "+4767676767"
    }
    ```
    </details>
  * `PUT`: updates and returns one of the logged in user's phone numbers by PK
    * Example request body: same as `POST` to `/api/v1/auth/phone-number/`
  * `DELETE`: deletes one of the logged in user's phone numbers by PK

  The phone number is validated with a python version of the Google library
  [libphonenumber](https://github.com/google/libphonenumber). It *will* check
  that the number is in a valid number series. Using a random number
  with enough digits that is not in a valid series will *not* work.
</details>

<details>
<summary>Incident endpoints</summary>

* `/api/v1/incidents/`:
  * `GET`: returns all incidents - both open and historic
    <details>
    <summary>Query parameters:</summary>
    All query parameters are optional. If a query parameter is not included or
    empty, for instance `acked=`, then the rows returned are not affected by
    that filter and shows rows of all kinds of that value, for instance both
    "acked" and "unacked" in the case of `acked=`.

    <dl>
    <dt>acked=true|false</dt>
    <dd>Fetch only acked (true) or unacked (false) incidents.</dd>
    <dt>open=true|false</dt>
    <dd>Fetch only open (true) or closed (false) incidents.</dd>
    <dt>stateful=true|false</dt>
    <dd>Fetch only stateful (true) or stateless (false) incidents.</dd>
    <dt>source__id__in=ID1[,ID2,..]</dt>
    <dd>Fetch only incidents with a source with numeric id ID1 or ID2 or..
    <dt>source__name__in=NAME1[,NAME2,..]</dt>
    <dd>Fetch only incidents with a source with name NAME1 or NAME2 or..
    <dt>source_incident_id=ID</dt>
    <dd>Fetch only incidents with source_incident_id set to ID.</dd>
    <dt>tags=key1=value1,key1=value2,key2=value</dt>
    <dd>Fetch only incidents with one or more of the tags. Tag-format is
    "key=value". If there are multiple tags with the same key, only one of the
    tags need match. If there are multiple keys, one of each key must match.</dd>
    </dl>

    So: `/api/v1/incidents/?acked=false&open=true&stateful&true&source__id__in=1&tags=location=broomcloset,location=understairs,problem=onfire` will fetch incidents that are all of "open", "unacked", "stateful", from source number 1, with "location" either "broomcloset" or "understairs", and that is on fire (problem=onfire).
    </details>
    <details>
    <summary>Example response body:</summary>

    ```json
    [
        {
            "pk": 10101,
            "start_time": "2011-11-11T11:11:11+02:00",
            "end_time": "2011-11-11T11:11:12+02:00",
            "source": {
                "pk": 11,
                "name": "Uninett GW 3",
                "type": {
                    "name": "nav"
                },
                "user": 12,
                "base_url": "https://somenav.somewhere.com"
            },
            "source_incident_id": "12345",
            "details_url": "https://uninett.no/api/alerts/12345/",
            "description": "Netbox 11 <12345> down.",
            "ticket_url": "https://tickettracker.com/tickets/987654/",
            "tags": [
                {
                    "added_by": 12,
                    "added_time": "2011-11-11T11:11:11.111111+02:00",
                    "tag": "object=Netbox 4"
                },
                {
                    "added_by": 12,
                    "added_time": "2011-11-11T11:11:11.111111+02:00",
                    "tag": "problem_type=boxDown"
                },
                {
                    "added_by": 200,
                    "added_time": "2020-08-10T11:26:14.550951+02:00",
                    "tag": "color=red"
                }
            ],
            "stateful": true,
            "open": false,
            "acked": false
        }
    ]
    ```
    Refer to [this section](#explanation-of-terms) for an explanation of the fields.
    </details>
  * `POST`: creates and returns an incident
    <details>
    <summary>Example request body:</summary>

    ```json
    {
        "source": 11,
        "start_time": "2011-11-11 11:11:11.11111",
        "end_time": null,
        "source_incident_id": "12345",
        "details_url": "https://uninett.no/api/alerts/12345/",
        "description": "Netbox 11 <12345> down.",
        "ticket_url": "https://tickettracker.com/tickets/987654/",
        "tags": [
            {"tag": "object=Netbox 4"},
            {"tag": "problem_type=boxDown"}
        ]
    }
    ```
    Refer to [this section](#explanation-of-terms) for an explanation of the fields.
    </details>

* `/api/v1/incidents/<int:pk>/`:
  * `GET`: returns an incident by PK
  * `PATCH`: modifies parts of an incident and returns it
    <details>
    <summary>Example request body:</summary>

    ```json
    {
        "ticket_url": "https://tickettracker.com/tickets/987654/",
        "tags": [
            {"tag": "object=Netbox 4"},
            {"tag": "problem_type=boxDown"}
        ]
    }
    ```

    The fields allowed to be modified are:
    * `details_url`
    * `ticket_url`
    * `tags`
    </details>

* `/api/v1/incidents/<int:pk>/ticket_url/`:
  * `PUT`: modifies just the ticket url of an incident and returns it
    <details>
    <summary>Example request body:</summary>

    ```json
    {
        "ticket_url": "https://tickettracker.com/tickets/987654/",
    }
    ```

    Only `ticket_url` may be modified.
    </details>

* `/api/v1/incidents/<int:pk>/events/`:
  * `GET`: returns all events related to the specified incident
    <details>
    <summary>Example response body:</summary>

    ```json
    [
        {
            "pk": 1,
            "incident": 10101,
            "actor": {
                "pk": 12,
                "username": "nav.oslo.uninett.no"
            },
            "timestamp": "2011-11-11T11:11:11+02:00",
            "received": "2011-11-11T11:12:11+02:00",
            "type": {
                "value": "STA",
                "display": "Incident start"
            },
            "description": ""
        },
        {
            "pk": 20,
            "incident": 10101,
            "actor": {
                "pk": 12,
                "username": "nav.oslo.uninett.no"
            },
            "timestamp": "2011-11-11T11:11:12+02:00",
            "received": "2011-11-11T11:11:13+02:00",
            "type": {
                "value": "END",
                "display": "Incident end"
            },
            "description": ""
        }
    ]

    Note that `received` is set by argus on reception of an event. Normally,
    this should be the same as, or a little later, than `timestamp`. If there
    is a large gap (in minutes), or `received` is earlier `timestamp`, it
    is likely something wrong with the internal clock either on the argus
    server or the event source.

    ```
  * `POST`: creates and returns an event related to the specified incident
    <details>
    <summary>Example request body:</summary>

    ```json
    {
        "timestamp": "2020-02-20 20:02:20.202021",
        "type": "OTH",
        "description": "The investigation is still ongoing."
    }
    ```

    If posted by an end user (a user with no associated source system), the `timestamp` field is optional, and will be set to the time the server received it if omitted.

    The valid `type`s are:
    * `STA` - Incident start
      * An incident automatically creates an event of this type when the incident is created, but cannot have more than one. In other words, it's never allowed to post an event of this type.
    * `END` - Incident end
      * Only source systems can post an event of this type, which is the standard way of closing an indicent. An incident cannot have more than one event of this type.
    * `CLO` - Close
      * Only end users can post an event of this type, which manually closes the incident.
    * `REO` - Reopen
      * Only end users can post an event of this type, which reopens the incident if it's been closed (either manually or by a source system).
    * `ACK` - Acknowledge
      * Use the `/api/v1/incidents/<int:pk>/acks/` endpoint.
    * `OTH` - Other
      * Any other type of event, which simply provides information on something that happened related to an incident, without changing its state in any way.
    </details>

* `GET` to `/api/v1/incidents/<int:pk>/events/<int:pk>/`: returns a specific event related to the specified incident

* `/api/v1/incidents/<int:pk>/acks/`:
  * `GET`: returns all acknowledgements of the specified incident
    <details>
    <summary>Example response body:</summary>

    ```json
    [
        {
            "pk": 2,
            "event": {
                "pk": 2,
                "incident": 10101,
                "actor": {
                    "pk": 140,
                    "username": "jp@example.org"
                },
                "timestamp": "2011-11-11T11:11:11.235877+02:00",
                received": "2011-11-11T11:11:11.235897+02:00",
                "type": {
                    "value": "ACK",
                    "display": "Acknowledge"
                },
                "description": "The incident is being investigated."
            },
            "expiration": "2011-11-13T12:00:00+02:00"
        },
        {
            "pk": 20,
            "event": {
                "pk": 20,
                "incident": 10101,
                "actor": {
                    "pk": 130,
                    "username": "ferrari.testarossa@example.com"
                },
                "timestamp": "2011-11-12T11:11:11+02:00",
                "received": "2011-11-12T11:11:11+02:00",
                "type": {
                    "value": "ACK",
                    "display": "Acknowledge"
                },
                "description": "The situation is under control!"
            },
            "expiration": null
        }
    ]
    ```
  * `POST`: creates and returns an acknowledgement of the specified incident
    <details>
    <summary>Example request body:</summary>

    ```json
    {
        "event": {
            "timestamp": "2011-11-11 11:11:11.235877",
            "description": "The incident is being investigated."
        },
        "expiration": "2011-11-13 12:00:00"
    }
    ```

    Only end users can post acknowledgements.

    The `timestamp` field is optional, and will be set to the time the server received it if omitted.
    </details>

* `GET` to `/api/v1/incidents/<int:pk>/acks/<int:pk>/`: returns a specific acknowledgement of the specified incident

* `GET` to `/api/v1/incidents/mine/`: behaves like `/api/v1/incidents/` except
  only showing the incidents added by the logged-in user, and no filtering on
  source or source type is possible.
* `GET` to `/api/v1/incidents/open/`: returns all open incidents
* `GET` to `/api/v1/incidents/open+unacked/`: returns all open incidents that have not been acked
* `GET` to `/api/v1/incidents/metadata/`: returns relevant metadata for all incidents

</details>

<details>
<summary>Notification profile endpoints</summary>

* `/api/v1/notificationprofiles/`:
  * `GET`: returns the logged in user's notification profiles
  * `POST`: creates and returns a notification profile which is then connected to the logged in user
    <details>
    <summary>Example request body:</summary>

    ```json
    {
        "timeslot": 1,
        "filters": [
            1,
            2
        ],
        "media": [
            "EM",
            "SM"
        ],
        "phone_number": 1,
        "active": true
    }
    ```

    The phone number field is optional and may also be null.
    </details>

* `/api/v1/notificationprofiles/<int:pk>/`:
  * `GET`: returns one of the logged in user's notification profiles by PK
  * `PUT`: updates and returns one of the logged in user's notification profiles by PK
    * Note that if `timeslot` is changed, the notification profile's PK will also change. This consequently means that the URL containing the previous PK will return a `404 Not Found` status code.
    * Example request body: same as `POST` to `/api/v1/notificationprofiles/`
  * `DELETE`: deletes one of the logged in user's notification profiles by PK

* `GET` to `/api/v1/notificationprofiles/<int:pk>/incidents/`: returns all incidents - both open and historic - filtered by one of the logged in user's notification profiles by PK

* `/api/v1/notificationprofiles/timeslots/`:
  * `GET`: returns the logged in user's time slots
  * `POST`: creates and returns a time slot which is then connected to the logged in user
    <details>
    <summary>Example request body:</summary>

    ```json
    {
        "name": "Weekdays",
        "time_recurrences": [
            {
                "days": [1, 2, 3, 4, 5],
                "start": "08:00:00",
                "end": "12:00:00"
            },
            {
                "days": [1, 2, 3, 4, 5],
                "start": "12:30:00",
                "end": "16:00:00"
            }
        ]
    }
    ```

    The optional key `"all_day"` indicates that Argus should use `Time.min` and `Time.max` as `"start"` and `"end"` respectively. This also overrides any provided values for `"start"` and `"end"`. An example request body:
    ```json
    {
        "name": "All the time",
        "time_recurrences": [
            {
                "days": [1, 2, 3, 4, 5, 6, 7],
                "all_day": true
            }
        ]
    }
    ```
    which would yield the response:
    ```json
    {
        "pk": 2,
        "name": "All the time",
        "time_recurrences": [
            {
                "days": [1, 2, 3, 4, 5, 6, 7],
                "start": "00:00:00",
                "end": "23:59:59.999999",
                "all_day": true
            }
        ]
    }
    ```
    </details>

* `/api/v1/notificationprofiles/timeslots/<int:pk>/`:
  * `GET`: returns one of the logged in user's time slots by PK
  * `PUT`: updates and returns one of the logged in user's time slots by PK
    * Example request body: same as `POST` to `/notificationprofiles/timeslots/`
  * `DELETE`: deletes one of the logged in user's time slots by PK

* `/api/v1/notificationprofiles/filters/`:
  * `GET`: returns the logged in user's filters
  * `POST`: creates and returns a filter which is then connected to the logged in user
    <details>
    <summary>Example request body:</summary>

    ```json
    {
        "name": "Critical incidents",
        "filter_string": "{\"sourceSystemIds\": [<SourceSystem.pk>, ...], \"tags\": [\"key1=value1\", ...]}"
    }
    ```
    </details>

* `/api/v1/notificationprofiles/filters/<int:pk>/`:
  * `GET`: returns one of the logged in user's filters by PK
  * `PUT`: updates and returns one of the logged in user's filters by PK
    * Example request body: same as `POST` to `/api/v1/notificationprofiles/filters/`
  * `DELETE`: deletes one of the logged in user's filters by PK

* `POST` to `/api/v1/notificationprofiles/filterpreview/`: returns all incidents - both open and historic - filtered by the values in the body
  <details>
  <summary>Example request body:</summary>

  ```json
  {
      "sourceSystemIds": [<SourceSystem.pk>, ...]
  }
  ```
  </details>

</details>


## Models

### Explanation of terms
* `incident`: an unplanned interruption in the source system.
* `event`: something that happened related to an incident.
* `acknowledgement`: an acknowledgement of an incident by a user, which hides the incident from the other open incidents.
  * If `expiration` is an instance of `datetime`, the incident will be shown again after the expiration time.
  * If `expiration` is `null`, the acknowledgement will never expire.
  * An incident is considered "acked" if it has one or more acknowledgements that have not expired.
* `start_time`: the time the `incident` was created.
* `end_time`: the time the `incident` was resolved or closed.
  * If `null`: the incident is stateless.
  * If `"infinity"`: the incident is stateful, but has not yet been resolved or closed - i.e. open.
  * If an instance of `datetime`: the incident is stateful, and was resolved or closed at the given time; if it's in the future, the incident is also considered open.
* `source`: the source system that the `incident` originated in.
* `object`: the most specific object that the `incident` is about.
* `parent_object`: an object that the `object` is possibly a part of.
* `problem_type`: the type of problem that the `incident` is about.
* `tag`: a key-value pair separated by an equality sign (=), in the shape of a string.
  * The key can consist of lowercase letters, numbers and underscores.
  * The value can consist of any length of any characters.

### ER diagram
![ER diagram](img/ER_model.png)

## Notifications and notification plugins

A notification plugin is a class that inherits from `argus.notificationprofile.media.base.NotificationMedium`. It has a `send(incident, user, **kwargs)` static method that does the actual sending.

The included `argus.notificationprofile.media.email.EmailNotification` needs only `incident` and `user`, while an SMS medium in addition needs a `phone_number`. A `phone_number` is a string that includes the international calling code, see for instance [Wikipedia: List of mobile telephone prefixes by country](https://en.wikipedia.org/wiki/List_of_mobile_telephone_prefixes_by_country).
