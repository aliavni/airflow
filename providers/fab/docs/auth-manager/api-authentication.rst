 .. Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

 ..   http://www.apache.org/licenses/LICENSE-2.0

 .. Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.

API Authentication
==================

Authentication for the API is handled separately to the Web Authentication. The default is to
check the user session:

.. code-block:: ini

    [api]
    auth_backends = airflow.providers.fab.auth_manager.api.auth.backend.session

.. versionchanged:: 1.10.11

    In Airflow <1.10.11, the default setting was to allow all API requests without authentication, but this
    posed security risks for if the Webserver is publicly accessible.

.. versionchanged:: 2.3.0

    In Airflow <2.3.0 this setting was ``auth_backend`` and allowed only one
    value. In 2.3.0 it was changed to support multiple backends that are tried
    in turn.

If you want to check which authentication backends are currently set, you can use ``airflow config get-value api auth_backends``
command as in the example below.

.. code-block:: console

    $ airflow config get-value api auth_backends
    airflow.providers.fab.auth_manager.api.auth.backend.basic_auth

.. versionchanged:: 3.0.0

    In Airflow, the default setting is using token based authentication.
    This approach is independent from which ``auth_backend`` is used.
    The default setting is using Airflow public API to create a token (JWT) first and use this token in the requests to access the API.


JWT Token based authentication
''''''''''''''''''''''''''''''
The JWT token based authentication is the default setting for the API.
To be able to use the Airflow Public API, you need to create a token first and use this token in the requests to access the API.

Endpoints are populated under ``/auth`` path. These endpoints are mounted to the Airflow API.
You should use your username and password, as seen in the example below.
The token is valid for seconds defined in ``auth_jwt_expiration_time`` which can be set from ``airflow.cfg``.

Example of creating a token:
.. code-block:: bash

    curl -X 'POST' \
      'http://localhost:32784/auth/token' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "username": "username",
      "password": "password"
      }'

This process will return a token that you can use in the requests to access the API.

Kerberos authentication
'''''''''''''''''''''''

Kerberos authentication is currently supported for the API, both experimental and stable.

To enable Kerberos authentication, set the following in the configuration:

.. code-block:: ini

    [api]
    auth_backends = airflow.providers.fab.auth_manager.api.auth.backend.kerberos_auth

    [kerberos]
    keytab = <KEYTAB>

The airflow Kerberos service is configured as ``airflow/fully.qualified.domainname@REALM``. Make sure this
principal exists `in both the Kerberos database as well as in the keytab file </docs/apache-airflow/stable/security/kerberos.html#enabling-kerberos>`_.

You have to make sure to name your users with the kerberos full username/realm in order to make it
work. This means that your user name should be ``user_name@REALM``.

.. code-block:: bash

    kinit user_name@REALM
    ENDPOINT_URL="http://localhost:8080/"
    curl -X GET  \
        --negotiate \  # enables Negotiate (SPNEGO) authentication
        --service airflow \  # matches the `airflow` service name in the `airflow/fully.qualified.domainname@REALM` principal
        --user : \
        "${ENDPOINT_URL}/api/v1/pools"


.. note::

    Remember that the stable API is secured by both authentication and `access control <./access-control.html>`_.
    This means that your user needs to have a Role with necessary associated permissions, otherwise you'll receive
    a 403 response.


Basic authentication
''''''''''''''''''''

`Basic username password authentication <https://en.wikipedia.org/wiki/Basic_access_authentication>`_ is currently
supported for the API. This works for users created through LDAP login or
within Airflow Metadata DB using password.

To enable basic authentication, set the following in the configuration:

.. code-block:: ini

    [api]
    auth_backends = airflow.providers.fab.auth_manager.api.auth.backend.basic_auth

Username and password needs to be base64 encoded and send through the
``Authorization`` HTTP header in the following format:

.. code-block:: text

    Authorization: Basic Base64(username:password)

Here is a sample curl command you can use to validate the setup:

.. code-block:: bash

    ENDPOINT_URL="http://localhost:8080/"
    curl -X GET  \
        --user "username:password" \
        "${ENDPOINT_URL}/api/v1/pools"

Note, you can still enable this setting to allow API access through username
password credential even though Airflow webserver might be using another
authentication method. Under this setup, only users created through LDAP or
``airflow users create`` command will be able to pass the API authentication.

Roll your own API authentication
''''''''''''''''''''''''''''''''

Each auth backend is defined as a new Python module. It must have 2 defined methods:

* ``init_app(app: Flask)`` - function invoked when creating a flask application, which allows you to add a new view.
* ``requires_authentication(fn: Callable)`` - a decorator that allows arbitrary code execution before and after or instead of a view function.

and may have one of the following to support API client authorizations used by :ref:`remote mode for CLI <cli-remote>`:

* function ``create_client_session() -> requests.Session``
* attribute ``CLIENT_AUTH: tuple[str, str] | requests.auth.AuthBase | None``

After writing your backend module, provide the fully qualified module name in the ``auth_backends`` key in the ``[api]``
section of ``airflow.cfg``.

Additional options to your auth backend can be configured in ``airflow.cfg``, as a new option.
