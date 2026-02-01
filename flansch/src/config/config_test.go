package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoad_Defaults(t *testing.T) {
	cfg, err := NewLoader().WithConfigDir(t.TempDir()).Load(nil)
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}

	tests := []struct {
		name string
		got  any
		want any
	}{
		{"server.host", cfg.Server.Host, "0.0.0.0"},
		{"server.port", cfg.Server.Port, 9090},
		{"arcadedb.host", cfg.ArcadeDB.Host, "localhost"},
		{"arcadedb.port", cfg.ArcadeDB.Port, 2480},
		{"arcadedb.database", cfg.ArcadeDB.Database, "bibliophage"},
		{"arcadedb.username", cfg.ArcadeDB.Username, "root"},
		{"arcadedb.password", cfg.ArcadeDB.Password, ""},
		{"log.level", cfg.Log.Level, "info"},
	}

	for _, tt := range tests {
		if tt.got != tt.want {
			t.Errorf("%s = %v, want %v", tt.name, tt.got, tt.want)
		}
	}
}

func TestLoad_Flags(t *testing.T) {
	tests := []struct {
		name  string
		args  []string
		check func(*Config) (got, want any)
	}{
		{
			name: "server.port flag",
			args: []string{"--server.port=8080"},
			check: func(c *Config) (any, any) {
				return c.Server.Port, 8080
			},
		},
		{
			name: "server.host flag",
			args: []string{"--server.host=127.0.0.1"},
			check: func(c *Config) (any, any) {
				return c.Server.Host, "127.0.0.1"
			},
		},
		{
			name: "arcadedb.host flag",
			args: []string{"--arcadedb.host=db.example.com"},
			check: func(c *Config) (any, any) {
				return c.ArcadeDB.Host, "db.example.com"
			},
		},
		{
			name: "log.level flag",
			args: []string{"--log.level=debug"},
			check: func(c *Config) (any, any) {
				return c.Log.Level, "debug"
			},
		},
		{
			name: "multiple flags",
			args: []string{"--server.port=7777", "--arcadedb.database=testdb"},
			check: func(c *Config) (any, any) {
				return []any{c.Server.Port, c.ArcadeDB.Database},
					[]any{7777, "testdb"}
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cfg, err := NewLoader().WithConfigDir(t.TempDir()).Load(tt.args)
			if err != nil {
				t.Fatalf("Load() error = %v", err)
			}

			got, want := tt.check(cfg)
			if !equal(got, want) {
				t.Errorf("got %v, want %v", got, want)
			}
		})
	}
}

func TestLoad_EnvVars(t *testing.T) {
	tests := []struct {
		name   string
		envKey string
		envVal string
		check  func(*Config) (got, want any)
	}{
		{
			name:   "FLANSCH_SERVER_PORT",
			envKey: "FLANSCH_SERVER_PORT",
			envVal: "8888",
			check: func(c *Config) (any, any) {
				return c.Server.Port, 8888
			},
		},
		{
			name:   "FLANSCH_ARCADEDB_HOST",
			envKey: "FLANSCH_ARCADEDB_HOST",
			envVal: "remote-db.local",
			check: func(c *Config) (any, any) {
				return c.ArcadeDB.Host, "remote-db.local"
			},
		},
		{
			name:   "FLANSCH_LOG_LEVEL",
			envKey: "FLANSCH_LOG_LEVEL",
			envVal: "warn",
			check: func(c *Config) (any, any) {
				return c.Log.Level, "warn"
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Setenv(tt.envKey, tt.envVal)

			cfg, err := NewLoader().WithConfigDir(t.TempDir()).Load(nil)
			if err != nil {
				t.Fatalf("Load() error = %v", err)
			}

			got, want := tt.check(cfg)
			if !equal(got, want) {
				t.Errorf("got %v, want %v", got, want)
			}
		})
	}
}

func TestLoad_ConfigFile(t *testing.T) {
	tests := []struct {
		name    string
		yaml    string
		check   func(*Config) (got, want any)
		wantErr bool
	}{
		{
			name: "partial config",
			yaml: `
server:
  port: 3000
`,
			check: func(c *Config) (any, any) {
				return []any{c.Server.Port, c.Server.Host},
					[]any{3000, "0.0.0.0"} // host should be default
			},
		},
		{
			name: "full config",
			yaml: `
server:
  host: "192.168.1.1"
  port: 4000
arcadedb:
  host: "arcade.local"
  port: 3000
  database: "mydb"
  username: "admin"
  password: "secret"
log:
  level: "error"
`,
			check: func(c *Config) (any, any) {
				return []any{
						c.Server.Host, c.Server.Port,
						c.ArcadeDB.Host, c.ArcadeDB.Port, c.ArcadeDB.Database,
						c.Log.Level,
					}, []any{
						"192.168.1.1", 4000,
						"arcade.local", 3000, "mydb",
						"error",
					}
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			dir := t.TempDir()
			configPath := filepath.Join(dir, "flansch.yaml")
			if err := os.WriteFile(configPath, []byte(tt.yaml), 0644); err != nil {
				t.Fatalf("failed to write config file: %v", err)
			}

			cfg, err := NewLoader().WithConfigDir(dir).Load(nil)
			if (err != nil) != tt.wantErr {
				t.Fatalf("Load() error = %v, wantErr %v", err, tt.wantErr)
			}
			if tt.wantErr {
				return
			}

			got, want := tt.check(cfg)
			if !equal(got, want) {
				t.Errorf("got %v, want %v", got, want)
			}
		})
	}
}

func TestLoad_Priority(t *testing.T) {
	// Setup: config file sets port to 1000
	dir := t.TempDir()
	yaml := `server:
  port: 1000
`
	if err := os.WriteFile(filepath.Join(dir, "flansch.yaml"), []byte(yaml), 0644); err != nil {
		t.Fatalf("failed to write config file: %v", err)
	}

	tests := []struct {
		name     string
		envKey   string
		envVal   string
		args     []string
		wantPort int
	}{
		{
			name:     "file only",
			wantPort: 1000,
		},
		{
			name:     "env overrides file",
			envKey:   "FLANSCH_SERVER_PORT",
			envVal:   "2000",
			wantPort: 2000,
		},
		{
			name:     "flag overrides env and file",
			envKey:   "FLANSCH_SERVER_PORT",
			envVal:   "2000",
			args:     []string{"--server.port=3000"},
			wantPort: 3000,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.envKey != "" {
				t.Setenv(tt.envKey, tt.envVal)
			}

			cfg, err := NewLoader().WithConfigDir(dir).Load(tt.args)
			if err != nil {
				t.Fatalf("Load() error = %v", err)
			}

			if cfg.Server.Port != tt.wantPort {
				t.Errorf("Server.Port = %d, want %d", cfg.Server.Port, tt.wantPort)
			}
		})
	}
}

func TestLoad_ExplicitConfigFlag(t *testing.T) {
	dir := t.TempDir()
	customPath := filepath.Join(dir, "custom.yaml")
	yaml := `server:
  port: 5555
`
	if err := os.WriteFile(customPath, []byte(yaml), 0644); err != nil {
		t.Fatalf("failed to write config file: %v", err)
	}

	cfg, err := NewLoader().Load([]string{"--config=" + customPath})
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}

	if cfg.Server.Port != 5555 {
		t.Errorf("Server.Port = %d, want 5555", cfg.Server.Port)
	}
}

func TestLoad_InvalidConfigPath(t *testing.T) {
	_, err := NewLoader().Load([]string{"--config=/nonexistent/path.yaml"})
	if err == nil {
		t.Error("Load() expected error for nonexistent config file")
	}
}

func TestLoad_InvalidFlag(t *testing.T) {
	_, err := NewLoader().Load([]string{"--unknown-flag=value"})
	if err == nil {
		t.Error("Load() expected error for unknown flag")
	}
}

// equal compares two values, handling slices.
func equal(a, b any) bool {
	as, aok := a.([]any)
	bs, bok := b.([]any)
	if aok && bok {
		if len(as) != len(bs) {
			return false
		}
		for i := range as {
			if as[i] != bs[i] {
				return false
			}
		}
		return true
	}
	return a == b
}
