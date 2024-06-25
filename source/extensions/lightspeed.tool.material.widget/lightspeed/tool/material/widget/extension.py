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

import carb
import omni.ext
import omni.kit.app
import omni.kit.window.toolbar

from .ui import MaterialButtonGroup


class LightspeedSetupExtension(omni.ext.IExt):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._material_tools = None

    def on_startup(self, ext_id):
        carb.log_info("[lightspeed.tool.material] Lightspeed Tool Material startup")
        toolbar = omni.kit.window.toolbar.toolbar.get_instance()
        # add material tools
        self._material_tools = MaterialButtonGroup()
        toolbar.add_widget(self._material_tools, 100)

    def on_shutdown(self):
        carb.log_info("[lightspeed.tool.material] Lightspeed Tool Material startup")
        # cleanup the toolbar
        toolbar = omni.kit.window.toolbar.toolbar.get_instance()
        if toolbar and self._material_tools:
            toolbar.remove_widget(self._material_tools)
        self._material_tools = None
