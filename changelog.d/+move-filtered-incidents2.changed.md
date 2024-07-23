Last half of big filter refactor/cleanup.

* Moves `Filter.filtered_incidents` to `argus.filter.queryset_filters.QuerySetFilter`
  * Changes the signature so that it works on a filterblob, not a Filter model
    instance
* Ensures that the fallback filter, which is only relevant when sending
  notifications, is ignored everywhere else. First step in getting rid of this
  misfeature of a setting.
* Adds support for filtering on event types
* Gets rid of `NotificationProfile.filtered_incidents`, instead use
  `argus.filter.queryset_filters.QuerySetFilter.incidents_by_notificationprofile`
