#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 mengskysama
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys
import os
import logging
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
from dbtransfer import DbTransfer
import config

def handler_SIGQUIT():
    return

def main():
    level = config.LOG_LEVEL
    logging.basicConfig(level=level,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    time.sleep(1)
    DbTransfer.thread_db()

    while True:
        time.sleep(100)


if __name__ == '__main__':
    main()
