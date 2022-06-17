#!/usr/bin/env bash

mkdir /home/abc/data
curl -L -O https://github.com/TomographicImaging/CIL-Data/raw/5affe9b1c3bd20b28aee7756aa968d7c2a9eeff4/head.mha
mv head.mha /home/abc/data