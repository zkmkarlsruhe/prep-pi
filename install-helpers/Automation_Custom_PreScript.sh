#!/bin/bash

# Copyright © 2025 Hugo Dünger -  ZKM | Zentrum für Kunst und Medien Karlsruhe
# Lizenziert unter der MIT-Lizenz

# Pre-answer "yes" to prompts from iptables-persistent during its installation.
# This ensures the installation doesn't hang waiting for user input.
debconf-set-selections <<< "iptables-persistent iptables-persistent/autosave_v4 boolean true"
debconf-set-selections <<< "iptables-persistent iptables-persistent/autosave_v6 boolean true"