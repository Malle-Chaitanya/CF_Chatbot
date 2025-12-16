'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { getApiBase, getCurrentUser } from '@/lib/session-utils';
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
  metadata: Record<string, any>;
}

interface TopQuestion {
  question: string;
  times_asked: number;
  percentage?: number;
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
  const [timeFilter, setTimeFilter] = useState<'today' | 'yesterday' | 'this_week' | 'last_week' | 'all'>('today');
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [users, setUsers] = useState<UserAnalytics[]>([]);
  const [topQuestions, setTopQuestions] = useState<TopQuestion[]>([]);
  const [mostActiveUsers, setMostActiveUsers] = useState<MostActiveUser[]>([]);

  // Verify admin access on mount
  useEffect(() => {
    const user = getCurrentUser();

    if (!user) {
      router.replace('/login?error=admin_only');
      return;
    }

    if (!isAdminEmail(user.email)) {
      router.replace('/login?error=admin_only');
      return;
    }

    setAuthUser(user);
    setLoading(false);
  }, [router]);

  // Fetch all analytics data with time filter
  const fetchAnalytics = useCallback(
    async (user: User, selectedTimeFilter?: string) => {
      setFetching(true);
      setError(null);

      const filter = selectedTimeFilter || timeFilter;

      try {
        // Fetch summary with time filter
        const summaryRes = await fetch(
          `${getApiBase()}/analytics/langfuse/dashboard-summary?time_filter=${filter}`,
          {
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${user.access_token}`
            }
          }
        );

        if (summaryRes.ok) {
          const summaryData = await summaryRes.json();
          if (summaryData.status === 'success') {
            setSummary(summaryData.summary);
            setMostActiveUsers(summaryData.most_active_users || []);
            setTopQuestions(summaryData.top_questions || []);
          }
        }

        // Fetch all users with time filter
        const usersRes = await fetch(
          `${getApiBase()}/analytics/langfuse/users?time_filter=${filter}`,
          {
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${user.access_token}`
            }
          }
        );

        if (usersRes.ok) {
          const usersData = await usersRes.json();
          if (usersData.status === 'success') {
            setUsers(usersData.users || []);
          }
        }
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setFetching(false);
      }
    },
    [timeFilter]
  );

  // Fetch data after authentication
  useEffect(() => {
    if (!authUser) return;
    fetchAnalytics(authUser);
  }, [authUser, fetchAnalytics]);

  const handleRefresh = () => {
    if (!authUser) return;
    fetchAnalytics(authUser);
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', fontFamily: 'Inter, system-ui, sans-serif' }}>
        <p style={{ color: '#6b7280' }}>Checking admin access...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto', fontFamily: 'Inter, system-ui, sans-serif' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '30px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '6px' }}>🔍 Langfuse Analytics</h1>
          <p style={{ color: '#6b7280', fontSize: '14px' }}>
            User engagement and question analytics. Visible only to admins: {ADMIN_EMAILS.join(', ')}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => router.push('/chat/new')}
            style={{
              padding: '10px 14px',
              borderRadius: '10px',
              border: '1px solid #d1d5db',
              background: 'white',
              cursor: 'pointer',
              color: '#111827',
              fontWeight: 600
            }}
          >
            Back to chats
          </button>
          <button
            onClick={handleRefresh}
            disabled={fetching}
            style={{
              padding: '10px 14px',
              borderRadius: '10px',
              border: 'none',
              background: '#0129ac',
              color: 'white',
              cursor: fetching ? 'not-allowed' : 'pointer',
              fontWeight: 700,
              opacity: fetching ? 0.6 : 1
            }}
          >
            {fetching ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ 
          background: '#fef2f2', 
          color: '#b91c1c', 
          padding: '12px 14px', 
          borderRadius: '10px', 
          marginBottom: '20px', 
          border: '1px solid #fecdd3' 
        }}>
          Error: {error}
        </div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '30px'
        }}>
          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid #e5e7eb',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
          }}>
            <p style={{ color: '#6b7280', fontSize: '14px', margin: '0 0 8px 0', fontWeight: 500 }}>Total Users</p>
            <p style={{ fontSize: '32px', fontWeight: 700, color: '#111827', margin: 0 }}>{summary.total_users}</p>
          </div>
          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid #e5e7eb',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
          }}>
            <p style={{ color: '#6b7280', fontSize: '14px', margin: '0 0 8px 0', fontWeight: 500 }}>Total Questions</p>
            <p style={{ fontSize: '32px', fontWeight: 700, color: '#111827', margin: 0 }}>{summary.total_questions}</p>
          </div>
          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid #e5e7eb',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
          }}>
            <p style={{ color: '#6b7280', fontSize: '14px', margin: '0 0 8px 0', fontWeight: 500 }}>Unique Questions</p>
            <p style={{ fontSize: '32px', fontWeight: 700, color: '#111827', margin: 0 }}>{summary.unique_questions}</p>
          </div>
          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid #e5e7eb',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
          }}>
            <p style={{ color: '#6b7280', fontSize: '14px', margin: '0 0 8px 0', fontWeight: 500 }}>Avg Questions/User</p>
            <p style={{ fontSize: '32px', fontWeight: 700, color: '#111827', margin: 0 }}>{summary.average_questions_per_user}</p>
          </div>
        </div>
      )}

      {/* Date Filter Buttons */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '20px',
        flexWrap: 'wrap'
      }}>
        {(['today', 'yesterday', 'this_week', 'last_week', 'all'] as const).map((filter) => (
          <button
            key={filter}
            onClick={() => {
              setTimeFilter(filter);
              if (authUser) fetchAnalytics(authUser, filter);
            }}
            style={{
              padding: '8px 14px',
              borderRadius: '8px',
              border: timeFilter === filter ? '2px solid #0129ac' : '1px solid #d1d5db',
              background: timeFilter === filter ? '#0129ac' : 'white',
              color: timeFilter === filter ? 'white' : '#111827',
              cursor: 'pointer',
              fontWeight: timeFilter === filter ? 600 : 500,
              fontSize: '13px',
              transition: 'all 0.2s ease'
            }}
          >
            {filter === 'today' && 'Today'}
            {filter === 'yesterday' && 'Yesterday'}
            {filter === 'this_week' && 'This Week'}
            {filter === 'last_week' && 'Last 7 Days'}
            {filter === 'all' && 'All Time'}
          </button>
        ))}
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '20px',
        borderBottom: '2px solid #e5e7eb'
      }}>
        <button
          onClick={() => setActiveTab('overview')}
          style={{
            padding: '12px 20px',
            background: 'none',
            border: 'none',
            color: activeTab === 'overview' ? '#111827' : '#6b7280',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: 500,
            borderBottom: activeTab === 'overview' ? '3px solid #0129ac' : 'none',
            transition: 'all 0.3s ease'
          }}
        >
          Overview
        </button>
        <button
          onClick={() => setActiveTab('users')}
          style={{
            padding: '12px 20px',
            background: 'none',
            border: 'none',
            color: activeTab === 'users' ? '#111827' : '#6b7280',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: 500,
            borderBottom: activeTab === 'users' ? '3px solid #0129ac' : 'none',
            transition: 'all 0.3s ease'
          }}
        >
          All Users ({users.length})
        </button>
        <button
          onClick={() => setActiveTab('questions')}
          style={{
            padding: '12px 20px',
            background: 'none',
            border: 'none',
            color: activeTab === 'questions' ? '#111827' : '#6b7280',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: 500,
            borderBottom: activeTab === 'questions' ? '3px solid #0129ac' : 'none',
            transition: 'all 0.3s ease'
          }}
        >
          Top Questions
        </button>
      </div>

      {/* Tab Content */}
      <div style={{ background: 'white', borderRadius: '12px', border: '1px solid #e5e7eb', padding: '20px' }}>
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div>
            {/* Most Active Users */}
            <div style={{ marginBottom: '30px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px', color: '#111827' }}>
                Top 10 Most Active Users
              </h2>
              <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden' }}>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  background: '#f9fafb',
                  padding: '12px 14px',
                  fontWeight: 700,
                  color: '#111827',
                  fontSize: '14px',
                  borderBottom: '1px solid #e5e7eb'
                }}>
                  <div>Email</div>
                  <div>Name</div>
                  <div style={{ textAlign: 'right' }}>Questions</div>
                </div>
                {mostActiveUsers.length === 0 ? (
                  <div style={{ padding: '16px', color: '#6b7280' }}>No data available.</div>
                ) : (
                  mostActiveUsers.map((user, idx) => (
                    <div
                      key={user.user_id}
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        padding: '12px 14px',
                        borderTop: '1px solid #e5e7eb',
                        background: idx % 2 === 0 ? 'white' : '#f9fafb',
                        fontSize: '14px'
                      }}
                    >
                      <div style={{ color: '#111827' }}>{user.email}</div>
                      <div style={{ color: '#111827' }}>{user.name}</div>
                      <div style={{ color: '#111827', fontWeight: 600, textAlign: 'right' }}>{user.questions_asked}</div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Top Questions */}
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px', color: '#111827' }}>
                Top 5 Questions
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {topQuestions.length === 0 ? (
                  <div style={{ color: '#6b7280' }}>No data available.</div>
                ) : (
                  topQuestions.map((q, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        gap: '12px',
                        padding: '12px 14px',
                        background: '#f9fafb',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        alignItems: 'flex-start'
                      }}
                    >
                      <span style={{
                        fontSize: '18px',
                        fontWeight: 700,
                        color: '#0129ac',
                        minWidth: '30px'
                      }}>#{idx + 1}</span>
                      <span style={{ flex: 1, color: '#111827', fontSize: '14px' }}>{q.question}</span>
                      <span style={{
                        fontSize: '14px',
                        fontWeight: 600,
                        color: '#e74c3c',
                        whiteSpace: 'nowrap'
                      }}>×{q.times_asked}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px', color: '#111827' }}>
              All Users ({users.length})
            </h2>
            <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden', overflowX: 'auto' }}>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(5, minmax(150px, 1fr))',
                background: '#f9fafb',
                padding: '12px 14px',
                fontWeight: 700,
                color: '#111827',
                fontSize: '13px',
                borderBottom: '1px solid #e5e7eb',
                minWidth: '800px'
              }}>
                <div>Email</div>
                <div>Name</div>
                <div>Total Questions</div>
                <div>First Question</div>
                <div>Last Active</div>
              </div>
              {users.length === 0 ? (
                <div style={{ padding: '16px', color: '#6b7280' }}>No users found.</div>
              ) : (
                users.map((user, idx) => (
                  <div
                    key={user.user_id}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(5, minmax(150px, 1fr))',
                      padding: '12px 14px',
                      borderTop: '1px solid #e5e7eb',
                      background: idx % 2 === 0 ? 'white' : '#f9fafb',
                      fontSize: '13px',
                      minWidth: '800px'
                    }}
                  >
                    <div style={{ color: '#111827' }}>{user.email}</div>
                    <div style={{ color: '#111827' }}>{user.name}</div>
                    <div style={{ color: '#111827', fontWeight: 600 }}>{user.total_questions}</div>
                    <div style={{ color: '#6b7280' }}>
                      {user.first_question_at ? new Date(user.first_question_at).toLocaleDateString() : '—'}
                    </div>
                    <div style={{ color: '#6b7280' }}>
                      {user.last_question_at ? new Date(user.last_question_at).toLocaleDateString() : '—'}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Questions Tab */}
        {activeTab === 'questions' && (
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px', color: '#111827' }}>
              Top Questions Across All Users
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {topQuestions.length === 0 ? (
                <div style={{ color: '#6b7280' }}>No data available.</div>
              ) : (
                topQuestions.map((q, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      gap: '15px',
                      padding: '15px',
                      background: '#f9fafb',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      alignItems: 'flex-start'
                    }}
                  >
                    <div style={{
                      fontSize: '18px',
                      fontWeight: 700,
                      color: '#0129ac',
                      minWidth: '40px'
                    }}>#{idx + 1}</div>
                    <div style={{ flex: 1 }}>
                      <p style={{ margin: '0 0 6px 0', color: '#111827', fontSize: '14px', fontWeight: 500 }}>
                        {q.question}
                      </p>
                      <p style={{ margin: 0, color: '#6b7280', fontSize: '12px' }}>
                        Asked {q.times_asked} times {q.percentage ? `(${q.percentage}% of total)` : ''}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

