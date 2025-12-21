'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { getCurrentUser } from '@/lib/session-utils';
import { getApiBase } from '@/lib/api';
import { isAdminEmail, ADMIN_EMAILS } from '@/constants/admins';
import { User } from '@/types/chat';

interface UserAnalytics {
  user_id: string;
  email: string;
  name: string;
  total_questions: number;
  first_question_at: string;
  last_question_at: string;
  top_questions: Array<{ question: string; count: number }>;
}

interface TopQuestion {
  question: string;
  times_asked: number;
}

interface MostActiveUser {
  user_id: string;
  email: string;
  name: string;
  questions_asked: number;
}

interface DashboardSummary {
  total_users: number;
  total_questions: number;
  unique_questions: number;
  average_questions_per_user: number;
}

export default function AdminLangfuseAnalyticsPage() {
  const router = useRouter();
  const [authUser, setAuthUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [fetching, setFetching] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'questions'>('overview');
  const [timeFilter, setTimeFilter] = useState<'today' | 'yesterday' | 'this_week' | 'last_week' | 'this_month' | 'all'>('today');
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [users, setUsers] = useState<UserAnalytics[]>([]);
  const [topQuestions, setTopQuestions] = useState<TopQuestion[]>([]);
  const [mostActiveUsers, setMostActiveUsers] = useState<MostActiveUser[]>([]);
  const [lastFetchTime, setLastFetchTime] = useState<number | null>(null);

  // Check admin access on mount
  useEffect(() => {
    function checkAuth() {
      try {
        const user = getCurrentUser(); // NOT async!
        if (!user || !isAdminEmail(user.email)) {
          router.push('/login');
          return;
        }
        setAuthUser(user);
      } catch (err) {
        console.error('Auth check failed:', err);
        router.push('/login');
      } finally {
        setLoading(false);
      }
    }
    checkAuth();
  }, [router]);

  // Fetch all analytics data
  const fetchAnalytics = useCallback(
    async (filter: string) => {
      setFetching(true);
      setError(null);

      try {
        const user = getCurrentUser(); // NOT async!
        if (!user) {
          setError('Not authenticated');
          console.error('[Analytics] No user found in localStorage');
          return;
        }

        const apiBase = getApiBase();
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };

        const fetchOptions = {
          headers,
          credentials: 'include' as const,
          signal: AbortSignal.timeout(90000), // 90 second timeout
        };

        // Fetch summary
        const summaryUrl = `${apiBase}/analytics/langfuse/dashboard-summary?time_filter=${filter}`;
        console.log('[Analytics Fetch] Summary URL:', summaryUrl);
        
        const summaryRes = await fetch(summaryUrl, fetchOptions);

        if (summaryRes.ok) {
          const data = await summaryRes.json();
          if (data.status === 'success') {
            setSummary(data.summary);
            setMostActiveUsers(data.most_active_users || []);
            setTopQuestions(data.top_questions || []);
          }
        }

        // Fetch users
        const usersUrl = `${apiBase}/analytics/langfuse/users?time_filter=${filter}`;
        const usersRes = await fetch(usersUrl, fetchOptions);

        if (usersRes.ok) {
          const data = await usersRes.json();
          if (data.status === 'success') {
            setUsers(data.users || []);
          }
        }

        setLastFetchTime(Date.now());
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch analytics';
        setError(message);
        console.error('Analytics fetch error:', err);
      } finally {
        setFetching(false);
      }
    },
    []
  );

  // Handle filter change
  const handleFilterChange = (filter: string) => {
    setTimeFilter(filter as any);
  };

  // Handle apply button click
  const handleApplyClick = () => {
    fetchAnalytics(timeFilter);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontSize: '18px' }}>
        Checking access...
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '8px' }}>Langfuse Analytics</h1>
        <p style={{ color: '#6b7280', fontSize: '16px' }}>Track user questions and analytics</p>
      </div>

      {/* Filter Buttons */}
      <div style={{ marginBottom: '24px', display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
        {['today', 'yesterday', 'this_week', 'last_week', 'this_month', 'all'].map((filter) => (
          <button
            key={filter}
            onClick={() => handleFilterChange(filter)}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: timeFilter === filter ? '2px solid #0129ac' : '1px solid #e5e7eb',
              background: timeFilter === filter ? '#0129ac' : 'white',
              color: timeFilter === filter ? 'white' : '#111827',
              cursor: 'pointer',
              fontWeight: timeFilter === filter ? '600' : '500',
              fontSize: '14px',
              transition: 'all 0.2s ease',
            }}
          >
            {filter === 'this_week' ? 'This Week' : filter === 'last_week' ? 'Last Week' : filter === 'this_month' ? 'This Month' : filter.charAt(0).toUpperCase() + filter.slice(1)}
          </button>
        ))}
        
        {/* Apply Button */}
        <button
          onClick={handleApplyClick}
          disabled={fetching}
          style={{
            padding: '8px 20px',
            borderRadius: '8px',
            border: 'none',
            background: fetching ? '#d1d5db' : '#10b981',
            color: 'white',
            cursor: fetching ? 'not-allowed' : 'pointer',
            fontWeight: '600',
            fontSize: '14px',
            transition: 'all 0.2s ease',
            marginLeft: '12px',
          }}
        >
          {fetching ? 'Fetching...' : 'Apply'}
        </button>
      </div>

      {/* Fetch Time */}
      {lastFetchTime && (
        <div style={{ marginBottom: '16px', fontSize: '12px', color: '#9ca3af' }}>
          Last updated: {new Date(lastFetchTime).toLocaleTimeString()}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#fee2e2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          color: '#991b1b',
          marginBottom: '24px'
        }}>
          Error: {error}
        </div>
      )}

      {/* Loading State */}
      {fetching && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#dbeafe',
          border: '1px solid #93c5fd',
          borderRadius: '8px',
          color: '#1e40af',
          marginBottom: '24px'
        }}>
          Loading analytics...
        </div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
          <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px', backgroundColor: '#f9fafb' }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Total Users</div>
            <div style={{ fontSize: '28px', fontWeight: '700' }}>{summary.total_users}</div>
          </div>
          <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px', backgroundColor: '#f9fafb' }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Total Questions</div>
            <div style={{ fontSize: '28px', fontWeight: '700' }}>{summary.total_questions}</div>
          </div>
          <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px', backgroundColor: '#f9fafb' }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Unique Questions</div>
            <div style={{ fontSize: '28px', fontWeight: '700' }}>{summary.unique_questions}</div>
          </div>
          <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px', backgroundColor: '#f9fafb' }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Avg per User</div>
            <div style={{ fontSize: '28px', fontWeight: '700' }}>{summary.average_questions_per_user.toFixed(2)}</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', borderBottom: '1px solid #e5e7eb' }}>
        {['overview', 'users', 'questions'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            style={{
              padding: '12px 0',
              borderBottom: activeTab === tab ? '2px solid #0129ac' : 'none',
              background: 'none',
              border: 'none',
              color: activeTab === tab ? '#0129ac' : '#6b7280',
              cursor: 'pointer',
              fontWeight: activeTab === tab ? '600' : '500',
              fontSize: '14px',
            }}
          >
            {tab === 'overview' ? 'Overview' : tab === 'users' ? 'Top Users' : 'Top Questions'}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && mostActiveUsers.length > 0 && (
        <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden' }}>
          <div style={{ padding: '16px', backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600' }}>Most Active Users</h2>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f3f4f6', borderBottom: '1px solid #e5e7eb' }}>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Rank</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Email</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Questions</th>
                </tr>
              </thead>
              <tbody>
                {mostActiveUsers.map((user, idx) => (
                  <tr key={user.user_id} style={{ borderBottom: '1px solid #e5e7eb', backgroundColor: idx % 2 === 0 ? 'white' : '#fafafa' }}>
                    <td style={{ padding: '12px 16px', fontSize: '14px', fontWeight: '500' }}>{idx + 1}</td>
                    <td style={{ padding: '12px 16px', fontSize: '14px' }}>{user.email}</td>
                    <td style={{ padding: '12px 16px', fontSize: '14px', textAlign: 'center', fontWeight: '600' }}>
                      {user.questions_asked}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Users Tab */}
      {activeTab === 'users' && users.length > 0 && (
        <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden' }}>
          <div style={{ padding: '16px', backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600' }}>All Users</h2>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f3f4f6', borderBottom: '1px solid #e5e7eb' }}>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Email</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Questions</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Last Asked</th>
                </tr>
              </thead>
              <tbody>
                {users.slice(0, 20).map((user, idx) => (
                  <tr key={user.user_id} style={{ borderBottom: '1px solid #e5e7eb', backgroundColor: idx % 2 === 0 ? 'white' : '#fafafa' }}>
                    <td style={{ padding: '12px 16px', fontSize: '14px' }}>{user.email}</td>
                    <td style={{ padding: '12px 16px', fontSize: '14px', textAlign: 'center', fontWeight: '500' }}>
                      {user.total_questions}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: '14px', color: '#6b7280' }}>
                      {new Date(user.last_question_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Questions Tab */}
      {activeTab === 'questions' && topQuestions.length > 0 && (
        <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden' }}>
          <div style={{ padding: '16px', backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600' }}>Top Questions</h2>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f3f4f6', borderBottom: '1px solid #e5e7eb' }}>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Rank</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Question</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Times Asked</th>
                </tr>
              </thead>
              <tbody>
                {topQuestions.map((q, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #e5e7eb', backgroundColor: idx % 2 === 0 ? 'white' : '#fafafa' }}>
                    <td style={{ padding: '12px 16px', fontSize: '14px', fontWeight: '500' }}>{idx + 1}</td>
                    <td style={{ padding: '12px 16px', fontSize: '14px' }}>{q.question.substring(0, 100)}</td>
                    <td style={{ padding: '12px 16px', fontSize: '14px', textAlign: 'center', fontWeight: '600' }}>
                      {q.times_asked}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!fetching && !summary && !error && (
        <div style={{ padding: '32px', textAlign: 'center', color: '#6b7280' }}>
          No data available for the selected period.
        </div>
      )}
    </div>
  );
}
