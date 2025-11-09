import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import Navbar from '@/components/Navbar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { categoriesAPI, productsAPI, cartAPI } from '@/api/api';
import { toast } from 'sonner';
import { Search, ShoppingCart, Star, Package } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const CustomerDashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [priceRange, setPriceRange] = useState('all');

  useEffect(() => {
    fetchCategories();
    fetchProducts();
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [selectedCategory, priceRange]);

  const fetchCategories = async () => {
    try {
      const response = await categoriesAPI.getAll();
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedCategory !== 'all') params.category_id = selectedCategory;
      if (searchQuery) params.search = searchQuery;
      
      if (priceRange !== 'all') {
        if (priceRange === 'low') {
          params.max_price = 10;
        } else if (priceRange === 'medium') {
          params.min_price = 10;
          params.max_price = 50;
        } else if (priceRange === 'high') {
          params.min_price = 50;
        }
      }

      const response = await productsAPI.getAll(params);
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
      toast.error('Failed to fetch products');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchProducts();
  };

  const addToCart = async (product) => {
    try {
      await cartAPI.addItem(user.id, {
        product_id: product.id,
        quantity: 1,
      });
      toast.success('Added to cart!');
    } catch (error) {
      console.error('Error adding to cart:', error);
      toast.error('Failed to add to cart');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50" data-testid="customer-dashboard">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2" data-testid="dashboard-title">Welcome, {user?.name}!</h1>
          <p className="text-gray-600">Browse and shop from thousands of products</p>
        </div>

        {/* Categories */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Shop by Category</h2>
          <div className="flex gap-3 overflow-x-auto pb-2" data-testid="categories-list">
            <Badge
              variant={selectedCategory === 'all' ? 'default' : 'outline'}
              className="cursor-pointer px-4 py-2"
              onClick={() => setSelectedCategory('all')}
              data-testid="category-all"
            >
              All Products
            </Badge>
            {categories.map((category) => (
              <Badge
                key={category.id}
                variant={selectedCategory === category.id ? 'default' : 'outline'}
                className="cursor-pointer px-4 py-2 whitespace-nowrap"
                onClick={() => setSelectedCategory(category.id)}
                data-testid={`category-${category.name.toLowerCase().replace(/ /g, '-')}`}
              >
                {category.name}
              </Badge>
            ))}
          </div>
        </div>

        {/* Search and Filters */}
        <div className="mb-8 grid md:grid-cols-3 gap-4" data-testid="search-filters">
          <form onSubmit={handleSearch} className="md:col-span-2">
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="Search products..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                data-testid="search-input"
              />
              <Button type="submit" data-testid="search-button">
                <Search className="h-4 w-4" />
              </Button>
            </div>
          </form>
          <Select value={priceRange} onValueChange={setPriceRange}>
            <SelectTrigger data-testid="price-filter">
              <SelectValue placeholder="Price Range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Prices</SelectItem>
              <SelectItem value="low">Under $10</SelectItem>
              <SelectItem value="medium">$10 - $50</SelectItem>
              <SelectItem value="high">Above $50</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Products Grid */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-600">Loading products...</p>
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-12" data-testid="no-products">
            <Package className="h-16 w-16 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-600">No products found</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6" data-testid="products-grid">
            {products.map((product) => (
              <Card
                key={product.id}
                className="hover:shadow-lg transition-shadow cursor-pointer"
                data-testid={`product-${product.id}`}
              >
                <div onClick={() => navigate(`/product/${product.id}`)}>
                  <div className="aspect-square overflow-hidden bg-gray-100">
                    <img
                      src={product.image_url || 'https://via.placeholder.com/300'}
                      alt={product.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <CardContent className="pt-4">
                    <h3 className="font-semibold mb-1 line-clamp-2" data-testid={`product-name-${product.id}`}>
                      {product.name}
                    </h3>
                    <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                      {product.description}
                    </p>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-lg font-bold text-blue-600" data-testid={`product-price-${product.id}`}>
                        ${product.price.toFixed(2)}
                      </span>
                      {product.rating > 0 && (
                        <div className="flex items-center">
                          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                          <span className="text-sm ml-1">{product.rating}</span>
                        </div>
                      )}
                    </div>
                    {product.stock > 0 ? (
                      <Badge variant="outline" className="text-green-600">
                        In Stock: {product.stock}
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-red-600">
                        Out of Stock
                      </Badge>
                    )}
                  </CardContent>
                </div>
                <CardFooter>
                  <Button
                    className="w-full"
                    onClick={() => addToCart(product)}
                    disabled={product.stock === 0}
                    data-testid={`add-to-cart-${product.id}`}
                  >
                    <ShoppingCart className="mr-2 h-4 w-4" />
                    Add to Cart
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CustomerDashboard;