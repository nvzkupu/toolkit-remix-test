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
from omni.flux.service.factory import get_instance as _get_service_factory_instance

from .service import StageCraftService as _StageCraftService


class TrexStageCraftServiceExtension(omni.ext.IExt):
    def on_startup(self, _ext_id):
        carb.log_info("[lightspeed.trex.service.stagecraft] Startup")
        _get_service_factory_instance().register_services([_StageCraftService])

    def on_shutdown(self):
        carb.log_info("[lightspeed.trex.service.stagecraft] Shutdown")
        _get_service_factory_instance().unregister_services([_StageCraftService])
