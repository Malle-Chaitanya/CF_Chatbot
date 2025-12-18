'use client';

import { useEffect } from 'react';
import { startTokenMonitor, stopTokenMonitor } from '@/lib/session-utils';

/**
 * TokenMonitor component that runs background token refresh checks.
 * This component should be included once at the app level.
 * 
 * Features:
 * - Checks token expiration every 2 minutes
 * - Automatically refreshes tokens before they expire
 * - Shows notification when refreshing
 * - Ensures seamless "never expire" user experience
 */
export default function TokenMonitor() {
  useEffect(() => {
    // Start the background token monitor
    startTokenMonitor();
    
    // Cleanup on unmount
    return () => {
      stopTokenMonitor();
    };
  }, []);
  
  // This component doesn't render anything
  return null;
}




