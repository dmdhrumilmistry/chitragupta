package main

import (
	"context"
	"fmt"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/labstack/echo/v4"

	"github.com/dmdhrumilmistry/chitragupta/pkg/config"
	"github.com/dmdhrumilmistry/chitragupta/pkg/db"
	_ "github.com/dmdhrumilmistry/chitragupta/pkg/logging"
	"github.com/rs/zerolog/log"
)

func main() {
	e := echo.New()

	mgo, err := db.NewMongo(config.DefaultConfig)
	if err != nil {
		log.Fatal().Err(err).Msg("failed to get db connection")
	}
	defer mgo.Client.Disconnect(context.TODO())

	if !config.DefaultConfig.IsDevEnv {
		gin.SetMode(gin.ReleaseMode)
	}

	e.GET("/", func(c echo.Context) error {
		return c.JSON(http.StatusOK, echo.Map{"message": "Hello, World!"})
	})

	log.Info().Msgf("Starting server on port %d", config.DefaultConfig.HostPort)
	log.Fatal().Err(e.Start(fmt.Sprintf(":%d", config.DefaultConfig.HostPort))).Msg("Server exited unexpectedly")
}
