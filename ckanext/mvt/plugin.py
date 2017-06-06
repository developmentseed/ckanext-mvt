import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.model as model
from ckan.lib.celery_app import celery
import ckan.lib.datapreview as datapreview

import pylons.config as config
import pylons
import uuid
import ckanapi
import tempfile
import os
import logging
import lib
import mimetypes

log = logging.getLogger(__name__)

def _celery_task(resource_id, action, tempdir):
    site_url = config.get('ckan.site_url', 'http://localhost/')
    apikey = model.User.get('default').apikey
    s3config = {
        'bucket': config.get('ckanext.mvt.s3.bucket'),
        'access_key': config.get('ckanext.mvt.s3.access_key'),
        'secret_key': config.get('ckanext.mvt.s3.secret_key'),
    }

    celery.send_task(
        'mvt.process_resource',
        args=[
            resource_id,
            site_url,
            apikey,
            s3config,
            tempdir,
            action
        ],
        task_id='{}-{}'.format(str(uuid.uuid4()), action)
    )


class MvtPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    TEMPDIR = os.path.join(os.path.dirname(__file__), '..', 'tmp')

    # IConfigurer
    def update_config(self, config):
        mimetypes.add_type('application/geo+json', '.geojson')

    # IResourceController
    def after_create(self, context, resource):
        _celery_task(resource['id'], 'create', MvtPlugin.TEMPDIR)

    def after_update(self, context, resource):
        _celery_task(resource['id'], 'update', MvtPlugin.TEMPDIR)

    def before_delete(self, context, resource, resources):
        _celery_task(resource['id'], 'delete', MvtPlugin.TEMPDIR)

    def before_show(self, data_dict):
        cache = lib.CacheHandler(MvtPlugin.TEMPDIR)
        s3url = cache.get_s3url(data_dict.get('id'))
        data_dict['tilejson'] = s3url
        return data_dict

class MvtViewPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IConfigurer, inherit=True)
    plugins.implements(plugins.IResourceView, inherit=True)

    TEMPDIR = os.path.join(os.path.dirname(__file__), '..', 'tmp')

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')

    # IResourceView

    def info(self):
        return {
            'name': 'mvt_view',
            'title': 'Map View',
            'icon': 'globe',
            'iframed': False,
            'always_available': False
        }

    def setup_template_variables(self, context, data_dict):
        layers = toolkit.aslist(config.get('ckanext.mvt.mapbox.style', ''))
        labels = toolkit.aslist(config.get('ckanext.mvt.mapbox.style_label', ''))
        cache = lib.CacheHandler(MvtPlugin.TEMPDIR)
        if len(labels) != len(layers):
            log.warn('The config file contains {0} layer id\'s and {1} labels. The extension needs an equal amount and can only use the first {2}'.format(len(labels), len(layers), min(len(layers),len(labels))))

        baseLayers = [];
        for i in range(min(len(layers),len(labels))):
            baseLayers.append({"id": layers[i], "label": labels[i]})

        return {
            'tilejson': data_dict['resource'].get('tilejson', ''),
            'mapbox': {
                'account': config.get('ckanext.mvt.mapbox.account', ''),
                'key': config.get('ckanext.mvt.mapbox.key', ''),
                'defaultStyle': toolkit.aslist(config.get('ckanext.mvt.mapbox.style', ''))[0],
                'styles': baseLayers
            },
            'resource_job_status': cache.get_job_status(data_dict['resource'].get('id'))
        }


    def can_view(self, data_dict):
        return data_dict['resource'].get('format', '').lower() == 'geojson'

    def view_template(self, context, data_dict):
        return 'mvtview.html'

    def after_update(self, context, data_dict):
        self.add_default_views(context, data_dict)

    def after_create(self, context, data_dict):
        self.add_default_views(context, data_dict)
