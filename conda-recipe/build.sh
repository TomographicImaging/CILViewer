mkdir "$SRC_DIR/ccpi"
cp -r "$RECIPE_DIR/../.." "$SRC_DIR/ccpi"

cd $SRC_DIR/ccpi/Python

$PYTHON setup.py build_ext
$PYTHON setup.py install


