#!/bin/bash

graph_models_command="graph_models argus_auth argus_incident argus_notificationprofile -o docs/img/ER_model_v2.png"

if [python3 manage.py $graph_models_command || bash cmd.sh $graph_models_command || docker-compose exec api django-admin $graph_models_command];
then
    if [ $(git diff-tree -r --name-only HEAD^ | grep docs/img/ER_model_v2.png ) ];
    then
        echo "Please commit updated ER model."
        exit 1;
    fi;
    exit 0;
fi;
exit 1;
