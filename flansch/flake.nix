{
  description = "Protobuf + Go gRPC development environment for flansch component of bibliophage";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            name = "flansch-protobuf-go-grpc-shell";

            buildInputs = with pkgs; [
              go
              protobuf
              protoc-gen-go
              protoc-gen-go-grpc
            ];
          };
        }
      );
    };
}
