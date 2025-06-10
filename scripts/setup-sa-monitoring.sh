#!/bin/bash

oc create sa chaos-ai-monitor -n default

oc adm policy add-cluster-role-to-user cluster-monitoring-view -z chaos-ai-monitor

# Copy the contents of token command, this will be your PROMETHEUS_TOKEN value
oc create token chaos-ai-monitor
