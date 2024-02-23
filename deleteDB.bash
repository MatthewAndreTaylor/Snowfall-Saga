# Remove all *.db files fmo currecnt directory recurvsivley
# Usage: ./deleteDB.bash

find . -name "*.db" -exec rm -f {} \;
