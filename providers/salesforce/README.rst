
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

.. NOTE! THIS FILE IS AUTOMATICALLY GENERATED AND WILL BE OVERWRITTEN!

.. IF YOU WANT TO MODIFY TEMPLATE FOR THIS FILE, YOU SHOULD MODIFY THE TEMPLATE
   ``PROVIDER_README_TEMPLATE.rst.jinja2`` IN the ``dev/breeze/src/airflow_breeze/templates`` DIRECTORY

Package ``apache-airflow-providers-salesforce``

Release: ``5.11.2``

Release Date: ``|PypiReleaseDate|``

`Salesforce <https://www.salesforce.com/>`__


Provider package
----------------

This is a provider package for ``salesforce`` provider. All classes for this provider package
are in ``airflow.providers.salesforce`` python package.

You can find package information and changelog for the provider
in the `documentation <https://airflow.apache.org/docs/apache-airflow-providers-salesforce/5.11.2/>`_.

Installation
------------

You can install this package on top of an existing Airflow 2 installation (see ``Requirements`` below
for the minimum Airflow version supported) via
``pip install apache-airflow-providers-salesforce``

The package supports the following python versions: 3.10,3.11,3.12,3.13

Requirements
------------

=====================  =====================================
PIP package            Version required
=====================  =====================================
``apache-airflow``     ``>=2.10.0``
``simple-salesforce``  ``>=1.0.0``
``pandas``             ``>=2.1.2; python_version < "3.13"``
``pandas``             ``>=2.2.3; python_version >= "3.13"``
=====================  =====================================

The changelog for the provider package can be found in the
`changelog <https://airflow.apache.org/docs/apache-airflow-providers-salesforce/5.11.2/changelog.html>`_.
