# shell.nix
# SPDX-License-Identifier: MIT
# Uses the system's nixpkgs channel without pinning a specific version.
# Optimized to use the binary cache, avoiding lengthy compilations.
{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python3.withPackages (ps: [
    ps.pymupdf
    ps.pytest
  ]);
in
pkgs.mkShell {
  packages = [
    # The Python interpreter
    python

    # System tools
    pkgs.qpdf           # For PDF manipulation (extracting pages)
  ];
}
