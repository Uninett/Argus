try:
    from argus.auth.allauth.utils.psa import convert_from_psa_socialaccount
except ImportError:

    def convert_from_psa_socialaccount(_):
        raise NotImplementedError


__all__ = ["convert_from_psa_socialaccount"]
