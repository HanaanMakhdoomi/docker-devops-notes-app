# Docker DevOps Notes App

A full-stack DevOps notes application built using:

- React
- Flask
- PostgreSQL
- Docker
- Docker Compose
- Nginx

## Features

- Create notes
- Delete notes
- Search notes
- Dark/light mode
- Sidebar navigation
- Dockerized multi-service architecture

## Architecture

Browser → Nginx → React Frontend → Flask Backend → PostgreSQL

## Run Locally

```bash
docker compose up --build
