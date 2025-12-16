'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { getApiBase, getCurrentUser } from '@/lib/session-utils';
import { isAdminEmail } from '@/constants/admins';
import { User } from '@/types/chat';

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

export default function TeamsAnalyticsPage() {
  const router = useRouter();
  const [authUser, setAuthUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [fetching, setFetching] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [teams, setTeams] = useState<TeamStats[]>([]);
  const [selectedTeamDetails, setSelectedTeamDetails] = useState<TeamDetails | null>(null);
  const [showTeamDetails, setShowTeamDetails] = useState<boolean>(false);

  const [timeFilter, setTimeFilter] = useState<string>('today');
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

  // Fetch teams analytics
  const fetchTeamsAnalytics = useCallback(async (filter: string) => {
    try {
      setFetching(true);
      setError(null);

      console.log('[Teams Fetch] Starting fetch with filter:', filter);
      
      const user = getCurrentUser(); // NOT async!
      console.log('[Teams Fetch] Got user:', user?.email);
      
      if (!user) {
        setError('Not authenticated');
        console.error('[Teams Fetch] No user found');
        return;
      }

      const apiBase = getApiBase();
      console.log('[Teams Fetch] API Base:', apiBase);
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (user.access_token) {
        headers['Authorization'] = `Bearer ${user.access_token}`;
      }

      const url = `${apiBase}/analytics/langfuse/teams/summary?time_filter=${filter}`;
      console.log('[Teams Fetch] Attempting to fetch from:', url);
      console.log('[Teams Fetch] Headers:', headers);

      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout

        const response = await fetch(url, {
          method: 'GET',
          headers,
          credentials: 'include',
          signal: controller.signal,
        });

        clearTimeout(timeoutId);
        console.log('[Teams Fetch] Response status:', response.status);

        if (!response.ok) {
          const errorText = await response.text();
          console.error('[Teams Fetch] Error response:', errorText);
          throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 200)}`);
        }

        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
          console.error('[Teams Fetch] Invalid content type:', contentType);
          throw new Error(`Invalid response type: ${contentType}`);
        }

        const data = await response.json();
        console.log('[Teams Fetch] Success! Data:', data);
        
        if (!data.teams && !Array.isArray(data)) {
          console.error('[Teams Fetch] Invalid response format:', data);
          throw new Error('Invalid response format from server');
        }
        
        setTeams(data.teams || data || []);
        setLastFetchTime(Date.now());
      } catch (fetchErr) {
        if (fetchErr instanceof TypeError && fetchErr.message.includes('Failed to fetch')) {
          console.error('[Teams Fetch] Network error (CORS or connection issue):', fetchErr);
          throw new Error('Failed to connect to server. Check if backend is running and CORS is configured correctly.');
        }
        console.error('[Teams Fetch] Network error:', fetchErr);
        throw fetchErr;
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch team analytics';
      setError(message);
      console.error('Teams analytics fetch error:', err);
    } finally {
      setFetching(false);
    }
  }, []);

  // Fetch team details
  const fetchTeamDetails = useCallback(async (teamName: string) => {
    try {
      const user = getCurrentUser(); // NOT async!
      if (!user) return;

      const apiBase = getApiBase();
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (user.access_token) {
        headers['Authorization'] = `Bearer ${user.access_token}`;
      }

      const response = await fetch(
        `${apiBase}/analytics/langfuse/teams/details/${encodeURIComponent(teamName)}?time_filter=${timeFilter}`,
        {
          method: 'GET',
          headers,
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();
        setSelectedTeamDetails(data);
        setShowTeamDetails(true);
      }
    } catch (err) {
      console.error('Team details fetch error:', err);
    }
  }, [timeFilter]);

  // Handle filter change
  const handleFilterChange = (filter: string) => {
    setTimeFilter(filter);
    fetchTeamsAnalytics(filter);
  };

  // Initial fetch on auth
  useEffect(() => {
    if (!loading && authUser) {
      fetchTeamsAnalytics(timeFilter);
    }
  }, [loading, authUser, timeFilter]);

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
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '8px' }}>Team Analytics</h1>
        <p style={{ color: '#6b7280', fontSize: '16px' }}>Track team performance and questions</p>
      </div>

      {/* Filter Buttons */}
      <div style={{ marginBottom: '24px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
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
          Loading team data...
        </div>
      )}

      {/* Summary Stats */}
      {teams.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
          <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px', backgroundColor: '#f9fafb' }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Total Questions</div>
            <div style={{ fontSize: '28px', fontWeight: '700' }}>
              {teams.reduce((sum, t) => sum + t.total_questions, 0)}
            </div>
          </div>
          <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px', backgroundColor: '#f9fafb' }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Total Teams</div>
            <div style={{ fontSize: '28px', fontWeight: '700' }}>{teams.length}</div>
          </div>
          <div style={{ padding: '16px', border: '1px solid #e5e7eb', borderRadius: '8px', backgroundColor: '#f9fafb' }}>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Active Teams</div>
            <div style={{ fontSize: '28px', fontWeight: '700' }}>
              {teams.filter(t => t.total_questions > 0).length}
            </div>
          </div>
        </div>
      )}

      {/* Leaderboard */}
      {teams.length > 0 ? (
        <div style={{ border: '1px solid #e5e7eb', borderRadius: '8px', overflow: 'hidden' }}>
          <div style={{ padding: '16px', backgroundColor: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600' }}>Team Leaderboard</h2>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f3f4f6', borderBottom: '1px solid #e5e7eb' }}>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Rank</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Team</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Total Questions</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Unique</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Active Members</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', fontWeight: '600', color: '#6b7280' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {teams.map((team, idx) => (
                  <tr key={team.team_name} style={{ borderBottom: '1px solid #e5e7eb', backgroundColor: idx % 2 === 0 ? 'white' : '#fafafa' }}>
                    <td style={{ padding: '12px 16px', fontSize: '14px', fontWeight: '500' }}>{idx + 1}</td>
                    <td style={{ padding: '12px 16px', fontSize: '14px', fontWeight: '500' }}>
                      <span style={{
                        display: 'inline-block',
                        width: '12px',
                        height: '12px',
                        borderRadius: '3px',
                        backgroundColor: team.color,
                        marginRight: '8px'
                      }}></span>
                      {team.team_name}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: '14px', textAlign: 'center', fontWeight: '600' }}>
                      {team.total_questions}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: '14px', textAlign: 'center' }}>
                      {team.unique_questions}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: '14px', textAlign: 'center' }}>
                      {team.active_members_count}/{team.member_count}
                    </td>
                    <td style={{ padding: '12px 16px', fontSize: '14px', textAlign: 'center' }}>
                      <button
                        onClick={() => fetchTeamDetails(team.team_name)}
                        style={{
                          padding: '4px 8px',
                          backgroundColor: '#0129ac',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px',
                          fontWeight: '500'
                        }}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : !fetching && !error ? (
        <div style={{ padding: '32px', textAlign: 'center', color: '#6b7280' }}>
          No team data available for the selected period.
        </div>
      ) : null}

      {/* Team Details Modal */}
      {showTeamDetails && selectedTeamDetails && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '24px',
            maxWidth: '700px',
            width: '90%',
            maxHeight: '80vh',
            overflowY: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: '700' }}>{selectedTeamDetails.team_name}</h2>
              <button
                onClick={() => setShowTeamDetails(false)}
                style={{ background: 'none', border: 'none', fontSize: '24px', cursor: 'pointer' }}
              >
                ×
              </button>
            </div>

            <div style={{ marginBottom: '20px', paddingBottom: '20px', borderBottom: '1px solid #e5e7eb' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Lead</div>
                  <div style={{ fontSize: '14px', fontWeight: '600' }}>{selectedTeamDetails.lead}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Total Members</div>
                  <div style={{ fontSize: '14px', fontWeight: '600' }}>{selectedTeamDetails.total_members}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Active Members</div>
                  <div style={{ fontSize: '14px', fontWeight: '600' }}>{selectedTeamDetails.active_members}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Total Questions</div>
                  <div style={{ fontSize: '14px', fontWeight: '600' }}>{selectedTeamDetails.team_total_questions}</div>
                </div>
              </div>
            </div>

            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>Members</h3>
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {selectedTeamDetails.members.map((member, idx) => (
                <div key={idx} style={{
                  padding: '12px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '4px',
                  marginBottom: '8px'
                }}>
                  <div style={{ fontSize: '14px', fontWeight: '500' }}>
                    {member.name}
                    {member.is_lead && <span style={{ marginLeft: '8px', fontSize: '12px', backgroundColor: '#dbeafe', color: '#0129ac', padding: '2px 6px', borderRadius: '3px' }}>Lead</span>}
                  </div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>{member.email}</div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>Questions: {member.total_questions}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
