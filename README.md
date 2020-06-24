# Argus
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Argus is a platform for aggregating alerts across network management systems, and sending notifications to users. Users build notification profiles that define which alerts they subscribe to.

This repository hosts the backend built with Django, while the frontend is hosted here: https://github.com/Uninett/aas-frontend.


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
* Create the text file `src/aas/site/settings/dataporten_secret.txt` containing the client key to the application

### Project setup
* Create a Python 3.6+ virtual environment
* `pip install -r requirements.txt`
* `python manage.py migrate`

Start the server with `python manage.py runserver`.

### Site- and deployment-specific settings

Site-specific settings are set as per 12 factor, with environment variables. For more details, see the relevant section in the docs: [Setting site-specific settingsi](https://aas.readthedocs.io/en/latest/site-specific-settings.html).

A recap of the environment variables that can be set by default follows.

#### Environment variables

* DEBUG, 1 for True, 0 for False
* TEMPLATE_DEBUG. By default set to the same as DEBUG.
* ARGUS_DATAPORTEN_SECRET, which holds the password for using dataporten for
  authentication.
* ARGUS_FRONTEND_URL, by default "http://localhost:3000", for CORS
* EMAIL_HOST, smarthost (domain name) to send email through
* EMAIL_HOST_PASSWORD, password if the smarthost needs that
* EMAIL_PORT, in production by default set to 587
* SECRET_KEY, used internally by django, should be about 50 chars of ascii
  noise (but avoid backspaces!)

*A Gmail account with "Allow less secure apps" turned on, was used in the development of this project.*

## Endpoints
*`/admin/` to access the project's admin pages.*

All endpoints require requests to contain a header with key `Authorization` and value `Token {token}`, where `{token}` is replaced by a registered auth token; these are generated per user by logging in through Feide, and can be found at `/admin/authtoken/token/`.

<details>
<summary>Auth endpoints</summary>

* `GET` to `/api/v1/auth/user/`: returns the logged in user
* `POST` to `/oidc/api-token-auth/`: returns an auth token for the posted user
  * Body: `{ username: <username>, password: <password> }`
* `/oidc/login/dataporten_feide/`: redirects to Feide login
</details>

<details>
<summary>Alert endpoints</summary>

* `/api/v1/alerts/`:
  * `GET`: returns all alerts - both active and historic
  * `POST`: creates and returns an alert
    <details>
    <summary>Body:</summary>

    Attribute explanation: https://nav.uninett.no/doc/dev/reference/eventengine.html#exporting-alerts-from-nav-into-other-systems
    ```json
    {
        "id": 212310,
        "history": 196179,
        "time": "2019-11-05T10:03:10.235877",
        "message": "box down example-sw.example.org 10.0.1.42",
        "source": "pping",
        "state": "s",
        "on_maintenance": false,
        "netbox": 138,
        "device_groups": null,
        "device": null,
        "subid": "",
        "subject_type": "Netbox",
        "subject": "example-sw.example.org",
        "subject_url": "/api/v1/ipdevinfo/example-sw.example.org/",
        "alert_details_url": "/api/v1/alerts/196179/",
        "netbox_history_url": "/api/v1/devicehistory/history/%3Fnetbox=138",
        "event_history_url": "/api/v1/devicehistory/history/?eventtype=e_boxState",
        "event_type": {
            "description": "Tells us whether a network-unit is down or up.",
            "id": "boxState"
        },
        "alert_type": {
            "description": "Box declared down.",
            "name": "boxDown"
        },
        "severity": 50,
        "value": 100
    }
    ```
    </details>

* `GET` to `/api/v1/alerts/<int:pk>`: returns an alert by pk
* `GET` to `/api/v1/alerts/active/`: returns all active alerts
* `PUT` to `/api/v1/alerts/<int:pk>/active`: changes an alert's active state by pk
  * Body: `{ "active": <bool> }`
* `GET` to `/api/v1/alerts/metadata/`: returns relevant metadata for all alerts

</details>

<details>
<summary>Notification profile endpoints</summary>

* `/api/v1/notificationprofiles/`:
  * `GET`: returns the logged in user's notification profiles
  * `POST`: creates and returns a notification profile which is then connected to the logged in user
    <details>
    <summary>Body:</summary>

    ```json
    {
        "time_slot": 1,
        "filters": [
            1,
            2
        ],
        "media": [
            "EM",
            "SM"
        ],
        "active": true
    }
    ```
    </details>

* `/api/v1/notificationprofiles/<int:pk>`:
  * `GET`: returns one of the logged in user's notification profiles by pk
  * `PUT`: updates and returns one of the logged in user's notification profiles by pk
    * Body: same as `POST` to `/api/v1/notificationprofiles/`
  * `DELETE`: deletes one of the logged in user's notification profiles by pk

* `GET` to `/api/v1/notificationprofiles/<int:pk>/alerts/`: returns all alerts - both active and historic - filtered by one of the logged in user's notification profiles by pk

* `/api/v1/notificationprofiles/timeslots/`:
  * `GET`: returns the logged in user's time slots
  * `POST`: creates and returns a time slot which is then connected to the logged in user
    <details>
    <summary>Body:</summary>

    ```json
    {
        "name": "Weekdays",
        "time_intervals": [
            {
                "day": "MO",
                "start": "08:00:00",
                "end": "16:00:00"
            },
            {
                "day": "TU",
                "start": "08:00:00",
                "end": "16:00:00"
            },
            {
                "day": "WE",
                "start": "08:00:00",
                "end": "16:00:00"
            },
            {
                "day": "TH",
                "start": "08:00:00",
                "end": "16:00:00"
            },
            {
                "day": "FR",
                "start": "08:00:00",
                "end": "16:00:00"
            }
        ]
    }
    ```
    </details>

* `/api/v1/notificationprofiles/timeslots/<int:pk>`:
  * `GET`: returns one of the logged in user's time slots by pk
  * `PUT`: updates and returns one of the logged in user's time slots by pk
    * Body: same as `POST` to `/notificationprofiles/timeslots/`
  * `DELETE`: deletes one of the logged in user's time slots by pk

* `/api/v1/notificationprofiles/filters/`:
  * `GET`: returns the logged in user's filters
  * `POST`: creates and returns a filter which is then connected to the logged in user
    <details>
    <summary>Body:</summary>

    ```json
    {
        "name": "Critical alerts",
        "filter_string": "{\"sourceIds\":[<AlertSource.pk>, ...], \"objectTypeIds\":[<ObjectType.pk>, ...], \"parentObjectIds\":[<ParentObject.pk>, ...], \"problemTypeIds\":[<ProblemType.pk>, ...]}"
    }
    ```
    </details>

* `/api/v1/notificationprofiles/filters/<int:pk>`:
  * `GET`: returns one of the logged in user's filters by pk
  * `PUT`: updates and returns one of the logged in user's filters by pk
    * Body: same as `POST` to `/api/v1/notificationprofiles/filters/`
  * `DELETE`: deletes one of the logged in user's filters by pk

* `POST` to `/api/v1/notificationprofiles/filterpreview/`: returns all alerts - both active and historic - filtered by the values in the body
  <details>
  <summary>Body:</summary>

  ```json
  {
      "sourceIds": [<AlertSource.pk>, ...],
      "objectTypeIds": [<ObjectType.pk>, ...],
      "parentObjectIds": [<ParentObject.pk>, ...],
      "problemTypeIds": [<ProblemType.pk>, ...]
  }
  ```
  </details>

</details>


## Models

### Explanation of terms
* `alert`: a blob of data sent from a network management system to inform about an event in the network.
* `source`: the network management system that the `alert` came from.
* `object`: the most specific object that the `alert` (network event) was about.
* `parent_object`: an object that the `object` is possibly a part of.
* `problem_type`: the type of problem that the `alert` is informing about.
* `active_state`: whether an `alert`'s problem has been resolved.

### ER diagram
![ER diagram](img/ER_model.png)
