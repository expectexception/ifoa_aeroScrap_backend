/**
 * Scraper Manager API Client for Frontend
 * 
 * Usage Examples for React, Vue, Angular, or vanilla JavaScript
 */

// ============================================================================
// 1. VANILLA JAVASCRIPT / FETCH API
// ============================================================================

class ScraperAPI {
  constructor(baseUrl = 'http://localhost:8000/api/scrapers/', token = null) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  setToken(token) {
    this.token = token;
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'API request failed');
    }

    return response.json();
  }

  // Get all scrapers
  async listScrapers() {
    return this.request('list/');
  }

  // Start a scraper
  async startScraper(scraperName, maxJobs = null, maxPages = null) {
    return this.request('start/', {
      method: 'POST',
      body: JSON.stringify({
        scraper_name: scraperName,
        max_jobs: maxJobs,
        max_pages: maxPages,
      }),
    });
  }

  // Start all scrapers
  async startAllScrapers(maxJobs = null, maxPages = null) {
    return this.request('start-all/', {
      method: 'POST',
      body: JSON.stringify({ max_jobs: maxJobs, max_pages: maxPages }),
    });
  }

  // Get job status
  async getJobStatus(jobId) {
    return this.request(`status/${jobId}/`);
  }

  // Cancel job
  async cancelJob(jobId) {
    return this.request(`cancel/${jobId}/`, { method: 'DELETE' });
  }

  // Get active jobs
  async getActiveJobs() {
    return this.request('active/');
  }

  // Get statistics
  async getStats() {
    return this.request('stats/');
  }

  // Get history
  async getHistory(scraperName = null, limit = 20) {
    const params = new URLSearchParams();
    if (scraperName) params.append('scraper', scraperName);
    params.append('limit', limit);
    return this.request(`history/?${params}`);
  }

  // Get recent jobs
  async getRecentJobs(source = null, limit = 50) {
    const params = new URLSearchParams();
    if (source) params.append('source', source);
    params.append('limit', limit);
    return this.request(`recent-jobs/?${params}`);
  }

  // Get scraper config
  async getScraperConfig(scraperName) {
    return this.request(`config/${scraperName}/`);
  }

  // Update scraper config
  async updateScraperConfig(scraperName, config) {
    return this.request(`config/${scraperName}/update/`, {
      method: 'PATCH',
      body: JSON.stringify(config),
    });
  }

  // Health check
  async healthCheck() {
    return this.request('health/');
  }
}

// Usage Example:
/*
const api = new ScraperAPI();
api.setToken('your-jwt-token');

// List all scrapers
const scrapers = await api.listScrapers();
console.log(scrapers);

// Start a scraper
const job = await api.startScraper('signature', 50);
console.log('Job started:', job.job_id);

// Check status
const status = await api.getJobStatus(job.job_id);
console.log('Status:', status);
*/


// ============================================================================
// 2. REACT HOOK IMPLEMENTATION
// ============================================================================

import { useState, useEffect, useCallback } from 'react';

export function useScraperAPI() {
  const [api] = useState(() => new ScraperAPI());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (apiMethod, ...args) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiMethod(...args);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { api, loading, error, execute };
}

// React Component Example:
/*
function ScraperDashboard() {
  const { api, loading, error, execute } = useScraperAPI();
  const [scrapers, setScrapers] = useState([]);
  const [activeJobs, setActiveJobs] = useState([]);

  useEffect(() => {
    // Set token from your auth system
    api.setToken(localStorage.getItem('authToken'));
    
    // Load scrapers
    execute(api.listScrapers.bind(api))
      .then(data => setScrapers(data.scrapers));
  }, []);

  const handleStartScraper = async (scraperName) => {
    try {
      const result = await execute(api.startScraper.bind(api), scraperName, 50);
      alert(`Scraper started! Job ID: ${result.job_id}`);
      // Refresh active jobs
      const active = await execute(api.getActiveJobs.bind(api));
      setActiveJobs(active.active_jobs);
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  return (
    <div>
      <h1>Scraper Dashboard</h1>
      {loading && <p>Loading...</p>}
      {error && <p>Error: {error}</p>}
      
      <h2>Available Scrapers</h2>
      {scrapers.map(scraper => (
        <div key={scraper.name}>
          <h3>{scraper.display_name}</h3>
          <p>{scraper.description}</p>
          <button onClick={() => handleStartScraper(scraper.name)}>
            Start Scraper
          </button>
        </div>
      ))}
      
      <h2>Active Jobs</h2>
      {activeJobs.map(job => (
        <div key={job.id}>
          <p>Job {job.id}: {job.scraper_name} - {job.status}</p>
        </div>
      ))}
    </div>
  );
}
*/


// ============================================================================
// 3. VUE 3 COMPOSITION API
// ============================================================================

import { ref, onMounted } from 'vue';

export function useScrapers() {
  const api = new ScraperAPI();
  const scrapers = ref([]);
  const loading = ref(false);
  const error = ref(null);

  const loadScrapers = async () => {
    loading.value = true;
    try {
      const data = await api.listScrapers();
      scrapers.value = data.scrapers;
    } catch (err) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  };

  const startScraper = async (scraperName, maxJobs = null) => {
    loading.value = true;
    try {
      return await api.startScraper(scraperName, maxJobs);
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  onMounted(() => {
    const token = localStorage.getItem('authToken');
    if (token) {
      api.setToken(token);
      loadScrapers();
    }
  });

  return {
    scrapers,
    loading,
    error,
    loadScrapers,
    startScraper,
    api,
  };
}

// Vue Component Example:
/*
<template>
  <div class="scraper-dashboard">
    <h1>Scraper Dashboard</h1>
    
    <div v-if="loading">Loading...</div>
    <div v-if="error" class="error">{{ error }}</div>
    
    <div v-for="scraper in scrapers" :key="scraper.name" class="scraper-card">
      <h3>{{ scraper.display_name }}</h3>
      <p>{{ scraper.description }}</p>
      <span :class="scraper.enabled ? 'enabled' : 'disabled'">
        {{ scraper.enabled ? 'Enabled' : 'Disabled' }}
      </span>
      <button @click="handleStart(scraper.name)" :disabled="!scraper.enabled">
        Start Scraper
      </button>
    </div>
  </div>
</template>

<script setup>
import { useScrapers } from './useScrapers';

const { scrapers, loading, error, startScraper } = useScrapers();

const handleStart = async (scraperName) => {
  try {
    const result = await startScraper(scraperName, 50);
    alert(`Scraper started! Job ID: ${result.job_id}`);
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
};
</script>
*/


// ============================================================================
// 4. ANGULAR SERVICE
// ============================================================================

/*
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ScraperService {
  private baseUrl = 'http://localhost:8000/api/scrapers/';
  private token: string | null = null;

  constructor(private http: HttpClient) {}

  setToken(token: string) {
    this.token = token;
  }

  private getHeaders(): HttpHeaders {
    let headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    
    if (this.token) {
      headers = headers.set('Authorization', `Bearer ${this.token}`);
    }
    
    return headers;
  }

  listScrapers(): Observable<any> {
    return this.http.get(`${this.baseUrl}list/`, {
      headers: this.getHeaders()
    });
  }

  startScraper(scraperName: string, maxJobs?: number, maxPages?: number): Observable<any> {
    return this.http.post(`${this.baseUrl}start/`, {
      scraper_name: scraperName,
      max_jobs: maxJobs,
      max_pages: maxPages
    }, {
      headers: this.getHeaders()
    });
  }

  getJobStatus(jobId: number): Observable<any> {
    return this.http.get(`${this.baseUrl}status/${jobId}/`, {
      headers: this.getHeaders()
    });
  }

  getStats(): Observable<any> {
    return this.http.get(`${this.baseUrl}stats/`, {
      headers: this.getHeaders()
    });
  }

  getActiveJobs(): Observable<any> {
    return this.http.get(`${this.baseUrl}active/`, {
      headers: this.getHeaders()
    });
  }

  cancelJob(jobId: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}cancel/${jobId}/`, {
      headers: this.getHeaders()
    });
  }
}

// Usage in Angular Component:
export class ScraperDashboardComponent implements OnInit {
  scrapers: any[] = [];
  loading = false;

  constructor(private scraperService: ScraperService) {}

  ngOnInit() {
    this.scraperService.setToken(localStorage.getItem('authToken'));
    this.loadScrapers();
  }

  loadScrapers() {
    this.loading = true;
    this.scraperService.listScrapers().subscribe({
      next: (data) => {
        this.scrapers = data.scrapers;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading scrapers:', err);
        this.loading = false;
      }
    });
  }

  startScraper(scraperName: string) {
    this.scraperService.startScraper(scraperName, 50).subscribe({
      next: (result) => {
        alert(`Scraper started! Job ID: ${result.job_id}`);
      },
      error: (err) => {
        alert(`Error: ${err.message}`);
      }
    });
  }
}
*/


// ============================================================================
// 5. REAL-TIME POLLING FOR JOB STATUS
// ============================================================================

class JobStatusPoller {
  constructor(api, jobId, onUpdate, interval = 2000) {
    this.api = api;
    this.jobId = jobId;
    this.onUpdate = onUpdate;
    this.interval = interval;
    this.timerId = null;
  }

  start() {
    this.poll();
    this.timerId = setInterval(() => this.poll(), this.interval);
  }

  stop() {
    if (this.timerId) {
      clearInterval(this.timerId);
      this.timerId = null;
    }
  }

  async poll() {
    try {
      const status = await this.api.getJobStatus(this.jobId);
      this.onUpdate(status);
      
      // Stop polling if job is complete
      if (['completed', 'failed', 'cancelled'].includes(status.status)) {
        this.stop();
      }
    } catch (error) {
      console.error('Polling error:', error);
    }
  }
}

// Usage:
/*
const poller = new JobStatusPoller(
  api,
  jobId,
  (status) => {
    console.log('Job status:', status);
    updateUI(status);
  }
);
poller.start();

// Stop polling when component unmounts
onUnmount(() => poller.stop());
*/


// ============================================================================
// 6. COMPLETE DASHBOARD EXAMPLE (React)
// ============================================================================

/*
function ScraperManagerDashboard() {
  const { api, loading, error, execute } = useScraperAPI();
  const [scrapers, setScrapers] = useState([]);
  const [activeJobs, setActiveJobs] = useState([]);
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    api.setToken(localStorage.getItem('authToken'));
    loadData();
    
    // Refresh active jobs every 5 seconds
    const interval = setInterval(loadActiveJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [scrapersData, statsData, historyData] = await Promise.all([
        execute(api.listScrapers.bind(api)),
        execute(api.getStats.bind(api)),
        execute(api.getHistory.bind(api), null, 10)
      ]);
      
      setScrapers(scrapersData.scrapers);
      setStats(statsData);
      setHistory(historyData.jobs);
    } catch (err) {
      console.error('Error loading data:', err);
    }
  };

  const loadActiveJobs = async () => {
    try {
      const data = await execute(api.getActiveJobs.bind(api));
      setActiveJobs(data.active_jobs);
    } catch (err) {
      console.error('Error loading active jobs:', err);
    }
  };

  const handleStartScraper = async (scraperName) => {
    try {
      const result = await execute(api.startScraper.bind(api), scraperName, 50);
      alert(`✅ Scraper started! Job ID: ${result.job_id}`);
      loadActiveJobs();
    } catch (err) {
      alert(`❌ Error: ${err.message}`);
    }
  };

  const handleCancelJob = async (jobId) => {
    if (confirm('Are you sure you want to cancel this job?')) {
      try {
        await execute(api.cancelJob.bind(api), jobId);
        alert('✅ Job cancelled');
        loadActiveJobs();
      } catch (err) {
        alert(`❌ Error: ${err.message}`);
      }
    }
  };

  return (
    <div className="dashboard">
      <h1>Scraper Manager Dashboard</h1>
      
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Total Runs</h3>
            <p>{stats.total_runs}</p>
          </div>
          <div className="stat-card">
            <h3>Success Rate</h3>
            <p>{stats.success_rate.toFixed(1)}%</p>
          </div>
          <div className="stat-card">
            <h3>Total Jobs</h3>
            <p>{stats.total_jobs_scraped}</p>
          </div>
          <div className="stat-card">
            <h3>Avg Time</h3>
            <p>{stats.avg_execution_time.toFixed(1)}s</p>
          </div>
        </div>
      )}

      <div className="active-jobs">
        <h2>Active Jobs ({activeJobs.length})</h2>
        {activeJobs.map(job => (
          <div key={job.id} className="job-card active">
            <h3>{job.scraper_name}</h3>
            <span className="status">{job.status}</span>
            <button onClick={() => handleCancelJob(job.id)}>Cancel</button>
          </div>
        ))}
      </div>

      <div className="scrapers-grid">
        <h2>Available Scrapers</h2>
        {scrapers.map(scraper => (
          <div key={scraper.name} className="scraper-card">
            <h3>{scraper.display_name}</h3>
            <p>{scraper.description}</p>
            <span className={scraper.enabled ? 'badge-success' : 'badge-disabled'}>
              {scraper.enabled ? 'Enabled' : 'Disabled'}
            </span>
            <button 
              onClick={() => handleStartScraper(scraper.name)}
              disabled={!scraper.enabled || loading}
            >
              Start Scraper
            </button>
          </div>
        ))}
      </div>

      <div className="history">
        <h2>Recent History</h2>
        <table>
          <thead>
            <tr>
              <th>Scraper</th>
              <th>Status</th>
              <th>Jobs Found</th>
              <th>Duration</th>
              <th>Started At</th>
            </tr>
          </thead>
          <tbody>
            {history.map(job => (
              <tr key={job.id}>
                <td>{job.scraper_name}</td>
                <td>{job.status}</td>
                <td>{job.jobs_found}</td>
                <td>{job.execution_time?.toFixed(1)}s</td>
                <td>{new Date(job.started_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
*/

export { ScraperAPI, JobStatusPoller };
