import ckan.plugins as p


class Demo(p.SingletonPlugin):

    p.implements(p.IConfigurer)

    def update_config(self, config):
        if p.toolkit.check_ckan_version(min_version='2.0'):
            # add template directory
            p.toolkit.add_template_directory(config, 'templates')
            p.toolkit.add_public_directory(config, 'public')
