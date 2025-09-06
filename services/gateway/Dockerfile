# services/gateway/Dockerfile

# Stage 1: Build the Go binary
FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go mod tidy
RUN CGO_ENABLED=0 GOOS=linux go build -o /main .

# Stage 2: Create the final small image
FROM alpine:latest
WORKDIR /
COPY --from=builder /main .
EXPOSE 8081
CMD ["/main"]
