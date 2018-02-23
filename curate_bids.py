import argparse
import logging
import json
import os
import tempfile
import sys

import flywheel

from supporting_files import bidsify_flywheel, utils, templates
from supporting_files.project_tree import get_project_tree

PROJECT_TEMPLATE_FILE_NAME = 'project-template.json'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('curate-bids')

def clear_meta_info(context, template):
    if 'info' in context and template.namespace in context['info']:
        del context['info'][template.namespace]

def format_validation_error(err):
    path = '/'.join(err.path)
    if path:
        return path + ' ' + err.message
    return err.message

def validate_meta_info(container, template):
    """ Validate meta information

    Adds 'BIDS.NA' if no BIDS info present
    Adds 'BIDS.valid' and 'BIDS.error_message'
        to communicate to user if values are valid

    Currently, validation is only checking if
        mandatory properties are non-empty strings

    Could add the following checks:
        Are the values alpha numeric?


    """
    # Get namespace
    namespace = template.namespace

    # If 'info' is NOT in container, then must not
    #   have matched to a template, create 'info'
    #  field with object {'BIDS': 'NA'}
    if 'info' not in container:
        container['info'] = {namespace: 'NA'}
    # if the namespace ('BIDS') is NOT in 'info',
    #   then must not have matched to a template,
    #   add  {'BIDS': 'NA'} to the meta info
    elif namespace not in container['info']:
        container['info'][namespace] = 'NA'
    # If already assigned BIDS 'NA', then break
    elif container['info'][namespace] == 'NA':
        pass
    # Otherwise, iterate over keys within container
    else:
        valid = True
        error_message = ''

        # Find template
        templateName = container['info'][namespace].get('template')
        if templateName:
            templateDef = template.definitions.get(templateName)
            if templateDef:
                errors = template.validate(templateDef, container['info'][namespace])
                if errors:
                    valid = False
                    error_message = '\n'.join([format_validation_error(err) for err in errors])
            else:
                valid = False
                error_message += 'Unknown template: %s. ' % templateName

        # Assign 'valid' and 'error_message' values
        container['info'][namespace]['valid'] = valid
        container['info'][namespace]['error_message'] = error_message

def update_meta_info(fw, context):
    """ Update file information

    """
    # Modify file
    if context['container_type'] == 'file':
        # Modify acquisition file
        if context['parent_container_type'] == 'acquisition':
            fw.set_acquisition_file_info(
                    context['acquisition']['_id'],
                    context['file']['name'],
                    context['file']['info']
                    )
        # Modify project file
        elif context['parent_container_type'] == 'project':
            fw.set_project_file_info(
                    context['project']['_id'],
                    context['file']['name'],
                    context['file']['info']
                    )
        # Modify session file
        elif context['parent_container_type'] == 'session':
            fw.set_session_file_info(
                    context['session']['_id'],
                    context['file']['name'],
                    context['file']['info']
                    )
        else:
            logger.info('Cannot determine file parent container type')
    # Modify project
    elif context['container_type'] == 'project':
        fw.replace_project_info(context['project']['_id'], context['project']['info'])
    # Modify session
    elif context['container_type'] == 'session':
        fw.replace_session_info(context['session']['_id'], context['session']['info'])
    # Cannot determine container type
    else:
        logger.info('Cannot determine container type')

def curate_bids_dir(fw, project_id, reset=False, template_file=None):
    """

    fw: Flywheel client
    project_id: project id of project to curate

    """
    project = get_project_tree(fw, project_id)
    curate_bids_tree(fw, project, reset, template_file, True)

def curate_bids_tree(fw, project, reset=False, template_file=None, update=True):
    # Get project
    project_files = project.get('files', [])

    # Get template (for now, just use default)
    template = templates.DEFAULT_TEMPLATE

    # Check for project file
    if not template_file:
        for f in project_files:
            if f['name'] == PROJECT_TEMPLATE_FILE_NAME:
                fd, path = tempfile.mkstemp('.json')
                os.close(fd)

                logger.info('Using project template: {0}'.format(f['name']))
                fw.download_file_from_project(project_id, f['name'], path)
                template_file = path

    if template_file:
        template = templates.loadTemplate(template_file)

    ##
    # Curation is now a 3-pass process
    # 1. Do initial template matching and updating
    # 2. Perform any path resolutions
    # 3. Send updates to server
    ##

    # 1. Do initial template matching and updating
    for context in project.context_iter():
        ctype = context['container_type']
        parent_ctype = context['parent_container_type']

        if reset:
            clear_meta_info(context[ctype], template)

        if ctype == 'project':
            bidsify_flywheel.process_matching_templates(context, template)
            # Validate meta information
            # TODO: Improve the validator to understand what is valid for dataset_description file...
            # validate_meta_info(context['project'])

        elif ctype == 'session':
            # Returns true if modified
            bidsify_flywheel.ensure_info_exists(context['session'], template)

        elif ctype == 'file':
            if parent_ctype == 'project' and context['file']['name'] == PROJECT_TEMPLATE_FILE_NAME:
                # Don't BIDSIFY project template
                continue

            # Process matching
            context['file'] = bidsify_flywheel.process_matching_templates(context, template)
            # Validate meta information
            validate_meta_info(context['file'], template)

    # 3. Send updates to server
    if update:
        for context in project.context_iter():
            ctype = context['container_type']
            node = context[ctype]
            if node.is_dirty():
                update_meta_info(fw, context)


if __name__ == '__main__':
    ### Read in arguments
    parser = argparse.ArgumentParser(description='BIDS Curation')
    parser.add_argument('--api-key', dest='api_key', action='store',
            required=True, help='API key')
    parser.add_argument('-p', dest='project_label', action='store',
            required=False, default=None, help='Project Label on Flywheel instance')
    parser.add_argument('--session', dest='session_id', action='store',
            required=False, default=None, help='Session ID, used to look up project if project label is not readily available')
    parser.add_argument('--reset', dest='reset', action='store_true', 
            default=False, help='Reset BIDS data before running')
    parser.add_argument('--template-file', dest='template_file', action='store',
            default=None, help='Template file to use')
    args = parser.parse_args()

    ### Prep
    # Check API key - raises Error if key is invalid
    fw = flywheel.Flywheel(args.api_key)
    # Get project id from label
    if args.project_label:
        project_id = utils.validate_project_label(fw, args.project_label)
    elif args.session_id:
        project_id = utils.get_project_id_from_session_id(fw, args.session_id)
    else:
        print('Either project label or session id is required!')
        sys.exit(1)


    ### Curate BIDS project
    curate_bids_dir(fw, project_id, reset=args.reset, template_file=args.template_file)
