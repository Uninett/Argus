Added an optional JSONField "metadata" to incident. This can be used for any
additional info the glue-service would like to store on the incident that needs
more structure than tags. The field has been added to the V2
IncidentSerializer but we do not plan to expose it in the frontend.
