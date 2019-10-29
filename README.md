# AAS Documentation

## Prerequisites
* Python 3.6+
* pip


## Dataporten setup
* Register a new application with the following redirect URL: `{server_url}/complete/dataporten_feide/`
  * `{server_url}` must be replaced with the URL to the server running this project, like `http://localhost:8000`
* Add the following permission scopes:
  * `profile`
  * `userid`
  * `userid-feide`
* Create the text file `src/aas/site/settings/dataporten_secret.txt` containing the client key to the application


## Email setup for production
* Change `EMAIL_HOST_USER` in [`base.py`](/src/aas/site/settings/base.py) to an email address to send notifications from
* Change `EMAIL_HOST` in [`prod.py`](/src/aas/site/settings/prod.py) to match the email's server URL
* Create the text file `src/aas/site/settings/email_secret.txt` containing the password to the email account

*A Gmail account with "Allow less secure apps" turned on, was used in the development of this project.*


## Project setup
* `pip install -r requirements/django.txt -r requirements/base.txt -r requirements/dev.txt`
* `python manage.py migrate`
* `python manage.py runserver`


## Endpoints
*`/admin/` to access the project's admin pages.*

All endpoints require requests to contain a header with key `Authorization` and value `Token {token}`, where `{token}` is replaced by a registered auth token; these are generated per user by logging in through Feide, and can be found at `/admin/authtoken/token/`.

* `GET` to `/alerts/`: returns all alerts
* *add more here*
