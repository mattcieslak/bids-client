import os
import shutil
import unittest
import jsonschema

import flywheel

from supporting_files import bidsify_flywheel

class BidsifyTestCases(unittest.TestCase):

    def setUp(self):
        # Define testdir
        self.testdir = 'testdir'

    def tearDown(self):
        # Cleanup 'testdir', if present
        if os.path.exists(self.testdir):
            shutil.rmtree(self.testdir)

    def test_project_by_label_invalidproject(self):
        """ Get project that does not exist. Assert function returns None.

        NOTE: the environment variable $APIKEY needs to be defined with users API key
        """
        client = flywheel.Flywheel(os.environ['APIKEY'])
        label = 'doesnotexistdoesnotexistdoesnotexist89479587349'
        project = bidsify_flywheel.get_project_by_label(client, label)
        self.assertEqual(project, [])

    def test_project_by_label_validproject(self):
        """ Get project that DOES exist. Assert function returns the project.

        NOTE: the environment variable $APIKEY needs to be defined with users API key

        """
        client = flywheel.Flywheel(os.environ['APIKEY'])
        label = 'Project Name'
        project = bidsify_flywheel.get_project_by_label(client, label)
        project_expected = {u'group': u'adni', u'created': u'2016-10-31T14:53:07.378Z',
                u'modified': u'2017-06-30T16:26:45.731Z', u'label': u'Project Name',
                u'_id': u'58175ad3de26e00012c69306',
                u'permissions': [{u'access': u'admin',
                    u'_id': u'jenniferreiter@invenshure.com'}]}
        self.assertEqual(project[0], project_expected)

    def test_valid_namespace_valid(self):
        """ Assert function does not raise error when a VALID namespace passed """
        from supporting_files.templates import namespace
        bidsify_flywheel.valid_namespace(namespace)

    def test_valid_namespace_invalid1(self):
        """ Assert function returns False when a INVALID namespace passed.

        Namespace is invalid because 'namespace' key should have a string but it's value is 0

        """

        invalid_namespace = {
            "namespace": 0,
            "description": "Namespace for BIDS info objects in Flywheel",
            "datatypes": [
                {
                    "container_type": "file",
                    "description": "BIDS template for diffusion files",
                    "where": {
                        "type": "nifti",
                        },
                    "properties": {
                        "Task": {"type": "string", "label": "Task Label", "default": ""},
                        },
                    "required": ["Task"]
                    }
                ]
            }

        # Assert ValidationError raised
        with self.assertRaises(jsonschema.ValidationError) as err:
            bidsify_flywheel.valid_namespace(invalid_namespace)

    def test_valid_namespace_invalid2(self):
        """ Assert function returns False when a INVALID namespace passed.

        Namespace is invalid because it does not contain the property "container_type"

        """
        invalid_namespace = {
            "namespace": "BIDS",
            "description": "Namespace for BIDS info objects in Flywheel",
            "datatypes": [
                {
                    "description": "BIDS template for diffusion files",
                    "where": {
                        "type": "nifti"
                        },
                    "properties": {
                        "Task": {"type": "string", "label": "Task Label", "default": ""},
                        }
                    }
                ]
            }

        # Assert ValidationError raised
        with self.assertRaises(jsonschema.ValidationError) as err:
            bidsify_flywheel.valid_namespace(invalid_namespace)

    def test_process_string_template_required(self):
        """  """
        from supporting_files.templates import namespace
        # Get project template from the templates file
        auto_update_str = 'sub-<subject.code>_ses-<session.label>_acq-<acquisition.label>_bold.nii.gz'
        # initialize context object
        context = {
            'container_type': 'file',
            'parent_container_type': 'project',
            'project': {u'label': u'project123'},
            'subject': {u'code': u'00123'},
            'session': {u'label': u'session444'},
            'acquisition': {u'label': u'acq222'},
            'file': None,
            'ext': None
        }

        # Call function
        updated_string = bidsify_flywheel.process_string_template(auto_update_str, context)

        self.assertEqual(updated_string,
                'sub-%s_ses-%s_acq-%s_bold.nii.gz' % (
                    context['subject']['code'],
                    context['session']['label'],
                    context['acquisition']['label']
                    ))

    def test_process_string_template_optional(self):
        """  """
        # Define string to auto update, subject code is optional
        auto_update_str = '[sub-<subject.code>]_ses-<session.label>_acq-<acquisition.label>_bold.nii.gz'
        # initialize context object
        context = {
            'container_type': 'file',
            'parent_container_type': 'project',
            'project': {u'label': u'project123'},
            'subject': {u'code': None},
            'session': {u'label': u'session444'},
            'acquisition': {u'label': u'acq222'},
            'file': None,
            'ext': None
        }

        # Call function
        updated_string = bidsify_flywheel.process_string_template(auto_update_str, context)
        # Assert function honors the optional 'sub-<subject.code>'
        self.assertEqual(updated_string,
                '_ses-%s_acq-%s_bold.nii.gz' % (
                    context['session']['label'],
                    context['acquisition']['label']
                    ))


    def test_process_string_template_subject_none(self):
        """ """

        context = {
            'project': {
                'info': {'BIDS': {'Ackowledgements': '',
                    'Funding': '', 'Name': '', 'License': '',
                    'HowToAcknowledge': '', 'Authors': '', 
                    'ReferencesAndLinks': '','DatasetDOI': '', 'BIDSVersion': ''}
                    },
                u'group': u'jr',
                u'label': u'ds001_reduced',
                u'_id': u'5a0b656b9b89b7001a1f309e'
                },
            'parent_container_type': 'acquisition',
            'session': {
                u'group': u'jr',
                u'label': u'sub-01', u'project': u'5a0b656b9b89b7001a1f309e',
                u'_id': u'5a0b656e9b89b7001d1f3140',
                u'subject': {u'code': u'sub-01', u'_id': u'5a0b656e9b89b7001d1f313f'}},
            'acquisition': {
                u'files': [
                    {u'origin': {u'type': u'user', u'id': u'jenniferreiter@invenshure.com'},
                        u'mimetype': u'application/octet-stream', u'name': u'sub-01_T1w.nii.gz',
                        u'created': u'2017-11-14T21:51:54.287Z', u'measurements': [u'anatomy_t1w'],
                        u'modified': u'2017-11-14T21:51:54.287Z',
                        u'type': u'nifti', u'size': 5663237}
                    ],
                u'created': u'2017-11-14T21:51:42.971Z',
                u'modified': u'2017-11-14T21:59:08.922Z',
                u'label': u'anat', u'session': u'5a0b656e9b89b7001d1f3140',
                u'_id': u'5a0b656e9b89b7001a1f30a0'
                },
            'file': {
                u'origin': {u'type': u'user',
                u'id': u'jenniferreiter@invenshure.com'},
                u'mimetype': u'application/octet-stream',
                u'name': u'sub-01_T1w.nii.gz', u'created': u'2017-11-14T21:51:54.287Z',
                u'measurements': [u'anatomy_t1w'],
                u'modified': u'2017-11-14T21:51:54.287Z',
                'info': {
                    'BIDS': {'Run': '', 'Ce': '', 'Filename': '',
                    'Rec': '', 'Folder': 'anat', 'Modality': 'T1w', 'Mod': ''}},
                    u'type': u'nifti', u'size': 5663237},
            'ext': '.nii.gz', 'container_type': 'file', 'subject': None
        }



    """
    def test_process_string_template_required_notpresent(self):
        """ """
        # TODO: Determine the expected behavior of this...
        # Define string to auto update
        auto_update_str = 'sub-<subject.code>_ses-<session.label>'
        # initialize context object
        context = {
            'container_type': 'file',
            'parent_container_type': 'project',
            'project': {u'label': u'project123'},
            'subject': {},
            'session': {u'label': u'session444'},
            'acquisition': {u'label': u'acq222'},
            'file': None,
            'ext': None
        }

        # Call function
        updated_string = bidsify_flywheel.process_string_template(auto_update_str, context)
        # Assert function honors the optional 'sub-<subject.code>'
        self.assertEqual(updated_string,
                'sub-%s_ses-%s' % (
                    context['subject']['code'],
                    context['session']['label']
                    ))
        """

    """
    def test_process_string_template_required_None(self):
        """ """
        # TODO: Determine the expected behavior of this...
        # Define string to auto update
        auto_update_str = 'sub-<subject.code>_ses-<session.label>'
        # initialize context object
        context = {
            'container_type': 'file',
            'parent_container_type': 'project',
            'project': {u'label': u'project123'},
            'subject': {u'code': None},
            'session': {u'label': u'session444'},
            'acquisition': {u'label': u'acq222'},
            'file': None,
            'ext': None
        }

        # Call function
        updated_string = bidsify_flywheel.process_string_template(auto_update_str, context)
        # Assert function honors the optional 'sub-<subject.code>'
        self.assertEqual(updated_string,
                'sub-%s_ses-%s' % (
                    context['subject']['code'],
                    context['session']['label']
                    ))
    """

    def test_add_properties_valid(self):
        """ """
        properties = {
                "Filename": {"type": "string", "label": "Filename", "default": "",
                    "auto_update": 'sub-<subject.code>_ses-<session.label>[_acq-<acquisition.label>]_T1w{ext}'},
                "Folder": {"type": "string", "label":"Folder", "default": "anat"},
                "Ce": {"type": "string", "label": "CE Label", "default": ""},
                "Rec": {"type": "string", "label": "Rec Label", "default": ""},
                "Run": {"type": "string", "label": "Run Index", "default": ""},
                "Mod": {"type": "string", "label": "Mod Label", "default": ""},
                "Modality": {"type": "string", "label": "Modality Label", "default": "T1w",
                    "enum": [
                        "T1w","T2w","T1rho","T1map","T2map","FLAIR","FLASH","PD","PDmap",
                        "PDT2","inplaneT1","inplaneT2","angio","defacemask","SWImagandphase"
                        ]
                    }
                }
        project_obj = {u'label': u'Project Name'}
        # Call function
        info_obj = bidsify_flywheel.add_properties(properties, project_obj)
        # Expected info object
        for key in properties:
            project_obj[key] = properties[key]['default']
        self.assertEqual(info_obj, project_obj)

    def test_update_properties_valid(self):
        """ """
        # Define inputs
        properties = {
            "Filename": {"type": "string", "label": "Filename", "default": "",
                "auto_update": 'sub-<subject.code>_ses-<session.label>[_acq-<acquisition.label>]_T1w{ext}'},
            "Folder": {"type": "string", "label":"Folder", "default": "anat"},
            "Mod": {"type": "string", "label": "Mod Label", "default": ""},
            "Modality": {"type": "string", "label": "Modality Label", "default": "T1w"}
        }
        context = {
            'container_type': 'file', 'parent_container_type': 'acquisition',
            'project': None, 'subject': {u'code': u'001'},
            'session': {u'label': u'sesTEST'}, 'acquisition': {u'label': u'acqTEST'},
            'file': {
                u'measurements': [u'anatomy_t1w'],
                u'type': u'nifti'
            },
            'ext': '.nii.gz'
        }
        project_obj = {u'test1': u'123', u'test2': u'456'}
        # Call function
        info_obj = bidsify_flywheel.update_properties(properties, context, project_obj)
        # Update project_obj, as expected
        project_obj['Filename'] = u'sub-%s_ses-%s_acq-%s_T1w%s' % (
                context['subject']['code'],
                context['session']['label'],
                context['acquisition']['label'],
                context['ext']
                )
        self.assertEqual(project_obj, info_obj)

    def test_process_matching_templates_anat(self):
        """ """
        # Define context
        context = {
            'container_type': 'file',
            'parent_container_type': 'acquisition',
            'project': None,
            'subject': {u'code': u'001'},
            'session': {u'label': u'sesTEST'},
            'acquisition': {u'label': u'acqTEST'},
            'file': {u'measurements': [u'anatomy_t1w'],
                    u'type': u'nifti'},
            'ext': '.nii.gz'
        }
        # Call function
        container = bidsify_flywheel.process_matching_templates(context)
        # Define expected container
        container_expected = {
            'info': {
                'BIDS': {
                    'Filename': u'sub-001_ses-sestest_acq-acqtest_T1w.nii.gz',
                    'Run': '', 'Ce': '', 'Rec': '', 'Folder': 'anat',
                    'Modality': 'T1w', 'Mod': ''
                    }
                },
            u'measurements': [u'anatomy_t1w'], u'type': u'nifti'}
        self.assertEqual(container, container_expected)

    def test_process_matching_templates_func(self):
        """ """
        # Define context
        context = {
            'container_type': 'file',
            'parent_container_type': 'acquisition',
            'project': None,
            'subject': {u'code': u'001'},
            'session': {u'label': u'sesTEST'},
            'acquisition': {u'label': u'acqTEST'},
            'file': {u'measurements': [u'functional'],
                    u'type': u'nifti'},
            'ext': '.nii.gz'
        }
        # Call function
        container = bidsify_flywheel.process_matching_templates(context)
        # Define expected container
        container_expected = {
            'info': {
                'BIDS': {
                    'Filename': u'sub-001_ses-sestest_acq-acqtest_bold.nii.gz',
                    'Folder': 'func', 'Task': '', 'Modality': 'bold',
                    'Rec': '', 'Run': '', 'Echo': ''
                    }
                },
            u'measurements': [u'functional'], u'type': u'nifti'}
        self.assertEqual(container, container_expected)

    def test_process_matching_templates_diff(self):
        """ """
        # Define context
        context = {
            'container_type': 'file',
            'parent_container_type': 'acquisition',
            'project': None,
            'subject': {u'code': u'001'},
            'session': {u'label': u'sesTEST'},
            'acquisition': {u'label': u'acqTEST'},
            'file': {u'measurements': [u'diffusion'],
                    u'type': u'nifti'},
            'ext': '.nii.gz'
        }
        # Call function
        container = bidsify_flywheel.process_matching_templates(context)
        # Define expected container
        container_expected = {
            'info': {
                'BIDS': {
                    'Filename': u'sub-001_ses-sestest_acq-acqtest_dwi.nii.gz',
                    'Folder': 'dwi', 'Run': ''
                    }
                },
            u'measurements': [u'diffusion'], u'type': u'nifti'}
        self.assertEqual(container, container_expected)

    def test_process_matching_templates_project_file(self):
        """ """
        # Define context
        context = {
            'container_type': 'file',
            'parent_container_type': 'project',
            'project': None,
            'subject': None,
            'session': None,
            'acquisition': None,
            'file': {u'measurements': [u'unknown'],
                    u'type': u'archive'},
            'ext': '.zip'
        }
        # Call function
        container = bidsify_flywheel.process_matching_templates(context)
        # Define expected container
        container_expected = {
            'info': {
                'BIDS': {
                    'Filename': '', 'Folder': ''
                    }
                },
            u'measurements': [u'unknown'], u'type': u'archive'}
        self.assertEqual(container, container_expected)



    """
    def test_process_matching_templates_project_file_multiple_measurements(self):
        """ """
        # TODO: figure out how to navigate this
        # Define context
        context = {
            'container_type': 'file',
            'parent_container_type': 'acquisition',
            'project': None,
            'subject': {u'code': u'001'},
            'session': {u'label': u'sesTEST'},
            'acquisition': {u'label': u'acqTEST'},
            'file': {
                u'measurements': [u'anatomy_t1w', u'anatomy_t2w'],
                u'type': u'nifti'
            },
            'ext': '.nii.gz'
        }
        # Call function
        container = bidsify_flywheel.process_matching_templates(context)
        self.assertTrue(False)
        self.assertTrue('info' in container)
    """



if __name__ == "__main__":

    unittest.main()
    run_module_suite()