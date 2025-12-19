'use client';

import { useEffect } from 'react';
import { startSessionMonitor, stopSessionMonitor } from '@/lib/session-utils';

/**
 * SessionMonitor component that runs background session refresh checks.
 * This component should be included once at the app level.
 * 
 * Features:
 * - Checks session validity every 5 minutes
 * - Automatically refreshes session tokens if needed
 * - Ensures seamless "never expire" user experience
 * - Uses cookie-based session authentication
 */
export default function TokenMonitor() {
  useEffect(() => {
    // Start the background session monitor
    startSessionMonitor();
    
    // Cleanup on unmount
    return () => {
      stopSessionMonitor();
    };
  }, []);
  
  // This component doesn't render anything
  return null;
}
