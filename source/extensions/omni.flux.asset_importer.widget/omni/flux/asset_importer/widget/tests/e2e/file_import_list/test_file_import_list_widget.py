"""
* SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
* SPDX-License-Identifier: Apache-2.0
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
* https://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from unittest.mock import PropertyMock, patch

import omni.kit
import omni.kit.test
import omni.usd
from carb.input import KeyboardInput
from omni import ui
from omni.flux.asset_importer.widget.file_import_list import (
    FileImportListDelegate,
    FileImportListModel,
    FileImportListWidget,
)
from omni.flux.utils.common.omni_url import OmniUrl
from omni.kit import ui_test
from omni.kit.test_suite.helpers import arrange_windows, wait_stage_loading


class TestFileImportListWidget(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self.stage = omni.usd.get_context().get_stage()
        self.temp_dir = TemporaryDirectory()

    # After running each test
    async def tearDown(self):
        await wait_stage_loading()
        if omni.usd.get_context().get_stage():
            await omni.usd.get_context().close_stage_async()
        self.temp_dir.cleanup()
        self.stage = None
        self.temp_dir = None

    async def __setup_widget(
        self, model: Optional[FileImportListModel] = None, delegate: Optional[FileImportListDelegate] = None
    ):
        await arrange_windows(topleft_window="Stage")

        window = ui.Window("TestFileImportListWindow", height=400, width=400)
        with window.frame:
            FileImportListWidget(model=model, delegate=delegate)

        await ui_test.human_delay()

        return window

    async def test_tree_should_show_all_items_and_action_buttons(self):
        # Setup the test
        model = FileImportListModel()
        delegate = FileImportListDelegate()

        base_path = Path(self.temp_dir.name)
        items = [base_path / "0.usda", base_path / "1.usda", base_path / "2.usda"]
        for item in items:
            item.touch()

        model.refresh(items)

        window = await self.__setup_widget(model=model, delegate=delegate)  # Keep in memory during test

        # Start the test
        file_items = ui_test.find_all(f"{window.title}//Frame/**/Label[*].identifier=='file_path'")
        add_item = ui_test.find(f"{window.title}//Frame/**/Button[*].identifier=='add_file'")
        remove_item = ui_test.find(f"{window.title}//Frame/**/Button[*].identifier=='remove_file'")

        # Make sure everything is rendered correctly
        self.assertEqual(len(items), len(file_items))
        self.assertIsNotNone(add_item)
        self.assertIsNotNone(remove_item)

        for file_item_label in file_items:
            self.assertEqual(file_item_label.widget.style_type_name_override, "PropertiesPaneSectionTreeItem")

    async def test_wrong_file_should_be_red(self):
        # Arrange
        model = FileImportListModel()
        delegate = FileImportListDelegate()

        with (
            patch("omni.flux.asset_importer.widget.common.items.ImportItem.is_valid") as mock_exist,
            patch(
                "omni.flux.asset_importer.widget.listener.FileListener.WAIT_TIME", new_callable=PropertyMock
            ) as mock_wait_time,
        ):
            mock_wait_time.return_value = 0.1
            mock_exist.return_value = (False, "")

            # Act
            base_path = Path(self.temp_dir.name)
            items = [base_path / "0.usda", base_path / "1.usda", base_path / "2.usda"]
            for item in items:
                item.touch()

            model.refresh(items)

            window = await self.__setup_widget(model=model, delegate=delegate)  # Keep in memory during test

            # Asset
            file_item_labels = ui_test.find_all(f"{window.title}//Frame/**/Label[*].identifier=='file_path'")
            self.assertEqual(len(items), len(file_item_labels))

            for file_item_label in file_item_labels:
                self.assertEqual(file_item_label.widget.style_type_name_override, "PropertiesPaneSectionTreeItemError")

    async def test_add_should_open_file_picker_and_add_item(self):
        # Setup the test
        model = FileImportListModel()
        delegate = FileImportListDelegate()

        base_path = Path(self.temp_dir.name)
        items = [base_path / "0.usda", base_path / "1.usda", base_path / "2.usda"]
        for item in items:
            item.touch()

        urls = [OmniUrl(item) for item in items]

        new_item = base_path / "3.usda"
        new_item.touch()

        model.refresh(urls)

        window = await self.__setup_widget(model=model, delegate=delegate)  # Keep in memory during test

        # Start the test
        file_items = ui_test.find_all(f"{window.title}//Frame/**/Label[*].identifier=='file_path'")
        add_item = ui_test.find(f"{window.title}//Frame/**/Button[*].identifier=='add_file'")

        # Make sure we have the required items
        self.assertEqual(len(urls), len(file_items))
        self.assertIsNotNone(add_item)

        await add_item.click()
        await ui_test.human_delay()

        # File Picker
        window_name = "Select a file to import"
        import_button = ui_test.find(f"{window_name}//Frame/**/Button[*].text=='Import'")
        dir_path_field = ui_test.find(f"{window_name}//Frame/**/StringField[*].identifier=='filepicker_directory_path'")
        file_name_field = ui_test.find(f"{window_name}//Frame/**/StringField[*].style_type_name_override=='Field'")

        self.assertIsNotNone(import_button)
        self.assertIsNotNone(dir_path_field)
        self.assertIsNotNone(file_name_field)

        # It takes a while for the tree to update
        await ui_test.human_delay(50)
        await dir_path_field.input(str(new_item.parent.resolve()), end_key=KeyboardInput.ENTER)
        await ui_test.human_delay(50)

        await file_name_field.input(str(new_item.name), end_key=KeyboardInput.DOWN)
        await ui_test.human_delay()

        # Make sure we are selecting the right file
        self.assertEqual(
            str(new_item.parent.resolve()), dir_path_field.model._field.model.get_value_as_string()  # noqa PLW0212
        )
        self.assertEqual(str(new_item.name), file_name_field.model.get_value_as_string())

        await import_button.click()

        await ui_test.human_delay()

        file_items = ui_test.find_all(f"{window.title}//Frame/**/Label[*].identifier=='file_path'")

        # A new file path should be added
        self.assertEqual(len(urls) + 1, len(file_items))
        self.assertEqual(new_item.resolve().as_posix(), Path(file_items[-1].widget.text).as_posix())

    async def test_remove_should_validate_selection_and_remove_items_if_valid(self):
        # Setup the test
        model = FileImportListModel()
        delegate = FileImportListDelegate()

        base_path = Path(self.temp_dir.name)
        items = [base_path / "0.usda", base_path / "1.usda", base_path / "2.usda"]
        for item in items:
            item.touch()

        model.refresh(items)

        window = await self.__setup_widget(model=model, delegate=delegate)  # Keep in memory during test

        # Start the test
        file_items = ui_test.find_all(f"{window.title}//Frame/**/Label[*].identifier=='file_path'")
        remove_item = ui_test.find(f"{window.title}//Frame/**/Button[*].identifier=='remove_file'")

        # Make sure everything is rendered correctly
        self.assertEqual(len(items), len(file_items))
        self.assertIsNotNone(remove_item)

        await remove_item.click()

        # Should remove nothing
        file_items = ui_test.find_all(f"{window.title}//Frame/**/Label[*].identifier=='file_path'")
        self.assertEqual(len(items), len(file_items))

        await file_items[0].click()
        await ui_test.human_delay()

        await remove_item.click()

        # Should remove the first item
        file_items = ui_test.find_all(f"{window.title}//Frame/**/Label[*].identifier=='file_path'")
        self.assertEqual(len(items) - 1, len(file_items))

        await file_items[0].click()
        await ui_test.human_delay()

        await remove_item.click()

        # Should remove the second item
        file_items = ui_test.find_all(f"{window.title}//Frame/**/Label[*].identifier=='file_path'")
        self.assertEqual(len(items) - 2, len(file_items))

        await file_items[0].click()
        await ui_test.human_delay()

        await remove_item.click()

        # Should do nothing as the validation should not allow 0 items to be left
        file_items = ui_test.find_all(f"{window.title}//Frame/**/Label[*].identifier=='file_path'")
        self.assertEqual(1, len(file_items))
