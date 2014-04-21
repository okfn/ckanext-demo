#!/usr/bin/env python
import json
import os
import urllib
from pylons import config
import ckan.model as model
import ckan.plugins.toolkit as toolkit
from ckan.lib.cli import CkanCommand
import ckan.lib.uploader as uploader


class Reset(CkanCommand):
    """
    Delete the extra datasets, groups, and organizations on demo.

    Usage:

    paster reset
           - Deletes all the datasets, groups, and organizations except the
             ones specified in the code.
    """
    summary = __doc__.split('\n')[1]
    usage = __doc__
    min_args = 0
    max_args = 1
    MAX_PER_PAGE = 50

    def _get_all_packages(self, context):
        page = 0
        while True:
            data_dict = {
                'offset': page * self.MAX_PER_PAGE,
                'limit': self.MAX_PER_PAGE,
            }
            packages = toolkit.get_action(
                'current_package_list_with_resources')(context, data_dict)
            if not packages:
                raise StopIteration
            for package in packages:
                yield package
            page += 1

    def command(self):
        if self.args and self.args[0] in ['--help', '-h', 'help']:
            print self.__doc__
            return
        self._load_config()
        user = toolkit.get_action('get_site_user')({'model': model,
                                                    'ignore_auth': True}, {})
        context = {'username': user.get('name'),
                   'user': user.get('name'),
                   'model': model}

        # Add new datasets to keep here
        keep_datasets = [
             u'newcastle-city-council-payments-over-500',
             u'food-hygiene-information-scheme-rating-glasgow',
             u'up-library-catalogue',
        ]

        # Add new organizations to keep here
        keep_orgs = [
            u'national-statistics-office',
            u'pagwell-borough-council',
        ]

        # Add new groups to keep here
        keep_groups = [
            u'geo-examples',
        ]

        # Get list of resources to delete and delete datasets
        datasets = self._get_all_packages(context)
        for dataset in datasets:
            # TODO: Don't delete datasets in the specified org
            if dataset['name'] not in keep_datasets or dataset['id'] not in keep_datasets:
                # save data of resources in filestore for later
                for res in dataset['resources']:
                    if res['url_type'] == 'upload':
                        # Delete the resource files from the filesystem
                        upload = uploader.ResourceUpload(res)
                        filepath = upload.get_path(res['id'])
                        try:
                            os.remove(filepath)
                        except:
                            pass
                # delete dataset
                print "Deleting dataset: {0}".format(dataset['name'])
                toolkit.get_action('dataset_delete')(context, {'id': dataset['id']})


        # Delete all organizations except specified ones
        orgs = toolkit.get_action('organization_list')(context, {})
        for org in orgs:
            if org not in keep_orgs:
                print "Deleting organization: {0}".format(org)
                toolkit.get_action('organization_delete')(context, {'id': org})
                toolkit.get_action('organization_purge')(context, {'id': org})

        # Delete all groups except expecified ones
        groups = toolkit.get_action('group_list')(context, {})
        for group in groups:
            if group not in keep_groups:
                print "Deleting group: {0}".format(group)
                toolkit.get_action('group_delete')(context, {'id': group})
                toolkit.get_action('group_purge')(context, {'id': group})

        # Purge datasets
        self.clean_deleted()


    def clean_deleted(self):
        sql = '''begin; update package set state = 'to_delete' where state <> 'deleted' and revision_id in (select id from revision where timestamp < now() - interval '1 day');
        delete from package_role where package_id in (select id from package where state = 'to_delete' );
        delete from user_object_role where id not in (select user_object_role_id from package_role) and context = 'Package';
        delete from resource_revision where resource_group_id in (select id from resource_group where package_id in (select id from package where state = 'to_delete'));
        delete from resource_group_revision where package_id in (select id from package where state = 'to_delete');
        delete from package_tag_revision where package_id in (select id from package where state = 'to_delete');
        delete from member_revision where table_id in (select id from package where state = 'to_delete');
        delete from package_extra_revision where package_id in (select id from package where state = 'to_delete');
        delete from package_revision where id in (select id from package where state = 'to_delete');
        delete from package_tag where package_id in (select id from package where state = 'to_delete');
        delete from resource where resource_group_id in (select id from resource_group where package_id in (select id from package where state = 'to_delete'));
        delete from package_extra where package_id in (select id from package where state = 'to_delete');
        delete from member where table_id in (select id from package where state = 'to_delete');
        delete from resource_group where package_id in (select id from package where state = 'to_delete');

        delete from related_dataset where dataset_id in (select id from package where state = 'to_delete');
        delete from package_relationship_revision where subject_package_id in (select id from package where state = 'to_delete');
        delete from package_relationship_revision where object_package_id in (select id from package where state = 'to_delete');
        delete from package_relationship where subject_package_id in (select id from package where state = 'to_delete');
        delete from package_relationship where object_package_id in (select id from package where state = 'to_delete');

        delete from package where id in (select id from package where state = 'to_delete'); commit;'''
        model.Session.execute(sql)
