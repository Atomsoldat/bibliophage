package config

import (
	"strings"

	"github.com/spf13/pflag"
	"github.com/spf13/viper"
)

// Config holds all configuration for flansch.
type Config struct {
	Server   ServerConfig   `mapstructure:"server"`
	ArcadeDB ArcadeDBConfig `mapstructure:"arcadedb"`
	Log      LogConfig      `mapstructure:"log"`
}

// ServerConfig holds settings for the flansch gRPC server.
type ServerConfig struct {
	Host string `mapstructure:"host"`
	Port int    `mapstructure:"port"`
}

// ArcadeDBConfig holds settings for connecting to ArcadeDB.
type ArcadeDBConfig struct {
	Host     string `mapstructure:"host"`
	Port     int    `mapstructure:"port"`
	Database string `mapstructure:"database"`
	Username string `mapstructure:"username"`
	Password string `mapstructure:"password"`
}

// LogConfig holds logging settings.
type LogConfig struct {
	Level string `mapstructure:"level"`
}

// Load reads configuration from file, environment variables, and flags.
// Priority (highest to lowest): flags > env vars > config file > defaults
func Load() (*Config, error) {
	v := viper.New()

	// Set defaults
	v.SetDefault("server.host", "0.0.0.0")
	v.SetDefault("server.port", 9090)
	v.SetDefault("arcadedb.host", "localhost")
	v.SetDefault("arcadedb.port", 2480)
	v.SetDefault("arcadedb.database", "bibliophage")
	v.SetDefault("arcadedb.username", "root")
	v.SetDefault("arcadedb.password", "")
	v.SetDefault("log.level", "info")

	// Config file settings
	v.SetConfigName("flansch")
	v.SetConfigType("yaml")
	v.AddConfigPath(".")
	v.AddConfigPath("/etc/flansch")
	v.AddConfigPath("$HOME/.config/flansch")

	// Read config file (ignore error if not found)
	_ = v.ReadInConfig()

	// Environment variables: FLANSCH_SERVER_PORT, FLANSCH_ARCADEDB_HOST, etc.
	v.SetEnvPrefix("FLANSCH")
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	v.AutomaticEnv()

	// Define CLI flags
	pflag.String("config", "", "path to config file")
	pflag.String("server.host", "", "host to bind the server to")
	pflag.Int("server.port", 0, "port for the gRPC server")
	pflag.String("arcadedb.host", "", "ArcadeDB server host")
	pflag.Int("arcadedb.port", 0, "ArcadeDB server port")
	pflag.String("arcadedb.database", "", "ArcadeDB database name")
	pflag.String("arcadedb.username", "", "ArcadeDB username")
	pflag.String("arcadedb.password", "", "ArcadeDB password")
	pflag.String("log.level", "", "log level (debug, info, warn, error)")
	pflag.Parse()

	// Bind flags to viper
	if err := v.BindPFlags(pflag.CommandLine); err != nil {
		return nil, err
	}

	// If --config flag is set, use that specific file
	if configFile := v.GetString("config"); configFile != "" {
		v.SetConfigFile(configFile)
		if err := v.ReadInConfig(); err != nil {
			return nil, err
		}
	}

	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, err
	}

	return &cfg, nil
}
