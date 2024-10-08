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

import omni.usd
from lightspeed.layer_manager.core import LayerManagerCore as _LayerManagerCore
from lightspeed.layer_manager.core.data_models import LayerType
from lightspeed.trex.components_pane.stagecraft.models import create_all_items as _create_all_items
from omni.flux.tree_panel.widget import PanelOutlinerWidget as _PanelOutlinerWidget
from omni.flux.tree_panel.widget.tree.model import Model as _Model
from omni.flux.utils.common import reset_default_attrs as _reset_default_attrs
from omni.flux.utils.common.decorators import ignore_function_decorator as _ignore_function_decorator
from omni.flux.utils.common.decorators import sandwich_attrs_function_decorator as _sandwich_attrs_function_decorator


class SetupUI:

    DEFAULT_TITLE = "Untitled project"

    def __init__(self, context_name: str):
        """Nvidia StageCraft Components Pane"""

        self._default_attr = {
            "_ui": None,
            "_items": None,
            "_model": None,
            "_layer_manager": None,
            "_sub_stage_event": None,
            "_sub_title_updated": None,
        }
        for attr, value in self._default_attr.items():
            setattr(self, attr, value)

        self._from_user = False
        self.__init_title = False
        self._context = omni.usd.get_context(context_name)
        self._layer_manager = _LayerManagerCore(context_name=context_name)

        self._sub_stage_event = self._context.get_stage_event_stream().create_subscription_to_pop(
            self.__on_stage_event, name="StageChanged"
        )

        self._items = _create_all_items()
        self._model = _Model()
        self._model.set_items(self._items)
        self._ui = _PanelOutlinerWidget(tree_model=self._model)  # hold or crash
        self._ui.set_title(self.DEFAULT_TITLE)

        self._sub_title_updated = self._ui.subscribe_title_updated(self._on_title_updated)

    def __on_stage_event(self, event):
        if event.type in [
            int(omni.usd.StageEventType.CLOSED),
            int(omni.usd.StageEventType.OPENED),
            int(omni.usd.StageEventType.SAVED),
            int(omni.usd.StageEventType.ASSETS_LOADED),
        ]:
            self.refresh()

    def get_ui_widget(self):
        return self._ui

    def get_model(self):
        return self._model

    @_sandwich_attrs_function_decorator(attrs=["_from_user"])
    def _on_title_updated(self, title: str):
        self.refresh()

    @_ignore_function_decorator(attrs=["_ignore_refresh"])
    def refresh(self):
        capture_layer = self._layer_manager.get_layer(LayerType.capture)
        replacement_layer = self._layer_manager.get_layer(LayerType.replacement)
        if capture_layer and replacement_layer:
            for item in self._model.get_item_children(None):
                item.enabled = True
        else:
            # enable only the first one
            for i, item in enumerate(self._model.get_item_children(None)):
                item.enabled = i == 0

        # update the title
        stage_url = self._context.get_stage_url()
        stage = self._context.get_stage()
        root_layer = stage.GetRootLayer() if stage else None
        if stage_url and stage and root_layer and not root_layer.anonymous:
            self._ui.set_title(Path(stage_url).stem)
        elif not self._from_user and not self.__init_title or self._ui.title_widget.text not in Path(stage_url).stem:
            self.__init_title = True
            self._ui.set_title(self.DEFAULT_TITLE)

    def destroy(self):
        _reset_default_attrs(self)
