#!/bin/bash
docker build -t task_manager .
docker run -d -p 5000:5000 --name task_manager_container task_manager