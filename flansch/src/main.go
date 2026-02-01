package main

import (
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	"lichturm.de/bibliophage/flansch/arcadedb"
	pb "lichturm.de/bibliophage/flansch/bibliophage/bibliophage/v1alpha3"
	"lichturm.de/bibliophage/flansch/config"
	"lichturm.de/bibliophage/flansch/server"
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

	// Connect to ArcadeDB
	arcadeAddr := fmt.Sprintf("%s:%d", cfg.ArcadeDB.Host, cfg.ArcadeDB.Port)
	conn, err := grpc.NewClient(arcadeAddr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("Failed to connect to ArcadeDB at %s: %v", arcadeAddr, err)
	}
	defer conn.Close()

	arcadeClient := arcadedb.NewArcadeDbServiceClient(conn)

	// Create the GraphService
	graphService := server.NewGraphService(
		arcadeClient,
		cfg.ArcadeDB.Database,
		cfg.ArcadeDB.Username,
		cfg.ArcadeDB.Password,
	)

	// Start gRPC server
	listenAddr := fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.Port)
	lis, err := net.Listen("tcp", listenAddr)
	if err != nil {
		log.Fatalf("Failed to listen on %s: %v", listenAddr, err)
	}

	grpcServer := grpc.NewServer()
	pb.RegisterGraphServiceServer(grpcServer, graphService)

	// Handle graceful shutdown
	go func() {
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
		<-sigCh
		fmt.Fprintf(os.Stderr, "\nShutting down...\n")
		grpcServer.GracefulStop()
	}()

	fmt.Fprintf(os.Stderr, "Flansch listening on %s\n", listenAddr)
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}
