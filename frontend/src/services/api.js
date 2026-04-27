/**
 * CadArena API Service v2.0
 * Enhanced API service with better error handling and integration
 */

import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with enhanced config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // 3 minutes for generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging and auth
api.interceptors.request.use(
  (config) => {
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    
    // Add timestamp to requests
    config.metadata = { startTime: new Date() };
    
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for enhanced error handling
api.interceptors.response.use(
  (response) => {
    const duration = new Date() - response.config.metadata.startTime;
    console.log(`✅ API Response: ${response.status} ${response.config.url} (${duration}ms)`);
    return response;
  },
  (error) => {
    const duration = error.config?.metadata ? new Date() - error.config.metadata.startTime : 0;
    console.error(`❌ API Error: ${error.config?.url} (${duration}ms)`, error.response?.data || error.message);
    const detail = error.response?.data?.detail;
    const detailMessage = Array.isArray(detail)
      ? detail.map((item) => item?.msg || item?.message || String(item)).join(', ')
      : detail;
    
    // Enhanced error handling
    if (error.code === 'ECONNREFUSED') {
      throw new Error('Backend server is not running. Please start the backend server on port 8000.');
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('Request timeout. The operation is taking too long.');
    } else if (error.response?.status === 400) {
      throw new Error(error.response?.data?.error || detailMessage || 'Bad request. Please check your input.');
    } else if (error.response?.status === 500) {
      throw new Error(error.response?.data?.error || detailMessage || 'Server error. Please try again later.');
    } else if (error.response?.status === 404) {
      throw new Error(detailMessage || 'API endpoint not found. Please check the backend server.');
    } else if (detailMessage) {
      throw new Error(detailMessage);
    } else if (error.response?.data?.error) {
      throw new Error(error.response.data.error);
    } else if (error.message.includes('Network Error')) {
      throw new Error('Cannot connect to backend server. Please check if it\'s running on port 8000.');
    } else {
      throw new Error(error.message || 'Network error. Please check your connection.');
    }
  }
);

/**
 * Enhanced CadArena API Service Class
 */
class CadArenaAPI {
  
  constructor() {
    this.isConnected = false;
    this.modelLoaded = false;
    this.lastHealthCheck = null;
  }
  
  /**
   * Check API health status with caching
   */
  async checkHealth(useCache = true) {
    try {
      // Use cached result if recent (within 30 seconds)
      if (useCache && this.lastHealthCheck && 
          (Date.now() - this.lastHealthCheck.timestamp) < 30000) {
        return this.lastHealthCheck.data;
      }

      const response = await api.get('/health');
      const data = response.data;
      
      this.isConnected = true;
      this.modelLoaded = data.model_loaded || false;
      this.lastHealthCheck = {
        data,
        timestamp: Date.now()
      };
      
      return data;
    } catch (error) {
      this.isConnected = false;
      this.modelLoaded = false;
      this.lastHealthCheck = null;
      throw new Error(`Health check failed: ${error.message}`);
    }
  }

  /**
   * Get detailed model information
   */
  async getModelInfo() {
    try {
      const response = await api.get('/model/info');
      const data = response.data;
      
      this.modelLoaded = data.model_info?.is_loaded || false;
      
      return data;
    } catch (error) {
      throw new Error(`Failed to get model info: ${error.message}`);
    }
  }

  /**
   * Load the model with progress tracking
   */
  async loadModel(onProgress = null) {
    try {
      console.log('🔄 Loading CadArena model...');
      
      if (onProgress) onProgress({ stage: 'starting', message: 'Initiating model loading...' });
      
      const response = await api.post('/model/load');
      const data = response.data;
      
      if (data.status === 'success') {
        this.modelLoaded = true;
        if (onProgress) onProgress({ stage: 'complete', message: 'Model loaded successfully!' });
      }
      
      return data;
    } catch (error) {
      this.modelLoaded = false;
      if (onProgress) onProgress({ stage: 'error', message: error.message });
      throw new Error(`Failed to load model: ${error.message}`);
    }
  }

  /**
   * Unload the model to free memory
   */
  async unloadModel() {
    try {
      const response = await api.post('/model/unload');
      this.modelLoaded = false;
      return response.data;
    } catch (error) {
      throw new Error(`Failed to unload model: ${error.message}`);
    }
  }

  /**
   * Generate a single floor plan
   * @param {Object} params - Generation parameters
   * @param {string} params.description - Floor plan description
   * @param {string} params.model - Model type ('baseline' or 'constraint_aware')
   * @param {string} params.style - Architectural style
   * @param {number} params.width - Image width (default: 512)
   * @param {number} params.height - Image height (default: 512)
   * @param {number} params.steps - Inference steps (default: 20)
   * @param {number} params.guidance - Guidance scale (default: 7.5)
   * @param {number} params.seed - Random seed (optional)
   * @param {boolean} params.save - Save to server (default: false)
   */
  async generateFloorPlan(params) {
    try {
      const {
        description,
        model = 'baseline',
        style = 'modern',
        width = 512,
        height = 512,
        steps = 20,
        guidance = 7.5,
        seed = null,
        save = false
      } = params;

      // Enhance description with style
      const enhancedDescription = `${style} ${description}`;

      const requestData = {
        description: enhancedDescription,
        width,
        height,
        steps,
        guidance,
        seed,
        save,
        model_type: model
      };

      console.log('🎨 Generating floor plan with params:', requestData);

      const response = await api.post('/generate', requestData);
      
      return {
        success: true,
        data: response.data,
        image: response.data.image,
        metadata: {
          description: response.data.description,
          parameters: response.data.parameters,
          timestamp: response.data.timestamp,
          generation_time: this.calculateGenerationTime(response.data.timestamp),
          // Mock metrics for now - can be enhanced later
          clip_score: 0.75 + Math.random() * 0.15,
          adjacency_score: 0.65 + Math.random() * 0.20,
          accuracy: 70 + Math.random() * 20
        }
      };

    } catch (error) {
      console.error('❌ Floor plan generation failed:', error);
      throw error;
    }
  }

  /**
   * Generate multiple variations of a floor plan
   * @param {Object} params - Generation parameters
   * @param {number} params.variations - Number of variations (default: 4)
   */
  async generateVariations(params) {
    try {
      const {
        description,
        variations = 4,
        model = 'baseline',
        style = 'modern',
        ...otherParams
      } = params;

      const enhancedDescription = `${style} ${description}`;

      const requestData = {
        description: enhancedDescription,
        variations,
        model_type: model,
        ...otherParams
      };

      console.log('🎨 Generating variations with params:', requestData);

      const response = await api.post('/generate/variations', requestData);
      
      return {
        success: true,
        data: response.data,
        variations: response.data.variations,
        metadata: {
          description: response.data.description,
          parameters: response.data.parameters,
          timestamp: response.data.timestamp,
          generation_time: this.calculateGenerationTime(response.data.timestamp)
        }
      };

    } catch (error) {
      console.error('❌ Variations generation failed:', error);
      throw error;
    }
  }

  /**
   * Generate batch of floor plans from multiple descriptions
   */
  async generateBatch(descriptions, params = {}, onProgress = null) {
    try {
      const requestData = {
        descriptions: descriptions.slice(0, 5), // Limit to 5
        ...params
      };

      console.log('🎨 Generating batch with params:', requestData);

      if (onProgress) {
        onProgress({ 
          stage: 'generating', 
          message: `Generating ${requestData.descriptions.length} floor plans...`,
          progress: 0
        });
      }

      const response = await api.post('/generate/batch', requestData);
      
      if (onProgress) {
        onProgress({ 
          stage: 'complete', 
          message: 'Batch generation completed!',
          progress: 100
        });
      }
      
      return {
        success: true,
        data: response.data,
        results: response.data.results
      };

    } catch (error) {
      if (onProgress) {
        onProgress({ stage: 'error', message: error.message });
      }
      console.error('❌ Batch generation failed:', error);
      throw error;
    }
  }

  /**
   * Get predefined prompts/presets
   */
  async getPresets() {
    try {
      const response = await api.get('/presets');
      return response.data;
    } catch (error) {
      console.warn('⚠️ Failed to load presets, using defaults');
      // Return default presets if API fails
      return {
        status: 'success',
        presets: {
          residential: [
            "Modern 1-bedroom studio apartment with open layout",
            "Cozy 2-bedroom apartment with separate kitchen and living room",
            "Spacious 3-bedroom family apartment with master suite",
            "Luxury 4-bedroom penthouse with balcony and walk-in closets"
          ],
          commercial: [
            "Small office space with reception area and meeting room",
            "Open-plan coworking space with flexible seating",
            "Retail store layout with customer area and storage",
            "Restaurant floor plan with dining area and kitchen"
          ],
          architectural_styles: [
            "Traditional colonial house floor plan",
            "Modern minimalist apartment layout",
            "Contemporary open-concept design",
            "Classic Victorian house floor plan"
          ]
        }
      };
    }
  }

  async getParseDesignModels() {
    const response = await api.get('/api/v1/parse-design-models');
    return response.data;
  }

  async listWorkspaceProjects(userId) {
    const response = await api.get('/api/v1/workspace/projects', {
      params: { user_id: userId },
    });
    return response.data;
  }

  async createWorkspaceProject(userId, name) {
    const response = await api.post('/api/v1/workspace/projects', {
      user_id: userId,
      name,
    });
    return response.data;
  }

  async getWorkspaceMessages(userId, projectId) {
    const response = await api.get(`/api/v1/workspace/projects/${encodeURIComponent(projectId)}/messages`, {
      params: { user_id: userId },
    });
    return response.data;
  }

  async generateWorkspaceDxf(projectId, payload) {
    const response = await api.post(
      `/api/v1/workspace/projects/${encodeURIComponent(projectId)}/generate-dxf`,
      payload,
    );
    return response.data;
  }

  dxfPreviewUrl(fileToken) {
    return `${API_BASE_URL}/api/v1/dxf/preview?file_token=${encodeURIComponent(fileToken)}&v=${Date.now()}`;
  }

  dxfDownloadUrl(fileToken, filename = 'cadarena_layout.dxf') {
    return `${API_BASE_URL}/api/v1/dxf/download?file_token=${encodeURIComponent(fileToken)}&filename=${encodeURIComponent(filename)}`;
  }

  async listCommunityQuestions(params = {}) {
    const response = await api.get('/api/v1/community/questions', {
      params: {
        query: params.query || undefined,
        tag: params.tag || undefined,
        discipline: params.discipline && params.discipline !== 'all' ? params.discipline : undefined,
        sort: params.sort || 'active',
        limit: params.limit || 40,
        offset: params.offset || 0,
      },
    });
    return response.data;
  }

  async getCommunityQuestion(questionId) {
    const response = await api.get(`/api/v1/community/questions/${encodeURIComponent(questionId)}`);
    return response.data;
  }

  async createCommunityQuestion(payload) {
    const response = await api.post('/api/v1/community/questions', payload);
    return response.data;
  }

  async createCommunityAnswer(questionId, payload) {
    const response = await api.post(
      `/api/v1/community/questions/${encodeURIComponent(questionId)}/answers`,
      payload,
    );
    return response.data;
  }

  async voteCommunityQuestion(questionId, direction) {
    const response = await api.post(
      `/api/v1/community/questions/${encodeURIComponent(questionId)}/vote`,
      { direction },
    );
    return response.data;
  }

  async voteCommunityAnswer(answerId, direction) {
    const response = await api.post(
      `/api/v1/community/answers/${encodeURIComponent(answerId)}/vote`,
      { direction },
    );
    return response.data;
  }

  /**
   * Calculate generation time from timestamp
   * @private
   */
  calculateGenerationTime(timestamp) {
    // This is a mock calculation - in real implementation,
    // the backend should provide actual generation time
    return 2.0 + Math.random() * 3.0; // 2-5 seconds
  }

  /**
   * Download generated image
   * @param {string} imageBase64 - Base64 encoded image
   * @param {string} filename - Filename for download
   */
  downloadImage(imageBase64, filename = 'floor_plan.png') {
    try {
      // Convert base64 to blob
      const byteCharacters = atob(imageBase64.split(',')[1]);
      const byteNumbers = new Array(byteCharacters.length);
      
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'image/png' });
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      return true;
    } catch (error) {
      console.error('❌ Download failed:', error);
      throw new Error('Failed to download image');
    }
  }
}

// Create and export API instance
const cadArenaAPI = new CadArenaAPI();

export default cadArenaAPI;

// Export individual methods for convenience
export const {
  checkHealth,
  getModelInfo,
  loadModel,
  generateFloorPlan,
  generateVariations,
  getPresets,
  downloadImage,
  getParseDesignModels,
  listWorkspaceProjects,
  createWorkspaceProject,
  getWorkspaceMessages,
  generateWorkspaceDxf,
  listCommunityQuestions,
  getCommunityQuestion,
  createCommunityQuestion,
  createCommunityAnswer,
  voteCommunityQuestion,
  voteCommunityAnswer
} = cadArenaAPI;
