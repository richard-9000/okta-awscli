#!/bin/bash
# Used after building, bundle the egg for a quick install shell script.

set -e

usage () {
  echo "usage: bundle.sh <your_okta_org>"
  exit 1
}

[ "$1" == "" ] && usage

(

# Print the script header
cat <<MAGIC
#!/bin/bash
cat > ~/.okta-aws <<EOF
[default]
base-url = $1.okta.com
EOF
flag="-d"; [ \`uname\` == "Linux" ] || flag="-D"
base64 \$flag > $1_install.egg <<EOFEGGFILE
MAGIC

# Print base64 of the egg file
cat `ls -x1 dist/*.egg|tail -1` | base64

# Print the script footer
cat <<MAGIC
EOFEGGFILE
python3 -m easy_install $1_install.egg
rm $1_install.egg
MAGIC

) > "$1_okta_awscli_install.sh"
