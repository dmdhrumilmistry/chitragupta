package db

import (
	"context"

	"github.com/dmdhrumilmistry/chitragupta/pkg/config"
	"github.com/rs/zerolog/log"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"go.mongodb.org/mongo-driver/mongo/readpref"
)

type Mongo struct {
	Client *mongo.Client
	Db     *mongo.Database
}

func NewMongoClient(cfg *config.Config) (*mongo.Client, error) {
	client, err := mongo.Connect(context.TODO(), options.Client().ApplyURI(cfg.DbUri))
	if err != nil {
		log.Fatal().Err(err).Msgf("Failed to create mongo client")
		return nil, err
	}

	// check connectivity
	if err := client.Ping(context.TODO(), readpref.Primary()); err != nil {
		log.Fatal().Err(err).Msg("Failed to connect to db")
		return nil, err
	}

	log.Info().Msg("Connected to db")

	return client, nil
}

func NewMongo(cfg *config.Config) (*Mongo, error) {
	dbClient, err := NewMongoClient(cfg)
	if err != nil {
		log.Fatal().Err(err).Msg("failed to init mongo client")
		return nil, err
	}

	db := dbClient.Database(cfg.DbName)

	return &Mongo{
		Client: dbClient,
		Db:     db,
	}, nil
}

func EnsureIndex(collection *mongo.Collection, indexModel mongo.IndexModel) {
	// Create the index
	indexName, err := collection.Indexes().CreateOne(context.TODO(), indexModel)
	if err != nil {
		log.Error().Err(err).Msg("failed to create index")
	} else {
		log.Info().Msgf("Index Created successfully: %s", indexName)
	}
}
