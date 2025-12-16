'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { getApiBase, getCurrentUser } from '@/lib/session-utils';
import { isAdminEmail } from '@/constants/admins';
import { User } from '@/types/chat';
import React from 'react';

interface TeamStats {
  team_name: string;
  lead: string | null;
  lead_email: string | null;
  member_count: number;
  active_members_count: number;
  color: string;
  total_questions: number;
  unique_questions: number;
  top_questions: Array<{ question: string; count: number }>;
}

interface TeamMember {
  name: string;
  email: string;
  is_lead: boolean;
  total_questions: number;
  top_questions: Array<{ question: string; count: number }>;
}

interface TeamDetails {
  team_name: string;
  lead: string;
  lead_email: string;
  color: string;
  members: TeamMember[];
  total_members: number;
  active_members: number;
  team_total_questions: number;
  team_unique_questions: number;
}

interface CachedData {
  timestamp: number;
  data: TeamStats[];
  dateRange: { start: Date; end: Date };
}

export default function TeamsAnalyticsPage() {
  const router = useRouter();
  const [authUser, setAuthUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [fetching, setFetching] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Calendar state
  const [showDatePicker, setShowDatePicker] = useState<boolean>(false);
  const [startDate, setStartDate] = useState<Date>(new Date());
  const [endDate, setEndDate] = useState<Date>(new Date());
  const [selectedDateRange, setSelectedDateRange] = useState<{ start: string; end: string } | null>(null);
  
  // Data state
  const [teams, setTeams] = useState<TeamStats[]>([]);
  const [cachedResults, setCachedResults] = useState<Map<string, CachedData>>(new Map());
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const [selectedTeamDetails, setSelectedTeamDetails] = useState<TeamDetails | null>(null);
  const [showTeamDetails, setShowTeamDetails] = useState<boolean>(false);

  // Verify admin access on mount
  useEffect(() => {
    const user = getCurrentUser();
    if (!user) {
      router.replace('/login?error=admin_only');
      return;
    }

    if (!isAdminEmail(user.email)) {
      console.warn('User is not admin:', user.email);
      router.replace('/login?error=admin_only');
      return;
    }

    console.log('[ADMIN] User is admin:', user.email);
    setAuthUser(user);
    setLoading(false);
  }, [router]);

  // Fetch teams analytics with date range
  const fetchTeamsAnalytics = useCallback(
    async (user: User, start: Date, end: Date) => {
      setFetching(true);
      setError(null);

      try {
        // Check cache first
        const cacheKey = `${start.toISOString().split('T')[0]}_${end.toISOString().split('T')[0]}`;
        const cached = cachedResults.get(cacheKey);
        
        // Use cache if it exists and is less than 1 hour old
        if (cached && (Date.now() - cached.timestamp < 3600000)) {
          console.log('[CACHE] Using cached data for date range:', cacheKey);
          setTeams(cached.data);
          setSelectedDateRange({ start: start.toLocaleDateString(), end: end.toLocaleDateString() });
          setFetching(false);
          return;
        }

        // Import token functions
        const { ensureValidToken, refreshAccessToken } = await import('@/lib/session-utils');
        
        // Ensure we have a valid token
        const tokenValid = await ensureValidToken();
        if (!tokenValid) {
          setError('Session expired. Please log in again.');
          router.push('/login');
          return;
        }

        // Get fresh user data from localStorage
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
        if (!currentUser.access_token) {
          setError('No authentication token found');
          return;
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout for date range
        
        // Format dates for API: YYYY-MM-DD
        const startStr = start.toISOString().split('T')[0];
        const endStr = end.toISOString().split('T')[0];
        
        const response = await fetch(
          `${getApiBase()}/analytics/langfuse/teams/summary?start_date=${startStr}&end_date=${endStr}`,
          {
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${currentUser.access_token}`
            },
            signal: controller.signal
          }
        ).finally(() => clearTimeout(timeoutId));

        if (response.status === 401) {
          // Try to refresh token and retry
          const refreshed = await refreshAccessToken();
          if (refreshed) {
            const refreshedUser = JSON.parse(localStorage.getItem('user') || '{}');
            const retryResponse = await fetch(
              `${getApiBase()}/analytics/langfuse/teams/summary?start_date=${startStr}&end_date=${endStr}`,
              {
                headers: {
                  'Content-Type': 'application/json',
                  Authorization: `Bearer ${refreshedUser.access_token}`
                }
              }
            );
            
            if (retryResponse.ok) {
              const data = await retryResponse.json();
              if (data.status === 'success') {
                setTeams(data.teams || []);
                // Cache the results
                setCachedResults(prev => new Map(prev).set(cacheKey, {
                  timestamp: Date.now(),
                  data: data.teams || [],
                  dateRange: { start, end }
                }));
                setSelectedDateRange({ start: start.toLocaleDateString(), end: end.toLocaleDateString() });
              }
            } else {
              setError('Failed to fetch team analytics');
            }
          } else {
            setError('Session expired. Please log in again.');
            router.push('/login');
          }
        } else if (response.ok) {
          const data = await response.json();
          if (data.status === 'success') {
            setTeams(data.teams || []);
            // Cache the results
            setCachedResults(prev => new Map(prev).set(cacheKey, {
              timestamp: Date.now(),
              data: data.teams || [],
              dateRange: { start, end }
            }));
            setSelectedDateRange({ start: start.toLocaleDateString(), end: end.toLocaleDateString() });
          } else if (data.error) {
            setError(data.error);
          }
        } else {
          setError(`HTTP ${response.status}: Failed to fetch team analytics`);
        }
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setFetching(false);
      }
    },
    [cachedResults, router]
  );

  // Fetch specific team details
  const fetchTeamDetails = useCallback(
    async (user: User, teamName: string, start: Date, end: Date) => {
      try {
        // Import token functions
        const { ensureValidToken, refreshAccessToken } = await import('@/lib/session-utils');
        
        // Ensure we have a valid token
        const tokenValid = await ensureValidToken();
        if (!tokenValid) {
          console.error('Session expired');
          return;
        }

        // Get fresh user data from localStorage
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
        if (!currentUser.access_token) {
          console.error('No authentication token found');
          return;
        }

        const startStr = start.toISOString().split('T')[0];
        const endStr = end.toISOString().split('T')[0];

        const response = await fetch(
          `${getApiBase()}/analytics/langfuse/teams/details?team_name=${encodeURIComponent(teamName)}&start_date=${startStr}&end_date=${endStr}`,
          {
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${currentUser.access_token}`
            }
          }
        );

        if (response.status === 401) {
          // Try to refresh token and retry
          const refreshed = await refreshAccessToken();
          if (refreshed) {
            const refreshedUser = JSON.parse(localStorage.getItem('user') || '{}');
            const retryResponse = await fetch(
              `${getApiBase()}/analytics/langfuse/teams/details?team_name=${encodeURIComponent(teamName)}&start_date=${startStr}&end_date=${endStr}`,
              {
                headers: {
                  'Content-Type': 'application/json',
                  Authorization: `Bearer ${refreshedUser.access_token}`
                }
              }
            );
            
            if (retryResponse.ok) {
              const data = await retryResponse.json();
              if (data.status === 'success') {
                setSelectedTeamDetails(data);
                setShowTeamDetails(true);
              }
            }
          }
        } else if (response.ok) {
          const data = await response.json();
          if (data.status === 'success') {
            setSelectedTeamDetails(data);
            setShowTeamDetails(true);
          }
        }
      } catch (err) {
        console.error('Error fetching team details:', err);
      }
    },
    []
  );

  // Initialize with today's date on mount
  useEffect(() => {
    const today = new Date();
    setStartDate(today);
    setEndDate(today);
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '40px', fontFamily: 'Inter, system-ui, sans-serif' }}>
        <p style={{ color: '#6b7280' }}>Checking admin access...</p>
      </div>
    );
  }

  const totalTeams = teams.length || 8;  // Default to 8 teams
  const totalQuestions = teams.reduce((sum, t) => sum + t.total_questions, 0);
  const activeTeams = teams.filter(t => t.total_questions > 0).length;

  return (
    <div style={{ padding: '32px', maxWidth: '1600px', margin: '0 auto', fontFamily: 'Inter, system-ui, sans-serif' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '30px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '6px' }}>👥 Team Analytics</h1>
          <p style={{ color: '#6b7280', fontSize: '14px' }}>Team-wise user engagement and question analytics</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => router.push('/chats')}
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
            onClick={() => {
              if (authUser) fetchTeamsAnalytics(authUser);
            }}
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

      {/* Date Range Picker */}
      <div style={{
        background: '#ede9fe',
        padding: '16px',
        borderRadius: '12px',
        marginBottom: '20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        flexWrap: 'wrap'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '14px', fontWeight: 600, color: '#111827' }}>📅</span>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: '#111827',
            fontWeight: 600,
            fontSize: '14px'
          }}>
            <input
              type="date"
              value={startDate.toISOString().split('T')[0]}
              onChange={(e) => setStartDate(new Date(e.target.value))}
              style={{
                padding: '6px 10px',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            />
            <span>→</span>
            <input
              type="date"
              value={endDate.toISOString().split('T')[0]}
              onChange={(e) => setEndDate(new Date(e.target.value))}
              style={{
                padding: '6px 10px',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            />
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => {
              const today = new Date();
              setStartDate(today);
              setEndDate(today);
            }}
            style={{
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid #d1d5db',
              background: 'white',
              color: '#111827',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: '12px'
            }}
          >
            Reset
          </button>
          <button
            onClick={() => {
              if (authUser) {
                fetchTeamsAnalytics(authUser, startDate, endDate);
              }
            }}
            disabled={fetching}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              background: '#7c3aed',
              color: 'white',
              cursor: fetching ? 'not-allowed' : 'pointer',
              fontWeight: 600,
              fontSize: '12px',
              opacity: fetching ? 0.6 : 1
            }}
          >
            {fetching ? 'Fetching...' : 'Apply'}
          </button>
        </div>
      </div>
      
      {/* Selected Date Range Info */}
      {selectedDateRange && (
        <div style={{
          background: '#f0fdf4',
          padding: '12px 14px',
          borderRadius: '8px',
          marginBottom: '16px',
          color: '#166534',
          fontSize: '13px',
          border: '1px solid #bbf7d0'
        }}>
          ✓ Showing data for {selectedDateRange.start} to {selectedDateRange.end}
          {cachedResults.size > 0 && (
            <span style={{ marginLeft: '8px', opacity: 0.7 }}>
              (Cached: {cachedResults.size} date range{cachedResults.size > 1 ? 's' : ''})
            </span>
          )}
        </div>
      )}

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
          <p style={{ color: '#6b7280', fontSize: '14px', margin: '0 0 8px 0', fontWeight: 500 }}>Total Teams</p>
          <p style={{ fontSize: '32px', fontWeight: 700, color: '#111827', margin: 0 }}>{totalTeams}</p>
        </div>
        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '12px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <p style={{ color: '#6b7280', fontSize: '14px', margin: '0 0 8px 0', fontWeight: 500 }}>Active Teams</p>
          <p style={{ fontSize: '32px', fontWeight: 700, color: '#111827', margin: 0 }}>{activeTeams}</p>
        </div>
        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '12px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <p style={{ color: '#6b7280', fontSize: '14px', margin: '0 0 8px 0', fontWeight: 500 }}>Total Questions</p>
          <p style={{ fontSize: '32px', fontWeight: 700, color: '#111827', margin: 0 }}>{totalQuestions}</p>
        </div>
        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '12px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <p style={{ color: '#6b7280', fontSize: '14px', margin: '0 0 8px 0', fontWeight: 500 }}>Avg Questions/Team</p>
          <p style={{ fontSize: '32px', fontWeight: 700, color: '#111827', margin: 0 }}>
            {totalTeams > 0 ? Math.round(totalQuestions / totalTeams) : 0}
          </p>
        </div>
      </div>

      {/* Teams Grid */}
      <div style={{
        background: 'white',
        borderRadius: '12px',
        border: '1px solid #e5e7eb',
        padding: '20px'
      }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px', color: '#111827' }}>Teams Overview</h2>
        
        {teams.length === 0 ? (
          <div style={{ padding: '20px', color: '#6b7280', textAlign: 'center' }}>No team data available</div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: '16px'
          }}>
            {teams.map((team) => (
              <div
                key={team.team_name}
                onClick={() => {
                  setSelectedTeam(team.team_name);
                  if (authUser) fetchTeamDetails(authUser, team.team_name, startDate, endDate);
                }}
                style={{
                  padding: '16px',
                  border: `2px solid ${team.color}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  background: 'white',
                  transition: 'all 0.2s ease',
                  boxShadow: selectedTeam === team.team_name ? `0 0 12px ${team.color}40` : 'none',
                  opacity: 1,
                  ':hover': {
                    boxShadow: `0 0 12px ${team.color}40`
                  }
                }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '12px'
                }}>
                  <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: team.color }}>
                    {team.team_name}
                  </h3>
                  <span style={{
                    background: team.color,
                    color: 'white',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 600
                  }}>
                    {team.total_questions}
                  </span>
                </div>

                <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '10px' }}>
                  <p style={{ margin: '4px 0' }}>
                    <strong>Lead:</strong> {team.lead || 'N/A'}
                  </p>
                  <p style={{ margin: '4px 0' }}>
                    <strong>Members:</strong> {team.member_count} ({team.active_members_count} active)
                  </p>
                </div>

                <div style={{
                  background: '#f9fafb',
                  padding: '8px',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}>
                  <p style={{ margin: '2px 0', color: '#6b7280' }}>
                    <strong>Unique Questions:</strong> {team.unique_questions}
                  </p>
                  {team.top_questions.length > 0 && (
                    <p style={{ margin: '4px 0 2px 0', color: '#111827', fontWeight: 500 }}>Top: {team.top_questions[0].question.substring(0, 40)}...</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Team Details Modal */}
      {showTeamDetails && selectedTeamDetails && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }} onClick={() => setShowTeamDetails(false)}>
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'white',
              borderRadius: '12px',
              padding: '24px',
              maxWidth: '800px',
              width: '90%',
              maxHeight: '80vh',
              overflowY: 'auto',
              boxShadow: '0 20px 25px rgba(0,0,0,0.15)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{
                margin: 0,
                fontSize: '22px',
                fontWeight: 700,
                color: selectedTeamDetails.color
              }}>
                {selectedTeamDetails.team_name}
              </h2>
              <button
                onClick={() => setShowTeamDetails(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#6b7280'
                }}
              >
                ×
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', marginBottom: '20px' }}>
              <div style={{ background: '#f9fafb', padding: '12px', borderRadius: '8px' }}>
                <p style={{ margin: '0 0 4px 0', color: '#6b7280', fontSize: '12px' }}>Lead</p>
                <p style={{ margin: 0, fontWeight: 600 }}>{selectedTeamDetails.lead}</p>
              </div>
              <div style={{ background: '#f9fafb', padding: '12px', borderRadius: '8px' }}>
                <p style={{ margin: '0 0 4px 0', color: '#6b7280', fontSize: '12px' }}>Total Questions</p>
                <p style={{ margin: 0, fontWeight: 600 }}>{selectedTeamDetails.team_total_questions}</p>
              </div>
              <div style={{ background: '#f9fafb', padding: '12px', borderRadius: '8px' }}>
                <p style={{ margin: '0 0 4px 0', color: '#6b7280', fontSize: '12px' }}>Active Members</p>
                <p style={{ margin: 0, fontWeight: 600 }}>{selectedTeamDetails.active_members}/{selectedTeamDetails.total_members}</p>
              </div>
              <div style={{ background: '#f9fafb', padding: '12px', borderRadius: '8px' }}>
                <p style={{ margin: '0 0 4px 0', color: '#6b7280', fontSize: '12px' }}>Unique Questions</p>
                <p style={{ margin: 0, fontWeight: 600 }}>{selectedTeamDetails.team_unique_questions}</p>
              </div>
            </div>

            <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '12px', marginTop: '20px' }}>Team Members</h3>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              maxHeight: '400px',
              overflowY: 'auto'
            }}>
              {selectedTeamDetails.members.map((member) => (
                <div key={member.email} style={{
                  padding: '12px',
                  background: member.total_questions > 0 ? '#f9fafb' : '#f3f4f6',
                  borderRadius: '8px',
                  borderLeft: `4px solid ${selectedTeamDetails.color}`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <p style={{ margin: 0, fontWeight: member.is_lead ? 600 : 500 }}>
                      {member.name} {member.is_lead && '👑'}
                    </p>
                    <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: '#6b7280' }}>{member.email}</p>
                  </div>
                  <span style={{
                    background: selectedTeamDetails.color,
                    color: 'white',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 600
                  }}>
                    {member.total_questions}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

