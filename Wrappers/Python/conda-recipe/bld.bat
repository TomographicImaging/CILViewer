
xcopy /e "%RECIPE_DIR%\.." "%SRC_DIR%"

%PYTHON% pip install .
if errorlevel 1 exit 1
