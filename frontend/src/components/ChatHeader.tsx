'use client';

import { useState } from 'react';

interface ChatHeaderProps {
  isReadOnly: boolean;
  sessionId?: string;
  onContinueThread?: () => void;
  onShare?: () => void;
}

export default function ChatHeader({ 
  isReadOnly, 
  sessionId, 
  onContinueThread, 
  onShare 
}: ChatHeaderProps) {
  const [showShareModal, setShowShareModal] = useState(false);

  return (
    <div className="chat-header">
      <div className="chat-header-content">
        {/* Read-only badge for others' chats */}
        {isReadOnly && (
          <div className="read-only-badge">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            <span>Read-Only</span>
          </div>
        )}

        {/* Action buttons */}
        <div className="header-actions">
          {/* Continue Thread button - only for read-only (others' chats) */}
          {isReadOnly && onContinueThread && (
            <button 
              className="header-btn continue-button" 
              onClick={onContinueThread}
              title="Copy this chat to your own chats and continue"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path>
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect>
              </svg>
              <span>Continue in this thread</span>
            </button>
          )}

          {/* Share button - available for both own and others' chats */}
          {onShare && (
            <button 
              className="header-btn share-button" 
              onClick={onShare}
              title={isReadOnly ? "Share this chat with others" : "Share this chat"}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="18" cy="5" r="3"></circle>
                <circle cx="6" cy="12" r="3"></circle>
                <circle cx="18" cy="19" r="3"></circle>
                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
              </svg>
              <span>Share</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

