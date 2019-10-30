# AAS
AAS - Aggregated Alarm System is a platform for aggregating alerts and sending notifications to users. Users build notification profiles that define which alerts they subscribe too. This repo hosts the back end built with Django, while the frontend is hosted here: https://github.com/ddabble/aas-frontend
## Prerequisites
* Python 3.5+
* Django 2.5.5+
* pip

## To run
1. Create a python 3.5+ virtual environment

2. Install dependencies

    ```
    pip install -r requirements/django.txt
    pip install -r requirements/base.txt
    pip install -r requirements/dev.txt
    ```

3. Apply migrations with ```python manage.py migrate```

4. Start server with ```python manage.py runserver 8000```
