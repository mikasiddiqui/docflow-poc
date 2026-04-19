import unittest

from src.trigger_service import _get_relative_path, _should_process_item


class TriggerServiceTests(unittest.TestCase):
    def test_should_process_pdf_inside_input_folder(self) -> None:
        item = {
            "name": "drawing.pdf",
            "file": {"mimeType": "application/pdf"},
            "parentReference": {"path": "/drives/abc/root:/Docflow/Input"},
        }

        self.assertTrue(_should_process_item(item, input_folder_path="Docflow/Input"))

    def test_should_not_process_non_pdf_or_removed_item(self) -> None:
        removed_item = {
            "@removed": {"reason": "deleted"},
            "name": "drawing.pdf",
            "file": {"mimeType": "application/pdf"},
            "parentReference": {"path": "/drives/abc/root:/Docflow/Input"},
        }
        non_pdf_item = {
            "name": "notes.docx",
            "file": {"mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
            "parentReference": {"path": "/drives/abc/root:/Docflow/Input"},
        }

        self.assertFalse(_should_process_item(removed_item, input_folder_path="Docflow/Input"))
        self.assertFalse(_should_process_item(non_pdf_item, input_folder_path="Docflow/Input"))

    def test_get_relative_path_builds_drive_relative_path(self) -> None:
        item = {
            "name": "drawing.pdf",
            "parentReference": {"path": "/drives/abc/root:/Docflow/Input/Subfolder"},
        }

        self.assertEqual(
            _get_relative_path(item),
            "Docflow/Input/Subfolder/drawing.pdf",
        )


if __name__ == "__main__":
    unittest.main()
