package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/gin-contrib/cors" // Import the new CORS package
	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/joho/godotenv"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// --- Database Model ---
type User struct {
	gorm.Model
	Email    string `gorm:"unique;not null"`
	Password string `gorm:"not null"`
}

var db *gorm.DB
var jwtKey []byte

// --- Main Function ---
func main() {
	// Load .env file if it exists (for local development).
	// In production (Kubernetes/Docker), variables are set by the environment.
	godotenv.Load()

	jwtKey = []byte(os.Getenv("JWT_SECRET"))

	dsn := os.Getenv("DB_URL")
	db, err = gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatal("Failed to connect to database")
	}

	db.AutoMigrate(&User{})

	r := gin.Default()

	// --- Configure CORS Middleware ---
	// This allows our React frontend to communicate with this Go backend.
	config := cors.DefaultConfig()
	config.AllowOrigins = []string{"http://localhost:5173"} // Your frontend's origin
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Type", "Authorization"}
	r.Use(cors.New(config))

	// --- Define Routes ---
	// Public routes
	r.POST("/register", Register)
	r.POST("/login", Login)

	// Protected Route Group
	api := r.Group("/api")
	api.Use(AuthMiddleware())
	{
		api.POST("/query", QueryHandler)
		api.POST("/analyze", AnalyzeHandler)
	}

	// Run the server
	r.Run(":8081") // Or your chosen port
}

// --- Handler Functions ---

func Register(c *gin.Context) {
	var input struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}

	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid input"})
		return
	}

	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(input.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to hash password"})
		return
	}

	user := User{Email: input.Email, Password: string(hashedPassword)}
	result := db.Create(&user)
	if result.Error != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Email already exists"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "Registration successful"})
}

func Login(c *gin.Context) {
	var input struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}

	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid input"})
		return
	}

	var user User
	db.First(&user, "email = ?", input.Email)
	if user.ID == 0 {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid email or password"})
		return
	}

	err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(input.Password))
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid email or password"})
		return
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"sub": user.ID,
		"exp": time.Now().Add(time.Hour * 24).Unix(),
	})

	tokenString, err := token.SignedString(jwtKey)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create token"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"token": tokenString})
}

func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Authorization header required"})
			return
		}

		tokenString := strings.TrimPrefix(authHeader, "Bearer ")
		if tokenString == authHeader {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Bearer token required"})
			return
		}

		token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
			}
			return jwtKey, nil
		})

		if err != nil || !token.Valid {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Invalid token"})
			return
		}

		c.Next()
	}
}

func QueryHandler(c *gin.Context) {
	var input struct {
		Question string `json:"question"`
	}

	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid input, 'question' field is required."})
		return
	}

	pythonServiceURL := "http://ai_core:8000/query"
	requestBody, err := json.Marshal(input)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create request for AI service"})
		return
	}

	resp, err := http.Post(pythonServiceURL, "application/json", bytes.NewBuffer(requestBody))
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "AI service is unreachable"})
		return
	}
	defer resp.Body.Close()

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to read response from AI service"})
		return
	}

	c.Data(resp.StatusCode, "application/json", responseBody)
}

func AnalyzeHandler(c *gin.Context) {
	var input struct {
		RepoURL string `json:"repo_url"`
	}

	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid input, 'repo_url' field is required."})
		return
	}

	pythonServiceURL := "http://ai_core:8000/analyze"
	requestBody, err := json.Marshal(input)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create request for AI service"})
		return
	}

	resp, err := http.Post(pythonServiceURL, "application/json", bytes.NewBuffer(requestBody))
	if err != nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "AI service is unreachable"})
		return
	}
	defer resp.Body.Close()

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to read response from AI service"})
		return
	}

	c.Data(resp.StatusCode, "application/json", responseBody)
}