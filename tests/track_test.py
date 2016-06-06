from unittest import TestCase

from esrally import track, exceptions, config


class TrackRepositoryTests(TestCase):
    def test_versions_parses_correct_version_string(self):
        self.assertEquals(["5.0.3", "5.0", "5"], track.TrackRepository.versions("5.0.3"))
        self.assertEquals(["5.0.0-SNAPSHOT", "5.0.0", "5.0", "5"], track.TrackRepository.versions("5.0.0-SNAPSHOT"))
        self.assertEquals(["10.3.63", "10.3", "10"], track.TrackRepository.versions("10.3.63"))

    def test_versions_rejects_invalid_version_strings(self):
        with self.assertRaises(exceptions.InvalidSyntax) as ctx:
            track.TrackRepository.versions("5.0.0a-SNAPSHOT")
        self.assertEqual("version string '5.0.0a-SNAPSHOT' does not conform to pattern '^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$'"
                         , ctx.exception.args[0])


class TrackReaderTests(TestCase):
    def test_missing_description_raises_syntax_error(self):
        track_specification = {
            "meta": {
                "description": "unittest track"
            }
        }
        reader = track.TrackReader()
        with self.assertRaises(track.TrackSyntaxError) as ctx:
            reader("unittest", track_specification, "/mappings", "/data")
        self.assertEqual("Track 'unittest' is invalid. Mandatory element 'meta.short-description' is missing.", ctx.exception.args[0])

    def test_parse_valid_track_specification(self):
        track_specification = {
            "meta": {
                "short-description": "short description for unit test",
                "description": "longer description of this track for unit test",
                "data-url": "https://localhost/data"
            },
            "indices": [
                {
                    "name": "index-historical",
                    "types": [
                        {
                            "name": "main",
                            "documents": "documents-main.json.bz2",
                            "document-count": 10,
                            "compressed-bytes": 100,
                            "uncompressed-bytes": 10000,
                            "mapping": "main-type-mappings.json"
                        },
                        {
                            "name": "secondary",
                            "documents": "documents-secondary.json.bz2",
                            "document-count": 20,
                            "compressed-bytes": 200,
                            "uncompressed-bytes": 20000,
                            "mapping": "secondary-type-mappings.json"
                        }

                    ]
                }
            ],
            "operations": [
                {
                    "name": "index-append",
                    "type": "index",
                    "index-settings": {},
                    "clients": {
                        "count": 8
                    },
                    "bulk-size": 5000,
                    "force-merge": False
                }
            ],
            "challenges": [
                {
                    "name": "default-challenge",
                    "description": "Default challenge",
                    "schedule": [
                        "index-append"
                    ]
                }

            ]
        }
        reader = track.TrackReader()
        resulting_track = reader("unittest", track_specification, "/mappings", "/data")
        self.assertEqual("unittest", resulting_track.name)
        self.assertEqual("short description for unit test", resulting_track.short_description)
        self.assertEqual("longer description of this track for unit test", resulting_track.description)
        self.assertEqual(1, len(resulting_track.indices))
        self.assertEqual("index-historical", resulting_track.indices[0].name)
        self.assertEqual(2, len(resulting_track.indices[0].types))
        self.assertEqual("main", resulting_track.indices[0].types[0].name)
        self.assertEqual("/data/documents-main.json.bz2", resulting_track.indices[0].types[0].document_archive)
        self.assertEqual("/data/documents-main.json", resulting_track.indices[0].types[0].document_file)
        self.assertEqual("/mappings/main-type-mappings.json", resulting_track.indices[0].types[0].mapping_file)
        self.assertEqual("secondary", resulting_track.indices[0].types[1].name)
        self.assertEqual(1, len(resulting_track.challenges))
        self.assertEqual("default-challenge", resulting_track.challenges[0].name)
