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
* ARGUS_FRONTEND_URL, for redirecting back to frontend after logging in through Feide, and also CORS
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
* `GET` to `/api/v1/auth/users/<int:pk>/`: returns a user by pk
* `POST` to `/oidc/api-token-auth/`: returns an auth token for the posted user
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
      "user": 1,
      "phone_number": "+4767676767"
    }
    ```
    </details>
* `/api/v1/auth/phone-number/<int:pk>`: 
  * `GET`: returns the specific phone number of the logged in user
    <details>
    <summary>Example response body:</summary>
 
    ```json
    {
      "pk": 2,
      "user": 1,
      "phone_number": "+4767676767"
    },
    ```
    </details>
  * `PUT`: updates and returns one of the logged in user's phone numbers by pk
    * Example request body: same as `POST` to `/api/v1/auth/phone-number/`
  * `DELETE`: deletes one of the logged in user's phone numbers by pk
</details>

<details>
<summary>Incident endpoints</summary>

* `/api/v1/incidents/`:
  * `GET`: returns all incidents - both open and historic
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
                "user": 12
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
  * `GET`: returns an incident by pk
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

* `/api/v1/incidents/<int:pk>/events/`:
  * `GET`: returns all events related to the specified incident
    <details>
    <summary>Example response body:</summary>

    ```json
    [
        {
            "pk": 1,
            "incident": 10101,
            "actor": 12,
            "timestamp": "2011-11-11T11:11:11+02:00",
            "type": {
                "value": "STA",
                "display": "Incident start"
            },
            "description": ""
        },
        {
            "pk": 20,
            "incident": 10101,
            "actor": 12,
            "timestamp": "2011-11-11T11:11:12+02:00",
            "type": {
                "value": "END",
                "display": "Incident end"
            },
            "description": ""
        }
    ]
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
                "actor": 140,
                "timestamp": "2011-11-11T11:11:11.235877+02:00",
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
                "actor": 130,
                "timestamp": "2011-11-12T11:11:11+02:00",
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
    </details>

* `GET` to `/api/v1/incidents/<int:pk>/acks/<int:pk>/`: returns a specific acknowledgement of the specified incident

* `GET` to `/api/v1/incidents/open/`: returns all open incidents that have not been acked
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
    </details>

* `/api/v1/notificationprofiles/<int:pk>/`:
  * `GET`: returns one of the logged in user's notification profiles by pk
  * `PUT`: updates and returns one of the logged in user's notification profiles by pk
    * Example request body: same as `POST` to `/api/v1/notificationprofiles/`
  * `DELETE`: deletes one of the logged in user's notification profiles by pk

* `GET` to `/api/v1/notificationprofiles/<int:pk>/incidents/`: returns all incidents - both open and historic - filtered by one of the logged in user's notification profiles by pk

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
        "name": "Immediately",
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
        "name": "Immediately",
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
  * `GET`: returns one of the logged in user's time slots by pk
  * `PUT`: updates and returns one of the logged in user's time slots by pk
    * Example request body: same as `POST` to `/notificationprofiles/timeslots/`
  * `DELETE`: deletes one of the logged in user's time slots by pk

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
  * `GET`: returns one of the logged in user's filters by pk
  * `PUT`: updates and returns one of the logged in user's filters by pk
    * Example request body: same as `POST` to `/api/v1/notificationprofiles/filters/`
  * `DELETE`: deletes one of the logged in user's filters by pk

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
