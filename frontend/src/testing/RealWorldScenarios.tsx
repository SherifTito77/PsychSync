/**
 * Real-World Testing Scenarios for Mobile Optimization
 * Demonstrates practical usage scenarios that developers will encounter
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  SimpleResponsiveList,
  VirtualizedList,
  MobileResponsiveDashboard,
  useMobileResponsive,
  useCrossPlatformOptimizations
} from '../components/mobile';
import {
  mobileBrowserCompatibility,
  UXUsabilityDefectDetector
} from '../utils';

// Real-world scenario data generators
class RealWorldDataGenerator {
  static generateEcommerceProducts() {
    return Array.from({ length: 50 }, (_, i) => ({
      id: `product-${i + 1}`,
      name: `Premium Product ${i + 1}`,
      price: Math.floor(Math.random() * 500) + 50,
      rating: (Math.random() * 2 + 3).toFixed(1),
      reviews: Math.floor(Math.random() * 1000) + 10,
      inStock: Math.random() > 0.2,
      category: ['Electronics', 'Clothing', 'Home', 'Sports', 'Books'][i % 5],
      image: `https://picsum.photos/200/200?random=${i + 1}`,
      badge: Math.random() > 0.8 ? ['Bestseller', 'New', 'Sale'][Math.floor(Math.random() * 3)] : null
    }));
  }

  static generateSocialMediaFeed() {
    return Array.from({ length: 100 }, (_, i) => ({
      id: `post-${i + 1}`,
      author: {
        name: `User ${i + 1}`,
        username: `user${i + 1}`,
        avatar: `https://picsum.photos/50/50?random=${i + 1}`,
        verified: Math.random() > 0.7
      },
      content: `This is sample post content ${i + 1}. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore.`,
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      likes: Math.floor(Math.random() * 1000),
      comments: Math.floor(Math.random() * 100),
      shares: Math.floor(Math.random() * 50),
      hasImage: Math.random() > 0.5,
      media: Math.random() > 0.5 ? `https://picsum.photos/400/300?random=${i + 1}` : null
    }));
  }

  static generateEmailInbox() {
    return Array.from({ length: 200 }, (_, i) => ({
      id: `email-${i + 1}`,
      sender: `Sender ${i + 1}`,
      senderEmail: `sender${i + 1}@example.com`,
      subject: `Important Email Subject ${i + 1}`,
      preview: `This is the preview text for email ${i + 1}. It gives a brief overview of the email content...`,
      timestamp: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      read: Math.random() > 0.6,
      starred: Math.random() > 0.8,
      hasAttachment: Math.random() > 0.3,
      folder: ['Inbox', 'Sent', 'Drafts', 'Important'][Math.floor(Math.random() * 4)],
      priority: ['high', 'normal', 'low'][Math.floor(Math.random() * 3)]
    }));
  }

  static generateHealthRecords() {
    return Array.from({ length: 100 }, (_, i) => ({
      id: `record-${i + 1}`,
      date: new Date(Date.now() - Math.random() * 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      type: ['Check-up', 'Lab Result', 'Prescription', 'Vaccination', 'Specialist Visit'][i % 5],
      provider: `Dr. ${['Smith', 'Johnson', 'Williams', 'Brown', 'Jones'][i % 5]}`,
      diagnosis: `Medical record entry ${i + 1}`,
      status: ['Completed', 'Scheduled', 'Pending', 'Cancelled'][Math.floor(Math.random() * 4)],
      urgent: Math.random() > 0.9,
      notes: `Detailed medical notes for record ${i + 1}. Patient showed improvement in symptoms.`
    }));
  }
}

// Real-world component implementations
export const EcommerceProductList: React.FC = () => {
  const [products] = useState(RealWorldDataGenerator.generateEcommerceProducts());
  const [filters, setFilters] = useState({ category: 'all', inStock: false });
  const { isMobile, breakpoints } = useMobileResponsive();

  const filteredProducts = products.filter(product => {
    const categoryMatch = filters.category === 'all' || product.category === filters.category;
    const stockMatch = !filters.inStock || product.inStock;
    return categoryMatch && stockMatch;
  });

  const renderProduct = (product: any) => (
    <div className={`product-card ${!product.inStock ? 'out-of-stock' : ''}`}>
      <div className="product-image-container">
        <img src={product.image} alt={product.name} className="product-image" />
        {product.badge && <span className="product-badge">{product.badge}</span>}
      </div>

      <div className="product-info">
        <h3 className="product-name">{product.name}</h3>
        <p className="product-category">{product.category}</p>

        <div className="product-rating">
          <span className="stars">{'★'.repeat(Math.floor(parseFloat(product.rating)))}</span>
          <span className="rating-value">{product.rating}</span>
          <span className="review-count">({product.reviews})</span>
        </div>

        <div className="product-price">${product.price}</div>

        {!product.inStock && <p className="out-of-stock-text">Out of Stock</p>}
      </div>

      <button className="add-to-cart" disabled={!product.inStock}>
        {product.inStock ? 'Add to Cart' : 'Out of Stock'}
      </button>
    </div>
  );

  return (
    <div className="ecommerce-scenario">
      <style jsx>{`
        .ecommerce-scenario {
          padding: ${isMobile ? '12px' : '24px'};
          max-width: 1200px;
          margin: 0 auto;
        }

        .scenario-header {
          text-align: center;
          margin-bottom: 24px;
        }

        .filters {
          display: flex;
          gap: 12px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }

        .filter-select {
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 6px;
          background: white;
        }

        .results-count {
          margin-bottom: 16px;
          font-size: 14px;
          color: #666;
        }

        .product-card {
          background: white;
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 16px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          display: ${isMobile ? 'block' : 'flex'};
          gap: 16px;
          transition: transform 0.2s ease;
        }

        .product-card:hover {
          transform: translateY(-2px);
        }

        .product-image-container {
          position: relative;
          width: ${isMobile ? '100%' : '120px'};
          height: ${isMobile ? '200px' : '120px'};
        }

        .product-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
          border-radius: 8px;
        }

        .product-badge {
          position: absolute;
          top: 8px;
          right: 8px;
          background: #ff4444;
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
        }

        .product-info {
          flex: 1;
        }

        .product-name {
          margin: 0 0 8px 0;
          font-size: 16px;
          font-weight: 600;
        }

        .product-category {
          margin: 0 0 8px 0;
          color: #666;
          font-size: 14px;
        }

        .product-rating {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }

        .stars {
          color: #ffc107;
        }

        .rating-value {
          font-weight: 600;
        }

        .review-count {
          color: #666;
          font-size: 12px;
        }

        .product-price {
          font-size: 20px;
          font-weight: bold;
          color: #2ecc71;
          margin-bottom: 8px;
        }

        .out-of-stock-text {
          color: #e74c3c;
          font-weight: 600;
          margin: 8px 0;
        }

        .add-to-cart {
          padding: 12px 24px;
          background: #3498db;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
          transition: background 0.2s ease;
          height: fit-content;
        }

        .add-to-cart:hover:not(:disabled) {
          background: #2980b9;
        }

        .add-to-cart:disabled {
          background: #bdc3c7;
          cursor: not-allowed;
        }

        .out-of-stock {
          opacity: 0.7;
        }

        @media (max-width: 768px) {
          .product-card {
            flex-direction: column;
          }

          .product-image-container {
            height: 200px;
          }
        }
      `}</style>

      <div className="scenario-header">
        <h2>🛒 E-commerce Product Listing</h2>
        <p>Mobile-optimized product grid with filters and real-world data</p>
      </div>

      <div className="filters">
        <select
          className="filter-select"
          value={filters.category}
          onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
        >
          <option value="all">All Categories</option>
          <option value="Electronics">Electronics</option>
          <option value="Clothing">Clothing</option>
          <option value="Home">Home</option>
          <option value="Sports">Sports</option>
          <option value="Books">Books</option>
        </select>

        <label className="filter-checkbox">
          <input
            type="checkbox"
            checked={filters.inStock}
            onChange={(e) => setFilters(prev => ({ ...prev, inStock: e.target.checked }))}
          />
          In Stock Only
        </label>
      </div>

      <div className="results-count">
        Showing {filteredProducts.length} of {products.length} products
      </div>

      {filteredProducts.length === 0 ? (
        <div className="no-results">
          <p>No products match your filters.</p>
        </div>
      ) : (
        <SimpleResponsiveList
          items={filteredProducts}
          renderItem={renderProduct}
          estimatedItemHeight={isMobile ? 300 : 150}
          className="product-list"
        />
      )}
    </div>
  );
};

export const SocialMediaFeed: React.FC = () => {
  const [posts] = useState(RealWorldDataGenerator.generateSocialMediaFeed());
  const { isMobile } = useMobileResponsive();
  const [newPostCount, setNewPostCount] = useState(0);

  // Simulate new posts coming in
  useEffect(() => {
    const interval = setInterval(() => {
      setNewPostCount(prev => prev + 1);
    }, 10000); // New post every 10 seconds

    return () => clearInterval(interval);
  }, []);

  const renderPost = (post: any) => (
    <div className="social-post">
      <div className="post-header">
        <div className="author-info">
          <img src={post.author.avatar} alt={post.author.name} className="author-avatar" />
          <div className="author-details">
            <div className="author-name">
              {post.author.name}
              {post.author.verified && <span className="verified-badge">✓</span>}
            </div>
            <div className="author-username">@{post.author.username}</div>
          </div>
        </div>
        <div className="post-timestamp">
          {new Date(post.timestamp).toLocaleDateString()}
        </div>
      </div>

      <div className="post-content">
        <p>{post.content}</p>
        {post.hasImage && (
          <img src={post.media} alt="Post media" className="post-image" />
        )}
      </div>

      <div className="post-actions">
        <button className="action-btn">
          <span>❤️</span> {post.likes}
        </button>
        <button className="action-btn">
          <span>💬</span> {post.comments}
        </button>
        <button className="action-btn">
          <span>🔄</span> {post.shares}
        </button>
      </div>
    </div>
  );

  return (
    <div className="social-media-scenario">
      <style jsx>{`
        .social-media-scenario {
          max-width: 600px;
          margin: 0 auto;
          padding: ${isMobile ? '12px' : '24px'};
        }

        .scenario-header {
          text-align: center;
          margin-bottom: 24px;
        }

        .new-posts-indicator {
          background: #3498db;
          color: white;
          padding: 8px 16px;
          border-radius: 20px;
          text-align: center;
          margin-bottom: 16px;
          font-size: 14px;
        }

        .social-post {
          background: white;
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 16px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .post-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .author-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .author-avatar {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          object-fit: cover;
        }

        .author-name {
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .verified-badge {
          background: #3498db;
          color: white;
          border-radius: 50%;
          width: 16px;
          height: 16px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
        }

        .author-username {
          color: #666;
          font-size: 14px;
        }

        .post-timestamp {
          color: #666;
          font-size: 12px;
        }

        .post-content {
          margin-bottom: 12px;
        }

        .post-content p {
          margin: 0 0 12px 0;
          line-height: 1.5;
        }

        .post-image {
          width: 100%;
          border-radius: 8px;
          margin-bottom: 12px;
        }

        .post-actions {
          display: flex;
          gap: 16px;
          padding-top: 12px;
          border-top: 1px solid #f0f0f0;
        }

        .action-btn {
          background: none;
          border: none;
          display: flex;
          align-items: center;
          gap: 4px;
          color: #666;
          cursor: pointer;
          font-size: 14px;
          padding: 4px 8px;
          border-radius: 4px;
          transition: background 0.2s ease;
        }

        .action-btn:hover {
          background: #f8f9fa;
        }

        @media (max-width: 768px) {
          .social-media-scenario {
            padding: 12px;
          }

          .post-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }
        }
      `}</style>

      <div className="scenario-header">
        <h2>📱 Social Media Feed</h2>
        <p>Infinite scroll feed with real-time updates</p>
      </div>

      {newPostCount > 0 && (
        <div className="new-posts-indicator">
          {newPostCount} new posts available
        </div>
      )}

      <VirtualizedList
        items={posts}
        renderItem={renderPost}
        estimatedItemHeight={300}
        className="social-feed"
      />
    </div>
  );
};

export const EmailInbox: React.FC = () => {
  const [emails] = useState(RealWorldDataGenerator.generateEmailInbox());
  const [selectedFolder, setSelectedFolder] = useState('all');
  const { isMobile } = useMobileResponsive();

  const filteredEmails = emails.filter(email =>
    selectedFolder === 'all' || email.folder === selectedFolder
  );

  const renderEmail = (email: any) => (
    <div className={`email-item ${email.read ? 'read' : 'unread'} ${email.urgent ? 'urgent' : ''}`}>
      <div className="email-header">
        <div className="sender-info">
          <input
            type="checkbox"
            className="email-checkbox"
            aria-label="Select email"
          />
          <button className={`star-btn ${email.starred ? 'starred' : ''}`}>
            {email.starred ? '⭐' : '☆'}
          </button>
          <span className="sender-name">{email.sender}</span>
        </div>
        <div className="email-meta">
          {email.hasAttachment && <span className="attachment-icon">📎</span>}
          <span className="email-date">
            {new Date(email.timestamp).toLocaleDateString()}
          </span>
        </div>
      </div>

      <div className="email-content">
        <h4 className={`email-subject ${email.urgent ? 'urgent-subject' : ''}`}>
          {email.urgent && '🚨 '}{email.subject}
        </h4>
        <p className="email-preview">{email.preview}</p>
      </div>

      <div className="email-footer">
        <span className={`priority-badge ${email.priority}`}>
          {email.priority}
        </span>
        <span className="folder-tag">{email.folder}</span>
      </div>
    </div>
  );

  return (
    <div className="email-inbox-scenario">
      <style jsx>{`
        .email-inbox-scenario {
          padding: ${isMobile ? '12px' : '24px'};
          max-width: 1000px;
          margin: 0 auto;
        }

        .scenario-header {
          text-align: center;
          margin-bottom: 24px;
        }

        .folder-tabs {
          display: flex;
          gap: 8px;
          margin-bottom: 20px;
          border-bottom: 2px solid #e0e0e0;
          overflow-x: auto;
        }

        .folder-tab {
          padding: 12px 20px;
          background: none;
          border: none;
          border-bottom: 3px solid transparent;
          cursor: pointer;
          white-space: nowrap;
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .folder-tab:hover {
          background: #f8f9fa;
        }

        .folder-tab.active {
          border-bottom-color: #3498db;
          color: #3498db;
        }

        .email-item {
          background: white;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          margin-bottom: 8px;
          padding: 16px;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .email-item:hover {
          border-color: #3498db;
          box-shadow: 0 2px 4px rgba(52, 152, 219, 0.1);
        }

        .email-item.unread {
          background: #f8f9ff;
          border-left: 4px solid #3498db;
        }

        .email-item.urgent {
          border-left-color: #e74c3c;
        }

        .email-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .sender-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .email-checkbox {
          margin: 0;
        }

        .star-btn {
          background: none;
          border: none;
          font-size: 16px;
          cursor: pointer;
          padding: 4px;
        }

        .star-btn.starred {
          color: #f39c12;
        }

        .sender-name {
          font-weight: 600;
          font-size: 14px;
        }

        .email-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          color: #666;
        }

        .attachment-icon {
          color: #e74c3c;
        }

        .email-content {
          margin-bottom: 8px;
        }

        .email-subject {
          margin: 0 0 4px 0;
          font-size: 16px;
          font-weight: 500;
        }

        .email-subject.urgent-subject {
          color: #e74c3c;
        }

        .email-preview {
          margin: 0;
          color: #666;
          font-size: 14px;
          line-height: 1.4;
        }

        .email-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .priority-badge {
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
        }

        .priority-badge.high {
          background: #ffebee;
          color: #e74c3c;
        }

        .priority-badge.normal {
          background: #f3f3f3;
          color: #666;
        }

        .priority-badge.low {
          background: #e8f5e8;
          color: #27ae60;
        }

        .folder-tag {
          font-size: 12px;
          color: #999;
        }

        @media (max-width: 768px) {
          .email-inbox-scenario {
            padding: 12px;
          }

          .folder-tabs {
            gap: 4px;
          }

          .folder-tab {
            padding: 8px 12px;
            font-size: 12px;
          }

          .email-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }

          .sender-info {
            gap: 8px;
          }

          .email-footer {
            flex-direction: column;
            align-items: flex-start;
            gap: 4px;
          }
        }
      `}</style>

      <div className="scenario-header">
        <h2>📧 Email Inbox</h2>
        <p>Mobile-optimized email client with folders and priorities</p>
      </div>

      <div className="folder-tabs">
        <button
          className={`folder-tab ${selectedFolder === 'all' ? 'active' : ''}`}
          onClick={() => setSelectedFolder('all')}
        >
          All ({emails.length})
        </button>
        <button
          className={`folder-tab ${selectedFolder === 'Inbox' ? 'active' : ''}`}
          onClick={() => setSelectedFolder('Inbox')}
        >
          Inbox ({emails.filter(e => e.folder === 'Inbox').length})
        </button>
        <button
          className={`folder-tab ${selectedFolder === 'Important' ? 'active' : ''}`}
          onClick={() => setSelectedFolder('Important')}
        >
          Important ({emails.filter(e => e.folder === 'Important').length})
        </button>
        <button
          className={`folder-tab ${selectedFolder === 'Sent' ? 'active' : ''}`}
          onClick={() => setSelectedFolder('Sent')}
        >
          Sent ({emails.filter(e => e.folder === 'Sent').length})
        </button>
      </div>

      <VirtualizedList
        items={filteredEmails}
        renderItem={renderEmail}
        estimatedItemHeight={120}
        className="email-list"
      />
    </div>
  );
};

export const HealthRecords: React.FC = () => {
  const [records] = useState(RealWorldDataGenerator.generateHealthRecords());
  const [selectedType, setSelectedType] = useState('all');
  const { isMobile } = useMobileResponsive();

  const filteredRecords = records.filter(record =>
    selectedType === 'all' || record.type === selectedType
  );

  const renderRecord = (record: any) => (
    <div className={`health-record ${record.urgent ? 'urgent' : ''}`}>
      <div className="record-header">
        <div className="record-type">
          <span className="type-icon">
            {record.type === 'Check-up' && '🩺'}
            {record.type === 'Lab Result' && '🔬'}
            {record.type === 'Prescription' && '💊'}
            {record.type === 'Vaccination' && '💉'}
            {record.type === 'Specialist Visit' && '👨‍⚕️'}
          </span>
          <span className="type-name">{record.type}</span>
        </div>
        <div className="record-date">{record.date}</div>
      </div>

      <div className="record-content">
        <h4 className="record-diagnosis">{record.diagnosis}</h4>
        <p className="record-provider">Dr. {record.provider}</p>
        {record.notes && <p className="record-notes">{record.notes}</p>}
      </div>

      <div className="record-footer">
        <span className={`status-badge ${record.status}`}>
          {record.status}
        </span>
        {record.urgent && <span className="urgent-badge">Urgent</span>}
      </div>
    </div>
  );

  return (
    <div className="health-records-scenario">
      <style jsx>{`
        .health-records-scenario {
          padding: ${isMobile ? '12px' : '24px'};
          max-width: 800px;
          margin: 0 auto;
        }

        .scenario-header {
          text-align: center;
          margin-bottom: 24px;
        }

        .type-filter {
          display: flex;
          gap: 8px;
          margin-bottom: 20px;
          flex-wrap: wrap;
        }

        .type-button {
          padding: 8px 16px;
          border: 1px solid #ddd;
          background: white;
          border-radius: 20px;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .type-button:hover {
          border-color: #27ae60;
        }

        .type-button.active {
          background: #27ae60;
          color: white;
          border-color: #27ae60;
        }

        .health-record {
          background: white;
          border-radius: 12px;
          padding: 16px;
          margin-bottom: 16px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          border-left: 4px solid #27ae60;
        }

        .health-record.urgent {
          border-left-color: #e74c3c;
          background: #fff5f5;
        }

        .record-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .record-type {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .type-icon {
          font-size: 20px;
        }

        .type-name {
          font-weight: 600;
          color: #333;
        }

        .record-date {
          color: #666;
          font-size: 14px;
        }

        .record-content {
          margin-bottom: 12px;
        }

        .record-diagnosis {
          margin: 0 0 8px 0;
          font-size: 16px;
          font-weight: 500;
          color: #333;
        }

        .record-provider {
          margin: 0 0 8px 0;
          color: #666;
          font-size: 14px;
        }

        .record-notes {
          margin: 0;
          color: #888;
          font-size: 13px;
          line-height: 1.4;
        }

        .record-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .status-badge {
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
          text-transform: uppercase;
        }

        .status-badge.completed {
          background: #d4edda;
          color: #155724;
        }

        .status-badge.scheduled {
          background: #cce5ff;
          color: #004085;
        }

        .status-badge.pending {
          background: #fff3cd;
          color: #856404;
        }

        .status-badge.cancelled {
          background: #f8d7da;
          color: #721c24;
        }

        .urgent-badge {
          background: #e74c3c;
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
        }

        @media (max-width: 768px) {
          .health-records-scenario {
            padding: 12px;
          }

          .record-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 4px;
          }

          .record-footer {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }
        }
      `}</style>

      <div className="scenario-header">
        <h2>🏥 Health Records</h2>
        <p>Mobile-optimized medical records with privacy considerations</p>
      </div>

      <div className="type-filter">
        <button
          className={`type-button ${selectedType === 'all' ? 'active' : ''}`}
          onClick={() => setSelectedType('all')}
        >
          All Types
        </button>
        <button
          className={`type-button ${selectedType === 'Check-up' ? 'active' : ''}`}
          onClick={() => setSelectedType('Check-up')}
        >
          Check-ups
        </button>
        <button
          className={`type-button ${selectedType === 'Lab Result' ? 'active' : ''}`}
          onClick={() => setSelectedType('Lab Result')}
        >
          Lab Results
        </button>
        <button
          className={`type-button ${selectedType === 'Prescription' ? 'active' : ''}`}
          onClick={() => setSelectedType('Prescription')}
        >
          Prescriptions
        </button>
        <button
          className={`type-button ${selectedType === 'Vaccination' ? 'active' : ''}`}
          onClick={() => setSelectedType('Vaccination')}
        >
          Vaccinations
        </button>
      </div>

      <SimpleResponsiveList
        items={filteredRecords}
        renderItem={renderRecord}
        estimatedItemHeight={140}
        className="health-list"
      />
    </div>
  );
};

// Main scenarios component
export const RealWorldTestingScenarios: React.FC = () => {
  const [activeScenario, setActiveScenario] = useState<'ecommerce' | 'social' | 'email' | 'health'>('ecommerce');
  const { isMobile } = useMobileResponsive();

  const scenarios = {
    ecommerce: {
      name: 'E-commerce Products',
      description: 'Product listing with filters and cards',
      component: EcommerceProductList
    },
    social: {
      name: 'Social Media Feed',
      description: 'Infinite scroll with real-time updates',
      component: SocialMediaFeed
    },
    email: {
      name: 'Email Inbox',
      description: 'Email client with folders and priorities',
      component: EmailInbox
    },
    health: {
      name: 'Health Records',
      description: 'Medical records with privacy features',
      component: HealthRecords
    }
  };

  const ActiveComponent = scenarios[activeScenario].component;

  return (
    <div className="real-world-scenarios">
      <style jsx>{`
        .real-world-scenarios {
          min-height: 100vh;
          background: #f8f9fa;
        }

        .header {
          background: white;
          padding: 24px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          margin-bottom: 24px;
        }

        .header h1 {
          text-align: center;
          margin: 0 0 8px 0;
          font-size: 28px;
          color: #333;
        }

        .header p {
          text-align: center;
          margin: 0;
          color: #666;
          font-size: 16px;
        }

        .scenario-selector {
          display: flex;
          justify-content: center;
          gap: 12px;
          margin-top: 24px;
          flex-wrap: wrap;
        }

        .scenario-button {
          padding: 12px 24px;
          border: 2px solid #ddd;
          background: white;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 14px;
          font-weight: 500;
          min-width: 150px;
        }

        .scenario-button:hover {
          border-color: #007AFF;
          background: #f8f9ff;
        }

        .scenario-button.active {
          border-color: #007AFF;
          background: #007AFF;
          color: white;
        }

        .scenario-content {
          padding: 0 24px 24px;
        }

        @media (max-width: 768px) {
          .header {
            padding: 16px;
          }

          .header h1 {
            font-size: 24px;
          }

          .scenario-selector {
            gap: 8px;
          }

          .scenario-button {
            padding: 10px 16px;
            font-size: 13px;
            min-width: 120px;
          }

          .scenario-content {
            padding: 0 12px 12px;
          }
        }
      `}</style>

      <div className="header">
        <h1>🌍 Real-World Mobile Scenarios</h1>
        <p>Test cross-platform compatibility with practical applications</p>

        <div className="scenario-selector">
          {Object.entries(scenarios).map(([key, scenario]) => (
            <button
              key={key}
              className={`scenario-button ${activeScenario === key ? 'active' : ''}`}
              onClick={() => setActiveScenario(key as keyof typeof scenarios)}
            >
              {scenario.name}
            </button>
          ))}
        </div>
      </div>

      <div className="scenario-content">
        <ActiveComponent />
      </div>
    </div>
  );
};

export default RealWorldTestingScenarios;