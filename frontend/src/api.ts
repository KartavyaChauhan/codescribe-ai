import axios from "axios";

// The base URL of our Go API Gateway
const API_BASE_URL = "http://localhost:8081";

// A data type for our auth functions
interface AuthCredentials {
  email: string;
  password: string;
}

export const registerUser = async (credentials: AuthCredentials) => {
  const response = await axios.post(`${API_BASE_URL}/register`, credentials);
  return response.data;
};

export const loginUser = async (credentials: AuthCredentials) => {
  const response = await axios.post(`${API_BASE_URL}/login`, credentials);
  return response.data; // This will contain the JWT token
};
// Analyze and Query types
interface AnalyzePayload {
  repo_url: string;
}

interface QueryPayload {
  question: string;
}

export const analyzeRepo = async (payload: AnalyzePayload, token: string) => {
  const response = await axios.post(`${API_BASE_URL}/api/analyze`, payload, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const queryRepo = async (payload: QueryPayload, token: string) => {
  const response = await axios.post(`${API_BASE_URL}/api/query`, payload, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};
