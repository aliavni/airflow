 .. Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

 ..   http://www.apache.org/licenses/LICENSE-2.0

 .. Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.


Setup and develop using GitHub Codespaces
#########################################

1. Go to |airflow_github| and fork the project.

   .. |airflow_github| raw:: html

     <a href="https://github.com/apache/airflow/" target="_blank">https://github.com/apache/airflow/</a>

   .. raw:: html

     <div align="center" style="padding-bottom:10px">
       <img src="images/airflow_fork.png"
            alt="Forking Apache Airflow project">
     </div>

2. From your fork create a codespace by clicking this
   👉 |codespace|

   .. |codespace| image:: https://github.com/codespaces/badge.svg
       :target: https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=33884891
       :alt: Open in GitHub Codespaces

3. Once the codespace starts your terminal should already be in the ``Breeze`` environment and you should
   be able to edit and run the tests in VS Code interface.

4. You can use `Quick start guide for Visual Studio Code <contributors_quick_start_vscode.rst>`_ for details
   as Codespaces use Visual Studio Code as interface.


Follow the `Quick start <../03_contributors_quick_start.rst>`_ for typical development tasks.
