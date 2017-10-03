with import (builtins.fetchTarball "https://d3g5gsiof5omrk.cloudfront.net/nixos/unstable-small/nixos-18.03pre114607.dd74844fff/nixexprs.tar.xz") {};

stdenv.mkDerivation rec {
  name = "env";
  env = buildEnv { name = name; paths = buildInputs; };

  buildInputs = [
    python2
    python2Packages.lxml
    python2Packages.pillow
    python2Packages.tkinter
    python2Packages.pyusb
    inkscape
  ];
}
