import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { categoriesAPI, seedDataAPI } from '@/api/api';
import { ShoppingBag, Package, Users, TrendingUp, ArrowRight, Store } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    // If user is logged in, redirect to appropriate dashboard
    if (user) {
      if (user.role === 'customer') navigate('/customer/dashboard');
      else if (user.role === 'retailer') navigate('/retailer/dashboard');
      else if (user.role === 'wholesaler') navigate('/wholesaler/dashboard');
    }
  }, [user, navigate]);

  useEffect(() => {
    const initData = async () => {
      try {
        // Try to seed data first
        await seedDataAPI.seed();
        // Then fetch categories
        const response = await categoriesAPI.getAll();
        setCategories(response.data.slice(0, 6));
      } catch (error) {
        console.error('Error fetching categories:', error);
      }
    };
    initData();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Navbar */}
      <nav className="bg-white shadow-md" data-testid="landing-navbar">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <Store className="h-8 w-8 text-blue-600" />
              <span className="text-2xl font-bold text-blue-600">Live MART</span>
            </div>
            <div className="flex space-x-4">
              <Button variant="ghost" onClick={() => navigate('/auth')}>Login</Button>
              <Button onClick={() => navigate('/auth')} data-testid="get-started-btn">Get Started</Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-4" data-testid="hero-section">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Your Online Delivery System
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            Connecting Customers, Retailers, and Wholesalers for seamless e-commerce experience.
            Shop local, support businesses, get everything delivered to your door.
          </p>
          <div className="flex justify-center space-x-4">
            <Button size="lg" onClick={() => navigate('/auth')} data-testid="shop-now-btn">
              Shop Now <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate('/auth')}>
              Become a Seller
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 px-4 bg-white" data-testid="features-section">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Why Choose Live MART?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Card>
              <CardContent className="pt-6">
                <ShoppingBag className="h-12 w-12 text-blue-600 mb-4" />
                <h3 className="text-xl font-semibold mb-2">For Customers</h3>
                <p className="text-gray-600">
                  Browse thousands of products, enjoy personalized recommendations, and get everything delivered to your doorstep.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <Package className="h-12 w-12 text-green-600 mb-4" />
                <h3 className="text-xl font-semibold mb-2">For Retailers</h3>
                <p className="text-gray-600">
                  Manage your inventory, track orders, connect with wholesalers, and grow your business online.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <Users className="h-12 w-12 text-purple-600 mb-4" />
                <h3 className="text-xl font-semibold mb-2">For Wholesalers</h3>
                <p className="text-gray-600">
                  Supply to multiple retailers, manage bulk orders, and streamline your distribution network.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      {categories.length > 0 && (
        <section className="py-16 px-4" data-testid="categories-section">
          <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">Shop by Category</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
              {categories.map((category) => (
                <Card
                  key={category.id}
                  className="cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => navigate('/auth')}
                  data-testid={`category-${category.name.toLowerCase().replace(/ /g, '-')}`}
                >
                  <CardContent className="p-4 text-center">
                    <div className="aspect-square mb-3 rounded-lg overflow-hidden bg-gray-100">
                      <img
                        src={category.image_url || 'https://via.placeholder.com/200'}
                        alt={category.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <h3 className="font-semibold text-sm">{category.name}</h3>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Stats Section */}
      <section className="py-16 px-4 bg-blue-600 text-white" data-testid="stats-section">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <TrendingUp className="h-12 w-12 mx-auto mb-4" />
              <h3 className="text-4xl font-bold mb-2">1000+</h3>
              <p className="text-blue-100">Products Available</p>
            </div>
            <div>
              <Users className="h-12 w-12 mx-auto mb-4" />
              <h3 className="text-4xl font-bold mb-2">500+</h3>
              <p className="text-blue-100">Active Sellers</p>
            </div>
            <div>
              <ShoppingBag className="h-12 w-12 mx-auto mb-4" />
              <h3 className="text-4xl font-bold mb-2">5000+</h3>
              <p className="text-blue-100">Happy Customers</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4" data-testid="cta-section">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-6">Ready to Get Started?</h2>
          <p className="text-xl text-gray-600 mb-8">
            Join thousands of users already experiencing the future of online shopping.
          </p>
          <Button size="lg" onClick={() => navigate('/auth')} data-testid="join-now-btn">
            Join Now - It's Free!
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8" data-testid="footer">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p>&copy; 2025 Live MART. All rights reserved.</p>
          <p className="text-gray-400 mt-2">Your trusted online delivery system</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;