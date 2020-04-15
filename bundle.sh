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
set -e
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
if [ \`id -un\` = "root" ]; then
  python3 -m easy_install lendingclub_install.egg
else
  python3 -m easy_install --user lendingclub_install.egg
  cat <<'INSTALLMSG'
The okta aws cli has been installed in your home directory, and can
be run with the following command:

  ~/.local/bin/okta-awscli -l

For convenience, add the following line to your .bash_profile or .bashrc:

PATH="\$PATH:~/.local/bin"

INSTALLMSG
fi
rm $1_install.egg
MAGIC

) > "$1_okta_awscli_install.sh"
