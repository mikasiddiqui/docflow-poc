import unittest

from src.mapper import map_to_structured_schema


class MapperTests(unittest.TestCase):
    def test_mapper_keeps_page_text_and_annotations_in_strict_shape(self) -> None:
        raw_extraction = {
            "source_file_name": "sample.pdf",
            "pages": [
                {
                    "page": 1,
                    "text": "Page 1 text",
                    "annotations": [
                        {
                            "kind": "annotation",
                            "content": "Reviewer comment",
                            "author": "Tom",
                            "subject": "Comment",
                        },
                        {
                            "kind": "markup",
                            "content": "Highlighted text",
                            "author": "",
                            "subject": "",
                        },
                    ],
                }
            ],
        }

        mapped = map_to_structured_schema(raw_extraction)

        self.assertEqual(mapped["source_file_name"], "sample.pdf")
        self.assertEqual(
            mapped["extracted_items"],
            [
                {
                    "page": 1,
                    "type": "text",
                    "content": "Page 1 text",
                    "author": "",
                    "subject": "",
                },
                {
                    "page": 1,
                    "type": "annotation",
                    "content": "Reviewer comment",
                    "author": "Tom",
                    "subject": "Comment",
                },
                {
                    "page": 1,
                    "type": "markup",
                    "content": "Highlighted text",
                    "author": "",
                    "subject": "",
                },
            ],
        )

    def test_mapper_skips_empty_annotation_content(self) -> None:
        raw_extraction = {
            "source_file_name": "sample.pdf",
            "pages": [
                {
                    "page": 2,
                    "text": "",
                    "annotations": [
                        {"kind": "annotation", "content": "   ", "author": "", "subject": ""},
                    ],
                }
            ],
        }

        mapped = map_to_structured_schema(raw_extraction)

        self.assertEqual(mapped["extracted_items"], [])


if __name__ == "__main__":
    unittest.main()
