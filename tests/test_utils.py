import jsonschema
import os
import shutil
import unittest

import flywheel
from supporting_files import utils

class UtilsTestCases(unittest.TestCase):

    def setUp(self):
        # Define testdir
        self.testdir = 'testdir'

    def tearDown(self):
        # Cleanup 'testdir', if present
        if os.path.exists(self.testdir):
            shutil.rmtree(self.testdir)

    def test_get_extension_nii(self):
        """ Get extension if .nii """
        fname = 'T1w.nii'
        ext = utils.get_extension(fname)
        self.assertEqual('.nii', ext)

    def test_get_extension_niigz(self):
        """ Get extension if .nii.gz """
        fname = 'T1w.nii.gz'
        ext = utils.get_extension(fname)
        self.assertEqual('.nii.gz', ext)

    def test_get_extension_tsv(self):
        """ Get extension if .tsv """
        fname = 'T1w.tsv'
        ext = utils.get_extension(fname)
        self.assertEqual('.tsv', ext)

    def test_get_extension_none(self):
        """ Assert function returns None if no extension present """
        fname = 'sub-01_T1w'
        ext = utils.get_extension(fname)
        self.assertIsNone(ext)

    def test_valid_namespace_valid(self):
        """ Assert function does not raise error when a VALID namespace passed """
        from supporting_files.templates import namespace
        utils.valid_namespace(namespace)

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
                        "Task": {"type": "string", "label": "Task Label", "default": ""}
                        },
                    "required": ["Task"]
                    }
                ]
            }

        # Assert ValidationError raised
        with self.assertRaises(jsonschema.ValidationError) as err:
            utils.valid_namespace(invalid_namespace)

    def test_valid_namespace_invalid2(self):
        """ Assert function returns False when a INVALID namespace passed.

        Namespace is invalid because it does not contain the property 'container_type'

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
                        "Task": {"type": "string", "label": "Task Label", "default": ""}
                        }
                    }
                ]
            }

        # Assert ValidationError raised
        with self.assertRaises(jsonschema.ValidationError) as err:
            utils.valid_namespace(invalid_namespace)


    def test_validate_project_label_invalidproject(self):
        """ Get project that does not exist. Assert function returns None.

        NOTE: the environment variable $APIKEY needs to be defined with users API key
        """
        client = flywheel.Flywheel(os.environ['APIKEY'])
        label = 'doesnotexistdoesnotexistdoesnotexist89479587349'
        with self.assertRaises(SystemExit):
            utils.validate_project_label(client, label)

    def test_validate_project_label_validproject(self):
        """ Get project that DOES exist. Assert function returns the project.

        NOTE: the environment variable $APIKEY needs to be defined with users API key

        """
        client = flywheel.Flywheel(os.environ['APIKEY'])
        label = 'Project Name'
        project_id = utils.validate_project_label(client, label)
        project_id_expected = u'58175ad3de26e00012c69306'
        self.assertEqual(project_id, project_id_expected)


if __name__ == "__main__":

    unittest.main()
    run_module_suite()
