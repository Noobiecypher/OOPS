import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import Navbar from '@/components/Navbar';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { productsAPI, cartAPI, feedbackAPI } from '@/api/api';
import { toast } from 'sonner';
import { ShoppingCart, Star, Store, ArrowLeft } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const ProductDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [product, setProduct] = useState(null);
  const [feedback, setFeedback] = useState([]);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  
  // Feedback form
  const [rating, setRating] = useState('5');
  const [comment, setComment] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  useEffect(() => {
    fetchProduct();
    fetchFeedback();
  }, [id]);

  const fetchProduct = async () => {
    try {
      const response = await productsAPI.getById(id);
      setProduct(response.data);
    } catch (error) {
      console.error('Error fetching product:', error);
      toast.error('Product not found');
      navigate('/customer/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const fetchFeedback = async () => {
    try {
      const response = await feedbackAPI.getProductFeedback(id);
      setFeedback(response.data);
    } catch (error) {
      console.error('Error fetching feedback:', error);
    }
  };

  const addToCart = async () => {
    try {
      await cartAPI.addItem(user.id, {
        product_id: product.id,
        quantity: quantity,
      });
      toast.success('Added to cart!');
    } catch (error) {
      console.error('Error adding to cart:', error);
      toast.error('Failed to add to cart');
    }
  };

  const handleSubmitFeedback = async (e) => {
    e.preventDefault();
    if (!user || user.role !== 'customer') {
      toast.error('Only customers can leave feedback');
      return;
    }

    setSubmittingFeedback(true);
    try {
      await feedbackAPI.create(user.id, {
        product_id: id,
        rating: parseInt(rating),
        comment: comment,
      });
      toast.success('Feedback submitted!');
      setComment('');
      fetchFeedback();
      fetchProduct();
    } catch (error) {
      console.error('Error submitting feedback:', error);
      toast.error('Failed to submit feedback');
    } finally {
      setSubmittingFeedback(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-7xl mx-auto px-4 py-8 text-center">
          <p>Loading product...</p>
        </div>
      </div>
    );
  }

  if (!product) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50" data-testid="product-detail-page">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="mb-6"
          data-testid="back-button"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>

        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Product Image */}
          <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={product.image_url || 'https://via.placeholder.com/600'}
              alt={product.name}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Product Details */}
          <div data-testid="product-details">
            <h1 className="text-3xl font-bold mb-2" data-testid="product-name">{product.name}</h1>
            {product.seller_name && (
              <div className="flex items-center text-gray-600 mb-4">
                <Store className="h-4 w-4 mr-1" />
                <span>Sold by: {product.seller_name}</span>
              </div>
            )}
            
            {product.rating > 0 && (
              <div className="flex items-center mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`h-5 w-5 ${
                      i < Math.floor(product.rating)
                        ? 'fill-yellow-400 text-yellow-400'
                        : 'text-gray-300'
                    }`}
                  />
                ))}
                <span className="ml-2 text-gray-600">({feedback.length} reviews)</span>
              </div>
            )}

            <div className="mb-4">
              <span className="text-3xl font-bold text-blue-600" data-testid="product-price">
                ${product.price.toFixed(2)}
              </span>
              <span className="text-gray-600 ml-2">per {product.unit}</span>
            </div>

            <div className="mb-6">
              {product.stock > 0 ? (
                <Badge variant="outline" className="text-green-600">
                  In Stock: {product.stock} {product.unit}s available
                </Badge>
              ) : (
                <Badge variant="outline" className="text-red-600">
                  Out of Stock
                </Badge>
              )}
            </div>

            <div className="mb-6">
              <h3 className="font-semibold mb-2">Description</h3>
              <p className="text-gray-600">{product.description}</p>
            </div>

            {user?.role === 'customer' && (
              <div className="space-y-4">
                <div>
                  <Label>Quantity</Label>
                  <div className="flex items-center gap-3 mt-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setQuantity(Math.max(1, quantity - 1))}
                      data-testid="decrease-quantity"
                    >
                      -
                    </Button>
                    <span className="w-12 text-center" data-testid="quantity-value">{quantity}</span>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}
                      disabled={quantity >= product.stock}
                      data-testid="increase-quantity"
                    >
                      +
                    </Button>
                  </div>
                </div>
                <Button
                  size="lg"
                  className="w-full"
                  onClick={addToCart}
                  disabled={product.stock === 0}
                  data-testid="add-to-cart-button"
                >
                  <ShoppingCart className="mr-2 h-5 w-5" />
                  Add to Cart
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Reviews Section */}
        <div className="mb-12" data-testid="reviews-section">
          <h2 className="text-2xl font-bold mb-6">Customer Reviews</h2>
          
          {user?.role === 'customer' && (
            <Card className="mb-6" data-testid="feedback-form">
              <CardContent className="pt-6">
                <form onSubmit={handleSubmitFeedback}>
                  <div className="space-y-4">
                    <div>
                      <Label>Rating</Label>
                      <Select value={rating} onValueChange={setRating}>
                        <SelectTrigger data-testid="rating-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="5">5 Stars - Excellent</SelectItem>
                          <SelectItem value="4">4 Stars - Good</SelectItem>
                          <SelectItem value="3">3 Stars - Average</SelectItem>
                          <SelectItem value="2">2 Stars - Poor</SelectItem>
                          <SelectItem value="1">1 Star - Terrible</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="comment">Comment (optional)</Label>
                      <Textarea
                        id="comment"
                        placeholder="Share your experience..."
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        data-testid="comment-textarea"
                      />
                    </div>
                    <Button type="submit" disabled={submittingFeedback} data-testid="submit-feedback-btn">
                      {submittingFeedback ? 'Submitting...' : 'Submit Review'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {feedback.length === 0 ? (
            <p className="text-gray-600">No reviews yet. Be the first to review this product!</p>
          ) : (
            <div className="space-y-4" data-testid="feedback-list">
              {feedback.map((review) => (
                <Card key={review.id} data-testid={`review-${review.id}`}>
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-semibold">{review.user_name}</p>
                        <div className="flex items-center mt-1">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              className={`h-4 w-4 ${
                                i < review.rating
                                  ? 'fill-yellow-400 text-yellow-400'
                                  : 'text-gray-300'
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                      <span className="text-sm text-gray-500">
                        {new Date(review.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {review.comment && (
                      <p className="text-gray-600 mt-2">{review.comment}</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductDetailPage;