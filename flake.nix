{
  description = "A TransGG bot to give roles out on questions";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs =
    { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [ (pkgs.python3.withPackages (pyPkgs: [ pyPkgs.discordpy ])) ];
        };
        formatter = pkgs.nixfmt-rfc-style;
      }
    );
}
