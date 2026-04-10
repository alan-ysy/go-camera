{
  description = "Python devshell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        python = pkgs.python312; # change to python311, python310, etc.
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            python
            python.pkgs.pip
            python.pkgs.ipython
            python.pkgs.black
            python.pkgs.pytest
          ];

          shellHook = ''
            echo "Python devshell ready"
            echo "Python version: $(python --version)"
          '';
        };
      });
}
