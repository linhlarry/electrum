# Build APK 

- Install dependencies. It is recommended to use the VirtualBox Image.

[http://python-for-android.readthedocs.org/en/latest/prerequisites/]
(http://python-for-android.readthedocs.org/en/latest/prerequisites/)

- Copy/Checkout source code to the VirtualBox Image, i.e. `~/electrum`

- Jump to `~/android/python-for-android`

- Comment all lines in `src/blacklist.txt` to inject as many libraries as possible

- Update the recipe of Kivy in `recipes/kivy/recipe.sh` with specific stable release, i.e. `v1.7.0`

`URL_kivy=https://github.com/kivy/kivy/archive/1.7.0.zip`

- Compile the necessary packages, `kivy` should be end of list.

`./distribute.sh -m "openssl kivy"`

- [Optional] Compile all packages to debug (list gotten from recipe dir)

```
    ./distribute.sh -m "android audiostream cymunk docutils ffmpeg \
                        hostpython jpeg libxml2 libxslt lxml mysql_connector \
                        numpy openssl pil png pyasn1 pycrypto pygame pyjnius \
                        pyopenssl pyqrcode python sdl setuptools sqlite3 \
                        twisted txws wokkel zope kivy"
```

- Jump to `dist/default` and build it

```
    ./build.py \
        --dir ~/electrum/ \
        --package com.kivy.electrum \
        --name "Electrum Kivy" \
        --permission INTERNET \
        --version 1.0.0 debug |& tee /tmp/log.txt
```

- You're done! Now try the generated APK on real device.

