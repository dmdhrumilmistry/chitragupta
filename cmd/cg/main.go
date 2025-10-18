package main

import (
	"fmt"
	"net/http"

	"github.com/labstack/echo/v4"

	_ "github.com/dmdhrumilmistry/chitragupta/pkg/logging"
	"github.com/rs/zerolog/log"
)

func main() {
	e := echo.New()
	port := 8000
	e.GET("/", func(c echo.Context) error {
		return c.JSON(http.StatusOK, echo.Map{"message": "Hello, World!"})
	})
	log.Info().Msgf("Starting server on port %d", port)

	log.Fatal().Err(e.Start(fmt.Sprintf(":%d", port))).Msg("Server exited unexpectedly")
}
