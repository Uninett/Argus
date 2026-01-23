Fixed longstanding bug that led to fewer notifications than expected. Instead
of checking when an *event* happened in order to decide whether to send
a notification, we only checked when the incident *started*. So, no
notifications could be sent for long-lasting incidents if they started outside
of all active timeslots.
