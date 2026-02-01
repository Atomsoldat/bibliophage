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

// Loader configures how configuration is loaded.
type Loader struct {
	v         *viper.Viper
	flags     *pflag.FlagSet
	configDir string // optional override for config search path
}

// NewLoader creates a Loader with default settings.
func NewLoader() *Loader {
	return &Loader{
		v:     viper.New(),
		flags: pflag.NewFlagSet("flansch", pflag.ContinueOnError),
	}
}

// WithConfigDir sets a custom config directory (useful for testing).
func (l *Loader) WithConfigDir(dir string) *Loader {
	l.configDir = dir
	return l
}

// Load reads configuration from file, environment variables, and CLI args.
// Priority (highest to lowest): flags > env vars > config file > defaults
func (l *Loader) Load(args []string) (*Config, error) {
	l.setDefaults()
	l.setupConfigFile()
	l.setupEnvVars()
	l.defineFlags()

	if err := l.flags.Parse(args); err != nil {
		return nil, err
	}

	if err := l.v.BindPFlags(l.flags); err != nil {
		return nil, err
	}

	if configFile := l.v.GetString("config"); configFile != "" {
		l.v.SetConfigFile(configFile)
		if err := l.v.ReadInConfig(); err != nil {
			return nil, err
		}
	}

	var cfg Config
	if err := l.v.Unmarshal(&cfg); err != nil {
		return nil, err
	}

	return &cfg, nil
}

func (l *Loader) setDefaults() {
	l.v.SetDefault("server.host", "0.0.0.0")
	l.v.SetDefault("server.port", 9090)
	l.v.SetDefault("arcadedb.host", "localhost")
	l.v.SetDefault("arcadedb.port", 2480)
	l.v.SetDefault("arcadedb.database", "bibliophage")
	l.v.SetDefault("arcadedb.username", "root")
	l.v.SetDefault("arcadedb.password", "")
	l.v.SetDefault("log.level", "info")
}

func (l *Loader) setupConfigFile() {
	l.v.SetConfigName("flansch")
	l.v.SetConfigType("yaml")

	if l.configDir != "" {
		l.v.AddConfigPath(l.configDir)
	} else {
		l.v.AddConfigPath(".")
		l.v.AddConfigPath("/etc/flansch")
		l.v.AddConfigPath("$HOME/.config/flansch")
	}

	// Ignore error if config file not found
	_ = l.v.ReadInConfig()
}

func (l *Loader) setupEnvVars() {
	l.v.SetEnvPrefix("FLANSCH")
	l.v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	l.v.AutomaticEnv()
}

func (l *Loader) defineFlags() {
	l.flags.String("config", "", "path to config file")
	l.flags.String("server.host", "", "host to bind the server to")
	l.flags.Int("server.port", 0, "port for the gRPC server")
	l.flags.String("arcadedb.host", "", "ArcadeDB server host")
	l.flags.Int("arcadedb.port", 0, "ArcadeDB server port")
	l.flags.String("arcadedb.database", "", "ArcadeDB database name")
	l.flags.String("arcadedb.username", "", "ArcadeDB username")
	l.flags.String("arcadedb.password", "", "ArcadeDB password")
	l.flags.String("log.level", "", "log level (debug, info, warn, error)")
}

// Load is a convenience function that creates a Loader and loads config.
func Load(args []string) (*Config, error) {
	return NewLoader().Load(args)
}
