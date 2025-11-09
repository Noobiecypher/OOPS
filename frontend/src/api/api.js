import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth API
export const authAPI = {
  register: (data) => axios.post(`${API}/auth/register`, data),
  login: (data) => axios.post(`${API}/auth/login`, data),
  verifyOTP: (data) => axios.post(`${API}/auth/verify-otp`, data),
};

// Categories API
export const categoriesAPI = {
  getAll: () => axios.get(`${API}/categories`),
  create: (data) => axios.post(`${API}/categories`, data),
};

// Products API
export const productsAPI = {
  getAll: (params) => axios.get(`${API}/products`, { params }),
  getById: (id) => axios.get(`${API}/products/${id}`),
  create: (data) => axios.post(`${API}/products`, data),
  update: (id, data) => axios.put(`${API}/products/${id}`, data),
  delete: (id) => axios.delete(`${API}/products/${id}`),
};

// Cart API
export const cartAPI = {
  getCart: (userId) => axios.get(`${API}/cart/${userId}`),
  addItem: (userId, data) => axios.post(`${API}/cart/${userId}`, data),
  updateItem: (userId, itemId, quantity) => 
    axios.put(`${API}/cart/${userId}/${itemId}`, null, { params: { quantity } }),
  removeItem: (userId, itemId) => axios.delete(`${API}/cart/${userId}/${itemId}`),
  clearCart: (userId) => axios.delete(`${API}/cart/${userId}`),
};

// Orders API
export const ordersAPI = {
  create: (userId, data) => axios.post(`${API}/orders/${userId}`, data),
  getUserOrders: (userId) => axios.get(`${API}/orders/${userId}`),
  getOrderDetail: (orderId) => axios.get(`${API}/orders/detail/${orderId}`),
  updateStatus: (orderId, status) => axios.put(`${API}/orders/${orderId}/status`, { status }),
};

// Feedback API
export const feedbackAPI = {
  create: (userId, data) => axios.post(`${API}/feedback/${userId}`, data),
  getProductFeedback: (productId) => axios.get(`${API}/feedback/product/${productId}`),
};

// Shops API
export const shopsAPI = {
  getNearby: (lat, lng, radius) => axios.get(`${API}/shops`, { params: { lat, lng, radius } }),
};

// Dashboard API
export const dashboardAPI = {
  getRetailerDashboard: (userId) => axios.get(`${API}/dashboard/retailer/${userId}`),
  getWholesalerDashboard: (userId) => axios.get(`${API}/dashboard/wholesaler/${userId}`),
};

// Seed data API
export const seedDataAPI = {
  seed: () => axios.post(`${API}/seed-data`),
};
