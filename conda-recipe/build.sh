mkdir "$SRC_DIR/ccpiviewer"
cp -r "$RECIPE_DIR/.." "$SRC_DIR/ccpiviewer"

cd $SRC_DIR/ccpiviewer

$PYTHON setup.py install


