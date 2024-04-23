#!/bin/sh

# remove soccer-simulation-proxy directory if exists
rm -rf soccer-simulation-proxy

# remove rcssserver directory if exists
rm -rf rcssserver

# download soccer simulation server App Image
mkdir rcssserver

wget $(curl -s https://api.github.com/repos/clsframework/rcssserver/releases/latest | grep -oP '"browser_download_url": "\K(.*rcssserver-x86_64-.*\.AppImage)' | head -n 1)

mv rcssserver-x86_64-*.AppImage rcssserver/rcssserver-x86_64.AppImage

# download soccer simulation proxy
rm -rf soccer-simulation-proxy.tar.gz

wget $(curl -s "https://api.github.com/repos/clsframework/soccer-simulation-proxy/releases/latest" | grep -oP '"browser_download_url": "\K[^"]*' | grep "soccer-simulation-proxy.tar.gz")

tar -xvf soccer-simulation-proxy.tar.gz

