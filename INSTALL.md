# Electrum Kivy User Guide

## Install dependencies
[Kivy](http://kivy.org/docs/installation/installation.html#ubuntu)
`http://kivy.org/docs/installation/installation.html#ubuntu`

## Checkout Kivy branch
    git clone https://github.com/linhlarry/electrum
    cd electrum
    git checkout kivy

## Generate resource file (once)
    sudo apt-get install pyqt4-dev-tools
    pyrcc4 icons.qrc -o gui/icons_rc.py

## Run program
    python electrum_kivy

## Clean wallet data
    rm -f ~/.electrum/*
