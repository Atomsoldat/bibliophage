package main

import (
	"fmt"
	"log"
	"os"

	"lichturm.de/bibliophage/flansch/config"
)

func main() {
	cfg, err := config.Load(os.Args[1:])
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	fmt.Fprintf(os.Stderr, "Flansch starting with config:\n")
	fmt.Fprintf(os.Stderr, "  Server: %s:%d\n", cfg.Server.Host, cfg.Server.Port)
	fmt.Fprintf(os.Stderr, "  ArcadeDB: %s:%d (database: %s)\n",
		cfg.ArcadeDB.Host, cfg.ArcadeDB.Port, cfg.ArcadeDB.Database)
	fmt.Fprintf(os.Stderr, "  Log level: %s\n", cfg.Log.Level)

	// TODO: Start gRPC server
}
