import React from 'react';

export default function StudioPage() {
  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        width: '100vw',
        height: '100dvh',
        overflow: 'hidden',
        background: '#fff',
      }}
    >
      <iframe
        src="/studio-app/index.html"
        title="CadArena Studio"
        style={{
          width: '100%',
          height: '100%',
          border: 'none',
          display: 'block',
        }}
        allow="clipboard-write"
      />
    </div>
  );
}
