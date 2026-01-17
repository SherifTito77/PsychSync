/**
 * Product Management Prompts Library
 *
 * Main component for browsing and executing product management prompts.
 * Provides filtering, search, and categorization capabilities.
 */

import React, { useState, useEffect } from 'react';
import { Search, Filter, Clock, TrendingUp, Users, BarChart, Settings, Star } from 'lucide-react';
import { api } from '@/services/api';
import type { Prompt, Category, PromptExecution } from '@/types/productManagement';

interface ProductManagementPromptsProps {
  onExecute?: (prompt: Prompt) => void;
}

export const ProductManagementPrompts: React.FC<ProductManagementPromptsProps> = ({
  onExecute
}) => {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [complexityFilter, setComplexityFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [favorites, setFavorites] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadCategories();
    loadPrompts();
    loadFavorites();
  }, [selectedCategory, complexityFilter, typeFilter]);

  const loadCategories = async () => {
    try {
      const response = await api.get('/product-management/categories');
      setCategories(response.data);
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  const loadPrompts = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (selectedCategory) params.category = selectedCategory;
      if (complexityFilter !== 'all') params.complexity = complexityFilter;
      if (typeFilter !== 'all') params.type = typeFilter;

      const response = await api.get('/product-management/prompts', { params });
      setPrompts(response.data.prompts);
    } catch (error) {
      console.error('Failed to load prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFavorites = async () => {
    try {
      const response = await api.get('/product-management/favorites');
      const favIds = new Set(response.data.map((p: Prompt) => p.id));
      setFavorites(favIds);
    } catch (error) {
      console.error('Failed to load favorites:', error);
    }
  };

  const toggleFavorite = async (promptId: string) => {
    try {
      if (favorites.has(promptId)) {
        await api.delete(`/product-management/favorites/${promptId}`);
        setFavorites(prev => {
          const next = new Set(prev);
          next.delete(promptId);
          return next;
        });
      } else {
        await api.post('/product-management/favorites', { prompt_id: promptId });
        setFavorites(prev => new Set(prev).add(promptId));
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  const executePrompt = async (prompt: Prompt) => {
    if (onExecute) {
      onExecute(prompt);
    }
  };

  const getCategoryIcon = (iconName: string) => {
    const icons: Record<string, React.ElementType> = {
      roadmap: TrendingUp,
      users: Users,
      'trending-up': TrendingUp,
      'chart-bar': BarChart,
      cog: Settings,
    };
    const Icon = icons[iconName] || Settings;
    return <Icon className="w-5 h-5" />;
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      strategic: 'bg-purple-100 text-purple-800',
      tactical: 'bg-blue-100 text-blue-800',
      analytical: 'bg-indigo-100 text-indigo-800',
      technical: 'bg-cyan-100 text-cyan-800',
      creative: 'bg-pink-100 text-pink-800',
      experimental: 'bg-orange-100 text-orange-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const filteredPrompts = prompts.filter(prompt =>
    prompt.prompt.toLowerCase().includes(searchQuery.toLowerCase()) ||
    prompt.use_cases.some(uc => uc.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="product-management-prompts">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Product Management Prompts
        </h1>
        <p className="text-gray-600">
          50 expertly curated prompts to accelerate your product decisions
        </p>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search prompts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Category Filter */}
          <div>
            <select
              value={selectedCategory || 'all'}
              onChange={(e) => setSelectedCategory(e.target.value === 'all' ? null : e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Categories</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>

          {/* Complexity Filter */}
          <div>
            <select
              value={complexityFilter}
              onChange={(e) => setComplexityFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Complexity</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>
      </div>

      {/* Categories */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`p-4 rounded-lg border-2 transition-all ${
            selectedCategory === null
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{prompts.length}</div>
            <div className="text-sm text-gray-600">All Prompts</div>
          </div>
        </button>
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={`p-4 rounded-lg border-2 transition-all ${
              selectedCategory === cat.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-center mb-2">
              {getCategoryIcon(cat.icon)}
            </div>
            <div className="text-center">
              <div className="text-lg font-bold text-gray-900">{cat.prompt_count}</div>
              <div className="text-xs text-gray-600">{cat.name}</div>
            </div>
          </button>
        ))}
      </div>

      {/* Prompts List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-gray-600">Loading prompts...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredPrompts.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No prompts found matching your criteria.</p>
            </div>
          ) : (
            filteredPrompts.map(prompt => (
              <PromptCard
                key={prompt.id}
                prompt={prompt}
                isFavorite={favorites.has(prompt.id)}
                onToggleFavorite={() => toggleFavorite(prompt.id)}
                onExecute={() => executePrompt(prompt)}
                getComplexityColor={getComplexityColor}
                getTypeColor={getTypeColor}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
};

interface PromptCardProps {
  prompt: Prompt;
  isFavorite: boolean;
  onToggleFavorite: () => void;
  onExecute: () => void;
  getComplexityColor: (complexity: string) => string;
  getTypeColor: (type: string) => string;
}

const PromptCard: React.FC<PromptCardProps> = ({
  prompt,
  isFavorite,
  onToggleFavorite,
  onExecute,
  getComplexityColor,
  getTypeColor
}) => {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-1 rounded text-xs font-medium ${getTypeColor(prompt.type)}`}>
              {prompt.type}
            </span>
            <span className={`px-2 py-1 rounded text-xs font-medium ${getComplexityColor(prompt.complexity)}`}>
              {prompt.complexity}
            </span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {prompt.prompt}
          </h3>
        </div>
        <button
          onClick={onToggleFavorite}
          className={`p-2 rounded-full transition-colors ${
            isFavorite
              ? 'text-yellow-500 hover:bg-yellow-50'
              : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
          }`}
        >
          <Star className={`w-5 h-5 ${isFavorite ? 'fill-current' : ''}`} />
        </button>
      </div>

      <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
        <div className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          <span>{prompt.estimated_time}</span>
        </div>
        <div className="flex items-center gap-1">
          <TrendingUp className="w-4 h-4" />
          <span>{prompt.outputs.length} outputs</span>
        </div>
      </div>

      <div className="mb-4">
        <p className="text-sm font-medium text-gray-700 mb-2">Expected Outputs:</p>
        <div className="flex flex-wrap gap-2">
          {prompt.outputs.slice(0, 3).map((output, idx) => (
            <span key={idx} className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-sm">
              {output}
            </span>
          ))}
          {prompt.outputs.length > 3 && (
            <span className="px-3 py-1 bg-gray-100 text-gray-500 rounded text-sm">
              +{prompt.outputs.length - 3} more
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-gray-100">
        <div className="text-xs text-gray-500">
          Use: {prompt.use_cases[0]}
        </div>
        <button
          onClick={onExecute}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          Execute Prompt
        </button>
      </div>
    </div>
  );
};

export default ProductManagementPrompts;
