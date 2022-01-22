"""
Most of this security has been well tested (and stolen) from https://github.com/Intility/fastapi-azure-auth,
which I'm the author of. However, this specific project has been written in a day or two for fun, not for enterprise
security. If you're using this library as inspiration for anything, please keep that in mind.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes
from fastapi.security.base import SecurityBase
from httpx import AsyncClient
from jose import ExpiredSignatureError, jwk, jwt
from jose.backends.cryptography_backend import CryptographyRSAKey
from jose.exceptions import JWTClaimsError, JWTError
from starlette.requests import Request

from core.config import settings
from schemas.user import User


class InvalidAuth(HTTPException):
    """
    Exception raised when the user is not authorized
    """

    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers={'WWW-Authenticate': 'Bearer'}
        )


log = logging.getLogger(__name__)


class OpenIdConfig:
    def __init__(self) -> None:
        self._config_timestamp: datetime | None = None
        self.openid_url = (
            f'https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/'
            f'{settings.AWS_USER_POOL_ID}/.well-known/openid-configuration'
        )

        self.issuer: str

    async def load_config(self) -> None:
        """
        Loads config from the openid endpoint if it's over 24 hours old (or don't exist)
        """
        refresh_time = datetime.now() - timedelta(hours=24)
        if not self._config_timestamp or self._config_timestamp < refresh_time:
            try:
                log.debug('Loading Cognito OpenID configuration.')
                await self._load_openid_config()
                self._config_timestamp = datetime.now()
            except Exception as error:
                log.exception('Unable to fetch OpenID configuration from Cognito. Error: %s', error)
                # We can't fetch an up to date openid-config, so authentication will not work.
                if self._config_timestamp:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail='Connection to Cognito is down. Unable to fetch provider configuration',
                        headers={'WWW-Authenticate': 'Bearer'},
                    )
                else:
                    raise RuntimeError(f'Unable to fetch provider information. {error}')

            log.info('Loaded settings from Cognito.')
            log.info('Issuer:                 %s', self.issuer)

    async def _load_openid_config(self) -> None:
        """
        Load openid config, fetch signing keys
        """
        async with AsyncClient(timeout=10) as client:
            log.info('Fetching OpenID Connect config from %s', self.openid_url)
            openid_response = await client.get(self.openid_url)
            openid_response.raise_for_status()
            openid_cfg = openid_response.json()

            self.authorization_endpoint = openid_cfg['authorization_endpoint']
            self.token_endpoint = openid_cfg['token_endpoint']
            self.issuer = openid_cfg['issuer']

            jwks_uri = openid_cfg['jwks_uri']
            log.info('Fetching jwks from %s', jwks_uri)
            jwks_response = await client.get(jwks_uri)
            jwks_response.raise_for_status()
            self._load_keys(jwks_response.json()['keys'])

    def _load_keys(self, keys: list[dict[str, Any]]) -> None:
        """
        Create certificates based on signing keys and store them
        """
        self.signing_keys: dict[str, CryptographyRSAKey] = {}
        for key in keys:
            if key.get('use') == 'sig':  # Only care about keys that are used for signatures, not encryption
                log.debug('Loading public key from certificate: %s', key)
                cert_obj = jwk.construct(key, 'RS256')
                if kid := key.get('kid'):
                    self.signing_keys[kid] = cert_obj.public_key()


class CognitoAuthorizationCodeBearerBase(SecurityBase):
    def __init__(self) -> None:
        self.openid_config: OpenIdConfig = OpenIdConfig()

        self.oauth = OAuth2AuthorizationCodeBearer(
            authorizationUrl='https://auth.klepp.me/oauth2/authorize',
            tokenUrl='https://auth.klepp.me/oauth2/token',
            scopes={'openid': 'openid'},
            scheme_name='CognitoAuth',
            auto_error=True,
        )
        self.model = self.oauth.model
        self.scheme_name: str = 'Cognito'

    async def __call__(self, request: Request, security_scopes: SecurityScopes) -> User:
        """
        Extends call to also validate the token.
        """
        access_token = await self.oauth(request=request)
        try:
            # Extract header information of the token.
            header: dict[str, str] = jwt.get_unverified_header(token=access_token) or {}
            claims: dict[str, Any] = jwt.get_unverified_claims(token=access_token) or {}
        except Exception as error:
            log.warning('Malformed token received. %s. Error: %s', access_token, error, exc_info=True)
            raise InvalidAuth(detail='Invalid token format')

        for scope in security_scopes.scopes:
            token_scope_string = claims.get('scp', '')
            if isinstance(token_scope_string, str):
                token_scopes = token_scope_string.split(' ')
                if scope not in token_scopes:
                    raise InvalidAuth('Required scope missing')
            else:
                raise InvalidAuth('Token contains invalid formatted scopes')

        # Load new config if old
        await self.openid_config.load_config()

        # Use the `kid` from the header to find a matching signing key to use
        try:
            if key := self.openid_config.signing_keys.get(header.get('kid', '')):
                # We require and validate all fields in a Cognito token
                options = {
                    'verify_signature': True,
                    'verify_aud': False,
                    'verify_iat': True,
                    'verify_exp': True,
                    'verify_nbf': False,
                    'verify_iss': True,
                    'verify_sub': True,
                    'verify_jti': True,
                    'verify_at_hash': True,
                    'require_aud': False,
                    'require_iat': True,
                    'require_exp': True,
                    'require_nbf': False,
                    'require_iss': True,
                    'require_sub': True,
                    'require_jti': False,
                    'require_at_hash': False,
                    'leeway': 0,
                }
                # Validate token
                token = jwt.decode(
                    access_token,
                    key=key,  # noqa
                    algorithms=['RS256'],
                    issuer=self.openid_config.issuer,
                    options=options,
                )
                # Attach the user to the request. Can be accessed through `request.state.user`
                user: User = User(**token)
                request.state.user = user
                return user
        except JWTClaimsError as error:
            log.info('Token contains invalid claims. %s', error)
            raise InvalidAuth(detail='Token contains invalid claims')
        except ExpiredSignatureError as error:
            log.info('Token signature has expired. %s', error)
            raise InvalidAuth(detail='Token signature has expired')
        except JWTError as error:
            log.warning('Invalid token. Error: %s', error, exc_info=True)
            raise InvalidAuth(detail='Unable to validate token')
        except Exception as error:
            # Extra failsafe in case of a bug in a future version of the jwt library
            log.exception('Unable to process jwt token. Uncaught error: %s', error)
            raise InvalidAuth(detail='Unable to process token')
        log.warning('Unable to verify token. No signing keys found')
        raise InvalidAuth(detail='Unable to verify token, no signing keys found')
