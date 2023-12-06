#!/usr/bin/bash

pacman -Sy
pacman -S --noconfirm git ${MINGW_PACKAGE_PREFIX}-{python,gtk4,python-gobject,python-pip}
