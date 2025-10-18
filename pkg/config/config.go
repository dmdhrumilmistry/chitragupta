package config

import (
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
	"github.com/rs/zerolog/log"
)

type Config struct {
	// Host config
	HostPort      string // 8080
	Host          string // localhost
	Proto         string // http
	DomainBaseUrl string // http://localhost:8080

	// Db Config
	DbUri          string
	DbName         string
	DbQueryTimeout int

	// App config
	AppEnv              string
	IsDevEnv            bool
	DefaultWorkersCount int

	// Secrets
	GithubToken string

	// Google Secrets for Oauth login
	GoogleClientId     string
	GoogleClientSecret string

	// JWT Config
	JWTExpirationInSeconds int
	JWTSecretKey           string

	// Analyzer Config
	RunOsv  bool
	RunMpaf bool
	RunEpss bool
}

var DefaultConfig = NewConfig()

// generateJWTSecret generates a secure random JWT secret of the specified length.
func generateJWTSecret(length int) (string, error) {
	// Create a byte slice to hold the random bytes
	secret := make([]byte, length)

	// Read random bytes from the crypto/rand package
	_, err := rand.Read(secret)
	if err != nil {
		return "", err
	}

	// Encode the random bytes to a base64 string
	return base64.StdEncoding.EncodeToString(secret), nil
}

func NewConfig() *Config {
	godotenv.Load()
	env := strings.ToLower(getEnvString("ENV", "production"))

	jwtSecret, err := generateJWTSecret(60)
	if err != nil {
		log.Error().Err(err).Msg("failed to generate jwt secret")
	}

	return &Config{
		HostPort: getEnvString("HOST_PORT", "8080"),
		Host:     getEnvString("HOST", "localhost"),
		Proto:    getEnvString("PROTO", "http"),
		// DomainBaseUrl: ,

		DbUri:               getEnvString("DB_URI", "mongodb://localhost:27017"),
		DbName:              getEnvString("DB_NAME", "chitragupta"),
		DbQueryTimeout:      getEnvInt("DB_QUERY_TIMEOUT", 5),
		AppEnv:              env,
		IsDevEnv:            env == "dev",
		DefaultWorkersCount: getEnvInt("DEFAULT_WORKERS_COUNT", 30),

		// Github Secret
		GithubToken: getEnvString("GITHUB_TOKEN", ""),

		// Google secrets
		GoogleClientId:     getEnvString("GOOGLE_CLIENT_ID", ""),
		GoogleClientSecret: getEnvString("GOOGLE_CLIENT_SECRET", ""),

		// JWT Config
		JWTExpirationInSeconds: getEnvInt("JWT_EXP", 3600),
		JWTSecretKey:           getEnvString("JWT_SECRET_KEY", jwtSecret),
	}
}

func (c *Config) GetBaseUrl() string {
	if c.DomainBaseUrl == "" {
		c.DomainBaseUrl = fmt.Sprintf("%s://%s:%s", c.Proto, c.Host, c.HostPort)
	}

	return c.DomainBaseUrl
}

func getEnvString(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}

	return value
}

func getEnvBool(key string) bool {
	value := strings.ToLower(os.Getenv(key))
	return value == "true" || value == "1" || value == "yes"
}

func getEnvInt(key string, defaultValue int) int {
	value, err := strconv.Atoi(os.Getenv(key))
	if err != nil {
		log.Error().Err(err).Msgf("failed to get env value as int: %s", key)
		return defaultValue
	}

	return value
}
