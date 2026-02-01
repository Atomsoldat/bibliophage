package server

import (
	"context"
	"errors"
	"testing"

	"google.golang.org/grpc"
	"google.golang.org/protobuf/types/known/structpb"

	"lichturm.de/bibliophage/flansch/arcadedb"
	pb "lichturm.de/bibliophage/flansch/bibliophage/bibliophage/v1alpha3"
)

// mockArcadeClient implements arcadedb.ArcadeDbServiceClient for testing.
type mockArcadeClient struct {
	createRecordFn func(ctx context.Context, req *arcadedb.CreateRecordRequest) (*arcadedb.CreateRecordResponse, error)
	deleteRecordFn func(ctx context.Context, req *arcadedb.DeleteRecordRequest) (*arcadedb.DeleteRecordResponse, error)
}

func (m *mockArcadeClient) CreateRecord(ctx context.Context, req *arcadedb.CreateRecordRequest, _ ...grpc.CallOption) (*arcadedb.CreateRecordResponse, error) {
	if m.createRecordFn != nil {
		return m.createRecordFn(ctx, req)
	}
	return &arcadedb.CreateRecordResponse{Rid: "#1:0"}, nil
}

func (m *mockArcadeClient) DeleteRecord(ctx context.Context, req *arcadedb.DeleteRecordRequest, _ ...grpc.CallOption) (*arcadedb.DeleteRecordResponse, error) {
	if m.deleteRecordFn != nil {
		return m.deleteRecordFn(ctx, req)
	}
	return &arcadedb.DeleteRecordResponse{}, nil
}

// Stub implementations for unused methods
func (m *mockArcadeClient) StreamQuery(context.Context, *arcadedb.StreamQueryRequest, ...grpc.CallOption) (grpc.ServerStreamingClient[arcadedb.QueryResult], error) {
	return nil, nil
}
func (m *mockArcadeClient) ExecuteCommand(context.Context, *arcadedb.ExecuteCommandRequest, ...grpc.CallOption) (*arcadedb.ExecuteCommandResponse, error) {
	return nil, nil
}
func (m *mockArcadeClient) ExecuteQuery(context.Context, *arcadedb.ExecuteQueryRequest, ...grpc.CallOption) (*arcadedb.ExecuteQueryResponse, error) {
	return nil, nil
}
func (m *mockArcadeClient) UpdateRecord(context.Context, *arcadedb.UpdateRecordRequest, ...grpc.CallOption) (*arcadedb.UpdateRecordResponse, error) {
	return nil, nil
}
func (m *mockArcadeClient) LookupByRid(context.Context, *arcadedb.LookupByRidRequest, ...grpc.CallOption) (*arcadedb.LookupByRidResponse, error) {
	return nil, nil
}
func (m *mockArcadeClient) BulkInsert(context.Context, *arcadedb.BulkInsertRequest, ...grpc.CallOption) (*arcadedb.InsertSummary, error) {
	return nil, nil
}
func (m *mockArcadeClient) InsertStream(context.Context, ...grpc.CallOption) (grpc.ClientStreamingClient[arcadedb.InsertChunk, arcadedb.InsertSummary], error) {
	return nil, nil
}
func (m *mockArcadeClient) InsertBidirectional(context.Context, ...grpc.CallOption) (grpc.BidiStreamingClient[arcadedb.InsertRequest, arcadedb.InsertResponse], error) {
	return nil, nil
}
func (m *mockArcadeClient) BeginTransaction(context.Context, *arcadedb.BeginTransactionRequest, ...grpc.CallOption) (*arcadedb.BeginTransactionResponse, error) {
	return nil, nil
}
func (m *mockArcadeClient) CommitTransaction(context.Context, *arcadedb.CommitTransactionRequest, ...grpc.CallOption) (*arcadedb.CommitTransactionResponse, error) {
	return nil, nil
}
func (m *mockArcadeClient) RollbackTransaction(context.Context, *arcadedb.RollbackTransactionRequest, ...grpc.CallOption) (*arcadedb.RollbackTransactionResponse, error) {
	return nil, nil
}

func TestGraphService_CreateNode(t *testing.T) {
	tests := []struct {
		name        string
		req         *pb.CreateNodeRequest
		mockFn      func(context.Context, *arcadedb.CreateRecordRequest) (*arcadedb.CreateRecordResponse, error)
		wantSuccess bool
		wantNodeID  string
	}{
		{
			name: "success with properties",
			req: &pb.CreateNodeRequest{
				TypeId:     "Character",
				Properties: mustStruct(t, map[string]any{"name": "Frodo", "age": 50.0}),
			},
			mockFn: func(_ context.Context, req *arcadedb.CreateRecordRequest) (*arcadedb.CreateRecordResponse, error) {
				if req.Type != "Character" {
					t.Errorf("expected type Character, got %s", req.Type)
				}
				if req.Database != "testdb" {
					t.Errorf("expected database testdb, got %s", req.Database)
				}
				return &arcadedb.CreateRecordResponse{Rid: "#10:5"}, nil
			},
			wantSuccess: true,
			wantNodeID:  "#10:5",
		},
		{
			name: "success without properties",
			req: &pb.CreateNodeRequest{
				TypeId: "Location",
			},
			wantSuccess: true,
			wantNodeID:  "#1:0",
		},
		{
			name: "arcade error",
			req: &pb.CreateNodeRequest{
				TypeId: "Character",
			},
			mockFn: func(context.Context, *arcadedb.CreateRecordRequest) (*arcadedb.CreateRecordResponse, error) {
				return nil, errors.New("connection refused")
			},
			wantSuccess: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mock := &mockArcadeClient{createRecordFn: tt.mockFn}
			svc := NewGraphService(mock, "testdb", "root", "secret")

			resp, err := svc.CreateNode(context.Background(), tt.req)
			if err != nil {
				t.Fatalf("CreateNode returned error: %v", err)
			}

			if resp.Success != tt.wantSuccess {
				t.Errorf("Success = %v, want %v (message: %s)", resp.Success, tt.wantSuccess, resp.Message)
			}

			if tt.wantSuccess && resp.Node.Id != tt.wantNodeID {
				t.Errorf("Node.Id = %s, want %s", resp.Node.Id, tt.wantNodeID)
			}
		})
	}
}

func TestGraphService_CreateEdge(t *testing.T) {
	tests := []struct {
		name        string
		req         *pb.CreateEdgeRequest
		mockFn      func(context.Context, *arcadedb.CreateRecordRequest) (*arcadedb.CreateRecordResponse, error)
		wantSuccess bool
	}{
		{
			name: "success",
			req: &pb.CreateEdgeRequest{
				Relationship: "KNOWS",
				Directed:     true,
				SourceNodeId: "#10:1",
				TargetNodeId: "#10:2",
			},
			mockFn: func(_ context.Context, req *arcadedb.CreateRecordRequest) (*arcadedb.CreateRecordResponse, error) {
				if req.Type != "KNOWS" {
					t.Errorf("expected type KNOWS, got %s", req.Type)
				}
				// Verify edge properties contain source/target
				if req.Record.Properties["@out"].GetStringValue() != "#10:1" {
					t.Errorf("expected @out=#10:1, got %v", req.Record.Properties["@out"])
				}
				if req.Record.Properties["@in"].GetStringValue() != "#10:2" {
					t.Errorf("expected @in=#10:2, got %v", req.Record.Properties["@in"])
				}
				return &arcadedb.CreateRecordResponse{Rid: "#20:0"}, nil
			},
			wantSuccess: true,
		},
		{
			name: "arcade error",
			req: &pb.CreateEdgeRequest{
				Relationship: "KNOWS",
				SourceNodeId: "#10:1",
				TargetNodeId: "#10:2",
			},
			mockFn: func(context.Context, *arcadedb.CreateRecordRequest) (*arcadedb.CreateRecordResponse, error) {
				return nil, errors.New("type KNOWS not found")
			},
			wantSuccess: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mock := &mockArcadeClient{createRecordFn: tt.mockFn}
			svc := NewGraphService(mock, "testdb", "root", "secret")

			resp, err := svc.CreateEdge(context.Background(), tt.req)
			if err != nil {
				t.Fatalf("CreateEdge returned error: %v", err)
			}

			if resp.Success != tt.wantSuccess {
				t.Errorf("Success = %v, want %v (message: %s)", resp.Success, tt.wantSuccess, resp.Message)
			}
		})
	}
}

func TestGraphService_DeleteNode(t *testing.T) {
	tests := []struct {
		name        string
		nodeID      string
		mockFn      func(context.Context, *arcadedb.DeleteRecordRequest) (*arcadedb.DeleteRecordResponse, error)
		wantSuccess bool
	}{
		{
			name:   "success",
			nodeID: "#10:5",
			mockFn: func(_ context.Context, req *arcadedb.DeleteRecordRequest) (*arcadedb.DeleteRecordResponse, error) {
				if req.Rid != "#10:5" {
					t.Errorf("expected rid #10:5, got %s", req.Rid)
				}
				return &arcadedb.DeleteRecordResponse{}, nil
			},
			wantSuccess: true,
		},
		{
			name:   "not found",
			nodeID: "#99:99",
			mockFn: func(context.Context, *arcadedb.DeleteRecordRequest) (*arcadedb.DeleteRecordResponse, error) {
				return nil, errors.New("record not found")
			},
			wantSuccess: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mock := &mockArcadeClient{deleteRecordFn: tt.mockFn}
			svc := NewGraphService(mock, "testdb", "root", "secret")

			resp, err := svc.DeleteNode(context.Background(), &pb.DeleteNodeRequest{Id: tt.nodeID})
			if err != nil {
				t.Fatalf("DeleteNode returned error: %v", err)
			}

			if resp.Success != tt.wantSuccess {
				t.Errorf("Success = %v, want %v", resp.Success, tt.wantSuccess)
			}
		})
	}
}

func TestGraphService_DeleteEdge(t *testing.T) {
	mock := &mockArcadeClient{
		deleteRecordFn: func(_ context.Context, req *arcadedb.DeleteRecordRequest) (*arcadedb.DeleteRecordResponse, error) {
			if req.Rid != "#20:0" {
				t.Errorf("expected rid #20:0, got %s", req.Rid)
			}
			return &arcadedb.DeleteRecordResponse{}, nil
		},
	}
	svc := NewGraphService(mock, "testdb", "root", "secret")

	resp, err := svc.DeleteEdge(context.Background(), &pb.DeleteEdgeRequest{Id: "#20:0"})
	if err != nil {
		t.Fatalf("DeleteEdge returned error: %v", err)
	}

	if !resp.Success {
		t.Errorf("expected success, got failure: %s", resp.Message)
	}
}

func TestStructToGrpcProperties(t *testing.T) {
	tests := []struct {
		name    string
		input   map[string]any
		check   func(t *testing.T, props map[string]*arcadedb.GrpcValue)
		wantErr bool
	}{
		{
			name:  "nil struct",
			input: nil,
			check: func(t *testing.T, props map[string]*arcadedb.GrpcValue) {
				if props != nil {
					t.Errorf("expected nil, got %v", props)
				}
			},
		},
		{
			name:  "string value",
			input: map[string]any{"name": "test"},
			check: func(t *testing.T, props map[string]*arcadedb.GrpcValue) {
				if props["name"].GetStringValue() != "test" {
					t.Errorf("expected 'test', got %v", props["name"])
				}
			},
		},
		{
			name:  "number value",
			input: map[string]any{"count": 42.0},
			check: func(t *testing.T, props map[string]*arcadedb.GrpcValue) {
				if props["count"].GetDoubleValue() != 42.0 {
					t.Errorf("expected 42.0, got %v", props["count"])
				}
			},
		},
		{
			name:  "bool value",
			input: map[string]any{"active": true},
			check: func(t *testing.T, props map[string]*arcadedb.GrpcValue) {
				if !props["active"].GetBoolValue() {
					t.Errorf("expected true, got false")
				}
			},
		},
		{
			name:  "list value",
			input: map[string]any{"tags": []any{"a", "b"}},
			check: func(t *testing.T, props map[string]*arcadedb.GrpcValue) {
				list := props["tags"].GetListValue()
				if len(list.Values) != 2 {
					t.Errorf("expected 2 values, got %d", len(list.Values))
				}
			},
		},
		{
			name:  "nested struct",
			input: map[string]any{"meta": map[string]any{"key": "value"}},
			check: func(t *testing.T, props map[string]*arcadedb.GrpcValue) {
				embedded := props["meta"].GetEmbeddedValue()
				if embedded.Fields["key"].GetStringValue() != "value" {
					t.Errorf("expected nested key=value")
				}
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var s *structpb.Struct
			if tt.input != nil {
				s = mustStruct(t, tt.input)
			}

			props, err := structToGrpcProperties(s)
			if (err != nil) != tt.wantErr {
				t.Fatalf("error = %v, wantErr %v", err, tt.wantErr)
			}

			if tt.check != nil {
				tt.check(t, props)
			}
		})
	}
}

func mustStruct(t *testing.T, m map[string]any) *structpb.Struct {
	t.Helper()
	s, err := structpb.NewStruct(m)
	if err != nil {
		t.Fatalf("failed to create struct: %v", err)
	}
	return s
}
