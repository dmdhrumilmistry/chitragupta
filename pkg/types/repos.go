package types

import "time"

type GithubAppConfig struct {
	AppID          int64
	InstallationID int64
	PrivateKey     string
}

type Repo struct {
	Id        string    `json:"id" bson:"id,omitempty"`
	Owner     string    `json:"owner" bson:"owner,omitempty"`
	Name      string    `json:"name" bson:"name,omitempty"`
	CommitSha []string  `json:"commit_sha" bson:"commit_sha,omitempty"`
	IsPrivate bool      `json:"is_private" bson:"is_private,omitempty"`
	IsFork    bool      `json:"is_fork" bson:"is_fork,omitempty"`
	UpdatedAt time.Time `json:"updated_at" bson:"updated_at,omitempty"`
	CreatedAt time.Time `json:"created_at" bson:"created_at,omitempty"`
}
