{
  description = "GoVision - Raspberry Pi Go Board Scanner";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
        python = pkgs.python312;
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            # System libraries OpenCV needs
            pkgs.libcamera
            pkgs.libjpeg
            pkgs.zlib

            # Python + project dependencies
            python
            python.pkgs.pip
            python.pkgs.ipython
            python.pkgs.black
            python.pkgs.pytest
            python.pkgs.numpy
            python.pkgs.opencv4
            python.pkgs.pillow
            python.pkgs.flask
            python.pkgs.pyyaml
            # python.pkgs.tflite-runtime
          ];

          shellHook = ''
            echo "GoVision devshell ready"
            echo "Python: $(python --version)"
            echo "OpenCV: $(python -c 'import cv2; print(cv2.__version__)')"
          '';
        };
      });
}
