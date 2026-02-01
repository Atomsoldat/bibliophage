package server

import (
	"context"
	"fmt"

	"google.golang.org/protobuf/types/known/structpb"

	"lichturm.de/bibliophage/flansch/arcadedb"
	pb "lichturm.de/bibliophage/flansch/bibliophage/bibliophage/v1alpha3"
)

// GraphService implements the bibliophage GraphService by proxying to ArcadeDB.
type GraphService struct {
	pb.UnimplementedGraphServiceServer

	arcade   arcadedb.ArcadeDbServiceClient
	database string
	creds    *arcadedb.DatabaseCredentials
}

// NewGraphService creates a GraphService that proxies to the given ArcadeDB client.
func NewGraphService(client arcadedb.ArcadeDbServiceClient, database, username, password string) *GraphService {
	return &GraphService{
		arcade:   client,
		database: database,
		creds: &arcadedb.DatabaseCredentials{
			Username: username,
			Password: password,
		},
	}
}

func (s *GraphService) CreateNode(ctx context.Context, req *pb.CreateNodeRequest) (*pb.CreateNodeResponse, error) {
	props, err := structToGrpcProperties(req.Properties)
	if err != nil {
		return &pb.CreateNodeResponse{
			Success: false,
			Message: fmt.Sprintf("invalid properties: %v", err),
		}, nil
	}

	resp, err := s.arcade.CreateRecord(ctx, &arcadedb.CreateRecordRequest{
		Database:    s.database,
		Credentials: s.creds,
		Type:        req.TypeId,
		Record: &arcadedb.GrpcRecord{
			Type:       req.TypeId,
			Properties: props,
		},
	})
	if err != nil {
		return &pb.CreateNodeResponse{
			Success: false,
			Message: err.Error(),
		}, nil
	}

	return &pb.CreateNodeResponse{
		Success: true,
		Message: "node created",
		Node: &pb.Node{
			Id:         resp.Rid,
			TypeId:     req.TypeId,
			Properties: req.Properties,
		},
	}, nil
}

func (s *GraphService) CreateEdge(ctx context.Context, req *pb.CreateEdgeRequest) (*pb.CreateEdgeResponse, error) {
	// Edges in ArcadeDB are stored as records with @in and @out links
	props := map[string]*arcadedb.GrpcValue{
		"@out": {Kind: &arcadedb.GrpcValue_StringValue{StringValue: req.SourceNodeId}},
		"@in":  {Kind: &arcadedb.GrpcValue_StringValue{StringValue: req.TargetNodeId}},
	}

	resp, err := s.arcade.CreateRecord(ctx, &arcadedb.CreateRecordRequest{
		Database:    s.database,
		Credentials: s.creds,
		Type:        req.Relationship,
		Record: &arcadedb.GrpcRecord{
			Type:       req.Relationship,
			Properties: props,
		},
	})
	if err != nil {
		return &pb.CreateEdgeResponse{
			Success: false,
			Message: err.Error(),
		}, nil
	}

	return &pb.CreateEdgeResponse{
		Success: true,
		Message: "edge created",
		Edge: &pb.Edge{
			Id:           resp.Rid,
			Relationship: req.Relationship,
			Directed:     req.Directed,
			NodeA:        req.SourceNodeId,
			NodeB:        req.TargetNodeId,
		},
	}, nil
}

func (s *GraphService) DeleteNode(ctx context.Context, req *pb.DeleteNodeRequest) (*pb.DeleteNodeResponse, error) {
	_, err := s.arcade.DeleteRecord(ctx, &arcadedb.DeleteRecordRequest{
		Database:    s.database,
		Credentials: s.creds,
		Rid:         req.Id,
	})
	if err != nil {
		return &pb.DeleteNodeResponse{
			Success: false,
			Message: err.Error(),
		}, nil
	}

	return &pb.DeleteNodeResponse{
		Success: true,
		Message: "node deleted",
	}, nil
}

func (s *GraphService) DeleteEdge(ctx context.Context, req *pb.DeleteEdgeRequest) (*pb.DeleteEdgeResponse, error) {
	_, err := s.arcade.DeleteRecord(ctx, &arcadedb.DeleteRecordRequest{
		Database:    s.database,
		Credentials: s.creds,
		Rid:         req.Id,
	})
	if err != nil {
		return &pb.DeleteEdgeResponse{
			Success: false,
			Message: err.Error(),
		}, nil
	}

	return &pb.DeleteEdgeResponse{
		Success: true,
		Message: "edge deleted",
	}, nil
}

// structToGrpcProperties converts a protobuf Struct to ArcadeDB GrpcValue properties.
func structToGrpcProperties(s *structpb.Struct) (map[string]*arcadedb.GrpcValue, error) {
	if s == nil {
		return nil, nil
	}

	props := make(map[string]*arcadedb.GrpcValue, len(s.Fields))
	for key, val := range s.Fields {
		gv, err := valueToGrpcValue(val)
		if err != nil {
			return nil, fmt.Errorf("field %q: %w", key, err)
		}
		props[key] = gv
	}
	return props, nil
}

// valueToGrpcValue converts a protobuf Value to an ArcadeDB GrpcValue.
func valueToGrpcValue(v *structpb.Value) (*arcadedb.GrpcValue, error) {
	switch k := v.Kind.(type) {
	case *structpb.Value_NullValue:
		return &arcadedb.GrpcValue{}, nil
	case *structpb.Value_NumberValue:
		return &arcadedb.GrpcValue{Kind: &arcadedb.GrpcValue_DoubleValue{DoubleValue: k.NumberValue}}, nil
	case *structpb.Value_StringValue:
		return &arcadedb.GrpcValue{Kind: &arcadedb.GrpcValue_StringValue{StringValue: k.StringValue}}, nil
	case *structpb.Value_BoolValue:
		return &arcadedb.GrpcValue{Kind: &arcadedb.GrpcValue_BoolValue{BoolValue: k.BoolValue}}, nil
	case *structpb.Value_ListValue:
		items := make([]*arcadedb.GrpcValue, len(k.ListValue.Values))
		for i, item := range k.ListValue.Values {
			gv, err := valueToGrpcValue(item)
			if err != nil {
				return nil, err
			}
			items[i] = gv
		}
		return &arcadedb.GrpcValue{Kind: &arcadedb.GrpcValue_ListValue{ListValue: &arcadedb.GrpcList{Values: items}}}, nil
	case *structpb.Value_StructValue:
		fields, err := structToGrpcProperties(k.StructValue)
		if err != nil {
			return nil, err
		}
		return &arcadedb.GrpcValue{Kind: &arcadedb.GrpcValue_EmbeddedValue{EmbeddedValue: &arcadedb.GrpcEmbedded{Fields: fields}}}, nil
	default:
		return nil, fmt.Errorf("unsupported value type: %T", v.Kind)
	}
}
