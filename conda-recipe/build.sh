if [ -z "$CIL_VERSION" ]; then
    echo "Need to set CIL_VERSION"
    exit 1
fi  
mkdir "$SRC_DIR/ccpiviewer"
cp -r "$RECIPE_DIR/.." "$SRC_DIR/ccpiviewer"

cd $SRC_DIR/ccpiviewer

$PYTHON setup.py install


