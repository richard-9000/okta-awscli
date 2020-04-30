#!/bin/bash
# Used after building, bundle the whl for a quick install shell script.

set -e

usage () {
  echo "usage: bundle.sh <your_okta_org>"
  exit 1
}

[ "$1" == "" ] && usage

(

lastbuild=`cd dist && ls -x1 *.whl|tail -1`

# Print the script header
cat <<MAGIC
#!/bin/bash
set -e
cat > ~/.okta-aws <<EOF
[default]
base-url = $1.okta.com
EOF
flag="-d"; [ \`uname\` == "Linux" ] || flag="-D"
base64 \$flag > "$lastbuild" <<EOFWHLFILE
MAGIC

# Print base64 of the whl file
cat "dist/$lastbuild" | base64

# Print the script footer
cat <<MAGIC
EOFWHLFILE
if [ \`id -un\` = "root" ]; then
  python3 -m pip install $lastbuild
else
  export PYTHONUSERBASE=~/.local/
  python3 -m pip install --user $lastbuild
  cat <<'INSTALLMSG'
The okta aws cli has been installed in your home directory, and can
be run with the following command:

  ~/.local/bin/okta-awscli -l

For convenience, add the following line to your .bash_profile or .bashrc:

PATH="\$PATH:~/.local/bin"

INSTALLMSG
fi
rm $lastbuild
MAGIC

) > "$1_okta_awscli_install.sh"
