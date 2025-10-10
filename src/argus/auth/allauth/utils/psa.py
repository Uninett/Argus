from allauth.socialaccount.models import SocialAccount
from social_django.models import UserSocialAuth

"""
Allauth format, example dataporten
==================================

id:  int
provider: str (dataporten)
uid: str (uuid)
last_login: datetime with timestamp
date_joined: datetime with timestamp
extra_data: json {
    "name": str (full name),
    "email": str (email),
    "userid": str (uuid),
    "userid_sec": List[str], str with internal structure,
    "profilephoto": str ("p:" + uuid)
user_id: int

PSA, example dataporten_feide
=============================

id:  int
provider: str (dataporten_feide)
uid: str (uuid)
user_id: int
created: datetime with timestamp
modified: datetime with timestamp
extra_data: json {
    "scope": "userid userid-feide userinfo-name userinfo-photo",
    "userid": str (uuid),
    "fullname": str (full name),
    "auth_time": int (epoch),
    "token_type": "Bearer",
    "access_token": str (uuid),
    "profilephoto_url": str (url)
"""


def convert_from_psa_socialaccount(user):
    "Convert data in the PSA socialaccount table to the allauth social_account table"

    allauths = SocialAccount.objects.filter(user=user)
    psas = UserSocialAuth.objects.filter(user=user)
    skipped = set()
    ok = set()
    bad_extra_data = {}
    for psa in psas:
        provider = _map_provider(psa.provider)
        if allauths.filter(provider=provider).exists():
            skipped.add(provider)
            continue
        try:
            extra_data = _convert_extra_data(psa.provider, psa.extra_data)
        except KeyError:
            bad_extra_data[psa.provider] = psa.extra_data
            continue
        else:
            if not extra_data:
                bad_extra_data[psa.provider] = psa.extra_data
                continue
        allauth = SocialAccount(
            user=user,
            provider=provider,
            uid=psa.uid,
            date_joined=psa.created,
            last_login=psa.modified,
            extra_data=extra_data,
        )
        allauth.save()
        ok.add(provider)
    return ok, skipped, bad_extra_data


def _map_provider(provider):
    mapping = {"dataporten_feide": "dataporten"}
    return mapping.get(provider, provider)


def _convert_profilephoto_url(url):
    if "/p:" not in url:
        return ""
    return "p:" + url.split("/p:")[1]


def _convert_extra_data(provider, extra_data):
    data = {}
    userid_key = "userid"
    if provider == "oidc":
        userid_key = "id"
    data["userid"] = extra_data[userid_key]
    photo = _convert_profilephoto_url(extra_data.get("profilephoto_url", ""))
    if photo:
        data["profilephoto"] = photo
    name = extra_data.get("name", extra_data.get("fullname", ""))
    if name:
        data["name"] = name
    return data
