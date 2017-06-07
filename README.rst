=============
ckanext-mvt
=============

This extension contains two plugins that adds large-size GeoJSON previewing to CKAN by converting the resources to Mapbox Vector Tiles:

- A plugin that takes a GeoJSON, converts it to MVT and uploads it to S3
- A plugin to preview the S3 tiles

------------
Requirements
------------

Tested with CKAN 2.4

------------
Installation
------------

To install ckanext-mvt:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-mvt Python package into your virtual environment::

     pip install ckanext-mvt (doesn't currently work)

3. Add ``mvt`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload

---------------
Config Settings
---------------

::

    # S3 configuration
    ckanext.mvt.s3.bucket = s3-bucket-name
    ckanext.mvt.s3.access_key = S3_ACCESS_KEY
    ckanext.mvt.s3.secret_key = S3_SECRET_KEY

    # Max size the resource can be for processing
    ckanext.mvt.max_size = 524288000

------------------------
Development Installation
------------------------

To install ckanext-mvt for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/developmentseed/ckanext-mvt.git
    cd ckanext-mvt
    python setup.py develop
    pip install -r dev-requirements.txt
