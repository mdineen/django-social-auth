from openid.extensions import ax, sreg

from .base import SocialAuthBackend
from .openid_auth import OLD_AX_ATTRS, AX_SCHEMA_ATTRS


class OAuthBackend(SocialAuthBackend):
    """OAuth authentication backend base class"""
    name = 'oauth'

    def get_user_id(self, details, response):
        "OAuth providers return an unique user id in response"""
        return response['id']


class TwitterOAuthBackend(OAuthBackend):
    """Twitter OAuth authentication backend"""
    name = 'twitter'

    def authenticate(self, **kwargs):
        if kwargs.pop('twitter', False):
            return super(TwitterOAuthBackend, self).authenticate(**kwargs)

    def get_user_details(self, response):
        return {'email': '', # not supplied
                'username': response['screen_name'],
                'fullname': response['name'],
                'firstname': response['name'],
                'lastname': ''}


class FacebookOAuthBackend(OAuthBackend):
    """Facebook OAuth authentication backend"""
    name = 'facebook'

    def authenticate(self, **kwargs):
        if kwargs.pop('facebook', False):
            return super(FacebookOAuthBackend, self).authenticate(**kwargs)

    def get_user_details(self, response):
        return {'email': response.get('email', ''),
                'username': response['name'],
                'fullname': response['name'],
                'firstname': response.get('first_name', ''),
                'lastname': response.get('last_name', '')}

       
class OpenIDBackend(SocialAuthBackend):
    """Generic OpenID authentication backend"""
    name = 'openid'

    def authenticate(self, **kwargs):
        """Authenticate the user based on an OpenID response."""
        if kwargs.pop('openid', False):
            return super(OpenIDBackend, self).authenticate(**kwargs)

    def get_user_id(self, details, response):
        return response.identity_url

    def get_user_details(self, response):
        values = {'email': None,
                  'username': None,
                  'fullname': None,
                  'firstname': None,
                  'lastname': None}

        resp = sreg.SRegResponse.fromSuccessResponse(response)
        if resp:
            values.update({'email': resp.get('email'),
                           'fullname': resp.get('fullname'),
                           'username': resp.get('nickname')})

        # Use Attribute Exchange attributes if provided
        resp = ax.FetchResponse.fromSuccessResponse(response)
        if resp:
            values.update((alias.replace('old_', ''), resp.getSingle(src))
                            for src, alias in OLD_AX_ATTRS + AX_SCHEMA_ATTRS)

        fullname = values.get('fullname', '')
        firstname = values.get('firstname', '')
        lastname = values.get('lastname', '')

        if not fullname and firstname and lastname:
            fullname = firstname + ' ' + lastname
        elif fullname:
            try: # Try to split name for django user storage
                firstname, lastname = fullname.rsplit(' ', 1)
            except ValueError:
                lastname = fullname

        values.update({'fullname': fullname,
                       'firstname': firstname,
                       'lastname': lastname,
                       'username': values.get('username') or \
                                   (firstname.title() + lastname.title())})
        return values
