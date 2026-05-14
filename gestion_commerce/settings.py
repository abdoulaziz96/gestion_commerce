INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    

    # allauth (commenté temporairement)
    # 'allauth',
    # 'allauth.account',
    # 'allauth.socialaccount',
    # 'allauth.socialaccount.providers.google',

    # Applications du projet
    'accounts',
    'produits',
    'ventes',
    'depenses',
    'stock',
    'rapports',
    'dashboard',
    'messagerie',
    'sync',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'allauth.account.middleware.AccountMiddleware',  # COMMENTÉ
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    # 'allauth.account.auth_backends.AuthenticationBackend',  # COMMENTÉ
]

# SITE_ID = 1  # COMMENTÉ si pas utilisé ailleurs

# ── Configuration allauth (TOUT COMMENTÉ) ──
# ACCOUNT_LOGIN_METHODS = {'email', 'username'}
# ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_EMAIL_VERIFICATION = 'optional'
# ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
# ACCOUNT_USERNAME_REQUIRED = False
# ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'

# ── Google OAuth (TOUT COMMENTÉ) ──
# SOCIALACCOUNT_PROVIDERS = {
#     'google': {
#         'SCOPE': ['profile', 'email'],
#         'AUTH_PARAMS': {'access_type': 'online'},
#         'OAUTH_PKCE_ENABLED': True,
#     }
# }

# SOCIALACCOUNT_AUTO_SIGNUP = True
# SOCIALACCOUNT_LOGIN_ON_GET = True